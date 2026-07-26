#!/usr/bin/env python3
"""Check the authoritative Human-Agent Trust Layer documentation contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRUST_FILES = {
    "en": ROOT / "docs" / "trust-layer.md",
    "zh": ROOT / "docs" / "trust-layer.zh-CN.md",
    "ja": ROOT / "docs" / "trust-layer.ja.md",
}
README_FILES = {
    "en": ROOT / "README.md",
    "zh": ROOT / "README.zh-CN.md",
    "ja": ROOT / "README.ja.md",
}
SECTION_IDS = (
    "why",
    "what",
    "how",
    "current-implementation",
    "deterministic-coverage",
    "machine-readable-evidence",
    "commands-and-demonstration",
    "boundaries-and-navigation",
)
CORE_TERMS = {
    "en": (
        "Repository Governance Layer",
        "Evidence over Self-Declaration",
        "AI Cockpit governs evidence; it does not replace evidence-producing tools.",
        "AI Cockpit is not a Security Sandbox.",
        "SBOM is Delegated Domain Evidence",
        "Capability Truth Matrix is the only source of current implementation status",
    ),
    "zh": (
        "Repository Governance Layer",
        "Evidence over Self-Declaration",
        "AI Cockpit governs evidence; it does not replace evidence-producing tools",
        "AI Cockpit is not a Security Sandbox",
        "SBOM 是 Delegated Domain Evidence",
        "Capability Truth Matrix 是当前实现状态的唯一事实来源",
    ),
    "ja": (
        "Repository Governance Layer",
        "Evidence over Self-Declaration",
        "AI Cockpit governs evidence; it does not replace evidence-producing tools",
        "AI Cockpit is not a Security Sandbox",
        "SBOM は Delegated Domain Evidence",
        "Capability Truth Matrix が現在の実装状態の唯一の事実源",
    ),
}
REQUIRED_IMPLEMENTATION = (
    "Unsupported Claim Regression Gate",
    "delusion-test-gate",
    "Guard Signal Envelope",
    "Preflight enforced profile",
    "Raw Request Binding",
    "Requested Operation",
    "Capability Mapping",
    "Human Decision and Recovery",
    "Archive Manifest",
)


def section_ids(text: str) -> list[str]:
    return re.findall(r"<!-- section-id: ([a-z0-9-]+) -->", text)


def links(path: Path, text: str) -> list[str]:
    return [
        target
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        if not target.startswith(("http:", "https:", "mailto:"))
    ]


def link_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for target in links(path, text):
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        if not resolved.is_file() and not resolved.is_dir():
            errors.append(f"{path.relative_to(ROOT)}: broken internal link {target}")
    return errors


def core_term_errors(language: str, text: str, label: str) -> list[str]:
    return [
        f"{label}: missing core boundary: {term}"
        for term in CORE_TERMS[language]
        if term not in text
    ]


def check_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    texts: dict[str, str] = {}
    trust_files = {
        "en": root / "docs" / "trust-layer.md",
        "zh": root / "docs" / "trust-layer.zh-CN.md",
        "ja": root / "docs" / "trust-layer.ja.md",
    }
    readme_files = {
        "en": root / "README.md",
        "zh": root / "README.zh-CN.md",
        "ja": root / "README.ja.md",
    }
    for language, path in trust_files.items():
        if not path.is_file():
            errors.append(f"missing Trust Layer document: {path.relative_to(root)}")
            continue
        text = path.read_text(encoding="utf-8")
        texts[language] = text
        ids = section_ids(text)
        if ids != list(SECTION_IDS):
            errors.append(f"{path.relative_to(root)}: section IDs differ from canonical order")
        errors.extend(core_term_errors(language, text, path.relative_to(root).as_posix()))
        for term in REQUIRED_IMPLEMENTATION:
            if term not in text:
                errors.append(f"{path.relative_to(root)}: missing implementation detail: {term}")
        errors.extend(link_errors(path, text))

    if texts:
        counts = {
            language: len(re.findall(r"^#{1,6} ", text, re.MULTILINE))
            for language, text in texts.items()
        }
        if len(set(counts.values())) != 1:
            errors.append(f"Trust Layer heading counts differ: {counts}")

    architecture = root / "docs" / "reference" / "documentation-architecture.md"
    if not architecture.is_file():
        errors.append("missing Documentation Architecture")
    else:
        architecture_text = architecture.read_text(encoding="utf-8")
        for term in (
            "Human-Agent Trust Layer",
            "Why / What / How",
            "Capability Truth Matrix",
            "Enterprise Control Checklist",
        ):
            if term not in architecture_text:
                errors.append(f"Documentation Architecture: missing registration term: {term}")
        errors.extend(link_errors(architecture, architecture_text))

    for language, path in readme_files.items():
        if not path.is_file():
            errors.append(f"missing README: {path.relative_to(root)}")
            continue
        text = path.read_text(encoding="utf-8")
        target = {
            "en": "docs/trust-layer.md",
            "zh": "docs/trust-layer.zh-CN.md",
            "ja": "docs/trust-layer.ja.md",
        }[language]
        if target not in text or "Human-Agent Trust Layer" not in text:
            errors.append(f"{path.relative_to(root)}: missing short Trust Layer entry")
        errors.extend(link_errors(path, text))
    return errors


def main() -> int:
    errors = check_repository()
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print("trust-layer documentation consistency check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
