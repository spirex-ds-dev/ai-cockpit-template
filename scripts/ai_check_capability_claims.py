#!/usr/bin/env python3
"""Bind current public capability claims to fresh Capability Truth evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from ai_capability_truth import (
    CapabilityTruthError,
    build_evidence_source,
    capability_state,
    validate_matrix,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATRIX_RELATIVE_PATH = Path("docs/reference/capability-truth-matrix.json")
MATRIX_PROJECTION = "docs/reference/capability-truth-matrix.md"
README_NAMES = ("README.md", "README.ja.md", "README.zh-CN.md")

INLINE_BINDING = re.compile(r"<!--\s*capability-claim:\s*([A-Za-z0-9_-]+)\s*-->", re.IGNORECASE)
ENGLISH_CLAIM = re.compile(
    r"\b(?:supports?|prevents?|blocks?|guarantees?|verifies|detects?|protects?|"
    r"ensures?|implemented|production[- ]ready|enterprise[- ]ready)\b",
    re.IGNORECASE,
)
LOCALIZED_CLAIM_TERMS = (
    "サポート",
    "防止",
    "ブロック",
    "保証",
    "検証",
    "検出",
    "保護",
    "確保",
    "実装済み",
    "本番対応",
    "エンタープライズ対応",
    "支持",
    "防止",
    "阻止",
    "保证",
    "验证",
    "检测",
    "保护",
    "确保",
    "已实现",
    "生产就绪",
    "企业就绪",
)
TEMPLATE_PROVISION_TERMS = (
    "template provides",
    "template is provided",
    "provided by the template",
    "template-only",
    "template only",
    "テンプレートで提供",
    "テンプレートが提供",
    "テンプレートのみ",
    "模板提供",
    "由模板提供",
    "仅限模板",
)
NO_INSTALL_PROOF_TERMS = (
    "does not prove adopter installation",
    "does not prove installation",
    "not proof of adopter installation",
    "not proof of installation",
    "導入済みを証明しません",
    "導入を証明しません",
    "インストール済みを証明しません",
    "証明しません",
    "不证明采用方已安装",
    "不证明已安装",
    "不能证明已安装",
    "并非安装证明",
)
PLANNED_TERMS = (
    "planned",
    "future",
    "not yet available",
    "計画中",
    "将来",
    "まだ利用できません",
    "计划中",
    "未来",
    "尚不可用",
)


def _front_matter(text: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    if not text.startswith("---\n"):
        return {}, {}
    closing = text.find("\n---\n", 4)
    if closing < 0:
        return {}, {}
    scalars: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    current_key = ""
    for line in text[4:closing].splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if match:
            current_key = match.group(1)
            value = match.group(2).strip().strip("\"'")
            scalars[current_key] = value
            if value.startswith("[") and value.endswith("]"):
                lists[current_key] = [
                    item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()
                ]
            continue
        item = re.match(r"^\s+-\s+([A-Za-z0-9_-]+)\s*$", line)
        if current_key and item:
            lists.setdefault(current_key, []).append(item.group(1))
    return scalars, lists


def extract_claim_ids(text: str) -> set[str]:
    """Extract exact capability IDs from YAML and inline markers."""
    _, lists = _front_matter(text)
    return set(lists.get("capabilityClaims", ())) | set(INLINE_BINDING.findall(text))


def _prose_text(text: str) -> str:
    """Remove binding metadata so IDs cannot satisfy their own wording rules."""
    if text.startswith("---\n"):
        closing = text.find("\n---\n", 4)
        if closing >= 0:
            text = text[closing + 5 :]
    return INLINE_BINDING.sub("", text)


def _contains_claim_language(text: str) -> bool:
    return ENGLISH_CLAIM.search(text) is not None or any(
        term in text for term in LOCALIZED_CLAIM_TERMS
    )


def _contains_all(text: str, groups: tuple[tuple[str, ...], ...]) -> bool:
    lowered = re.sub(r"\s+", " ", text.lower())
    return all(any(term.lower() in lowered for term in group) for group in groups)


def _is_current_public(text: str) -> bool:
    scalars, _ = _front_matter(text)
    return scalars.get("authority") == "canonical" and scalars.get("status") in {
        "current",
        "reference",
    }


def _documents(root: Path) -> list[Path]:
    selected: set[Path] = set()
    for name in README_NAMES:
        path = root / name
        if path.is_file():
            selected.add(path)
    docs = root / "docs"
    if docs.is_dir():
        candidates = sorted(docs.rglob("*.md"))
        canonical_siblings: set[str] = set()
        for path in candidates:
            relative = path.relative_to(root).as_posix()
            if relative == MATRIX_PROJECTION:
                continue
            if _is_current_public(path.read_text(encoding="utf-8")):
                selected.add(path)
                canonical_siblings.add(_sibling_key(relative))
        for path in candidates:
            relative = path.relative_to(root).as_posix()
            if relative != MATRIX_PROJECTION and _sibling_key(relative) in canonical_siblings:
                selected.add(path)
    return sorted(selected)


def _sibling_key(relative: str) -> str:
    return re.sub(r"\.(?:ja|zh-CN)(?=\.md$)", "", relative)


def _load_rows(matrix_path: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    value = json.loads(matrix_path.read_text(encoding="utf-8"))
    rows = value.get("capabilities", [])
    if not isinstance(rows, list):
        return [], {}
    typed_rows = [row for row in rows if isinstance(row, dict)]
    return typed_rows, {str(row["id"]): row for row in typed_rows if isinstance(row.get("id"), str)}


def _effective_state(row: dict[str, Any], *, root: Path) -> str:
    state = capability_state(row)
    if state == "evidence_stale":
        return state
    source_paths = row.get("sourceEvidence")
    test_paths = row.get("testEvidence")
    if not isinstance(source_paths, list) or not isinstance(test_paths, list):
        return "evidence_stale"
    try:
        observed = build_evidence_source(source_paths, test_paths, root=root)
    except CapabilityTruthError:
        return "evidence_stale"
    if observed != row.get("evidenceSource"):
        return "evidence_stale"
    return state


def claim_errors(
    root: Path = PROJECT_ROOT,
    matrix_path: Path | None = None,
) -> list[str]:
    """Return deterministic errors for unsupported current public claims."""
    root = root.resolve()
    matrix_path = matrix_path or root / MATRIX_RELATIVE_PATH
    errors = [f"capability matrix: {error}" for error in validate_matrix(matrix_path, root=root)]
    _, rows_by_id = _load_rows(matrix_path)
    bindings_by_sibling: dict[str, list[tuple[str, set[str]]]] = {}

    for path in _documents(root):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        prose = _prose_text(text)
        identifiers = extract_claim_ids(text)
        bindings_by_sibling.setdefault(_sibling_key(relative), []).append((relative, identifiers))
        if _contains_claim_language(prose) and not identifiers:
            errors.append(
                f"{relative}: unbound capability claim; add capabilityClaims or "
                "<!-- capability-claim: id -->"
            )
        for identifier in sorted(identifiers):
            row = rows_by_id.get(identifier)
            if row is None:
                errors.append(f"{relative}: unknown capability id: {identifier}")
                continue
            state = _effective_state(row, root=root)
            if state == "evidence_stale":
                errors.append(
                    f"{relative}: capability {identifier} has effective state evidence_stale"
                )
            elif state == "template_only" and not _contains_all(
                prose, (TEMPLATE_PROVISION_TERMS, NO_INSTALL_PROOF_TERMS)
            ):
                errors.append(
                    f"{relative}: capability {identifier} is template_only; state that "
                    "the template provides it and does not prove adopter installation"
                )
            elif state == "planned" and not _contains_all(prose, (PLANNED_TERMS,)):
                errors.append(
                    f"{relative}: capability {identifier} is planned; use planned or future wording"
                )

    for sibling, documents in sorted(bindings_by_sibling.items()):
        if len(documents) < 2:
            continue
        expected = documents[0][1]
        if any(identifiers != expected for _, identifiers in documents[1:]):
            detail = "; ".join(f"{path}={sorted(identifiers)}" for path, identifiers in documents)
            errors.append(f"{sibling}: multilingual capability binding mismatch: {detail}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--matrix", type=Path)
    args = parser.parse_args()
    errors = claim_errors(args.root, args.matrix)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1
    print("capability claim binding check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
