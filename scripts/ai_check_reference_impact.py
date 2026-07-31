#!/usr/bin/env python3
"""Evaluate evidence-backed reference impact before a compatibility-affecting change.

This initial boundary intentionally performs only repository-local text analysis.
Dynamic, monitoring, and external-consumer status are caller-provided evidence;
unknown evidence never becomes permission.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

OPERATIONS = {
    "delete",
    "rename",
    "move",
    "deprecate",
    "change_visibility",
    "change_signature",
    "remove_configuration",
    "remove_public_api",
}
EVIDENCE_CATEGORIES = (
    "dynamicReferences",
    "externalConsumers",
    "monitoringReferences",
)
BYPASS_TERMS = ("do not question", "bypass", "skip impact analysis", "直接删除", "不要质疑")
TARGET_TYPES = {
    "function",
    "class",
    "method",
    "api",
    "configuration_key",
    "feature_flag",
    "database_field",
    "cli_option",
    "environment_variable",
    "workflow_job",
    "make_target",
    "script_entrypoint",
}
CODE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".java",
    ".kt",
    ".kts",
    ".swift",
    ".dart",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".cs",
}
CONFIGURATION_SUFFIXES = {".yaml", ".yml", ".json", ".toml", ".ini", ".env"}


def _safe_relative(root: Path, value: str) -> Path:
    normalized = value.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", normalized) or normalized.startswith("//"):
        raise ValueError("target path must be repository-relative")
    portable = PurePosixPath(normalized)
    if portable.is_absolute() or ".." in portable.parts:
        raise ValueError("target path escapes the repository root")
    unresolved = root.joinpath(*portable.parts)
    if unresolved.is_symlink():
        raise ValueError("target path must not be a symlink")
    candidate = unresolved.resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("target path escapes the repository root") from exc
    return candidate


def _is_test_path(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(part.casefold() in {"test", "tests"} for part in relative.parts[:-1]) or (
        relative.stem.casefold().startswith("test_")
        or relative.stem.casefold().endswith("_test")
        or relative.stem.casefold().endswith(".test")
        or relative.stem.casefold().endswith(".spec")
    )


def _python_mentions(path: Path, name: str) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name:
            return True
        if isinstance(node, ast.Attribute) and node.attr == name:
            return True
        if isinstance(node, (ast.Import, ast.ImportFrom)) and any(
            alias.name.rsplit(".", 1)[-1] == name or alias.asname == name for alias in node.names
        ):
            return True
    return False


def _text_mentions(path: Path, name: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    return bool(pattern.search(path.read_text(encoding="utf-8", errors="replace")))


def _code_references(root: Path, target_path: Path, name: str) -> tuple[list[str], list[str]]:
    references: list[str] = []
    test_references: list[str] = []
    for path in root.rglob("*"):
        if path.suffix.casefold() not in CODE_SUFFIXES:
            continue
        if path.resolve() == target_path or path.is_symlink():
            continue
        mentioned = (
            _python_mentions(path, name) if path.suffix == ".py" else _text_mentions(path, name)
        )
        if not mentioned:
            continue
        relative = path.relative_to(root).as_posix()
        if _is_test_path(path, root):
            test_references.append(relative)
        else:
            references.append(relative)
    return sorted(references), sorted(test_references)


def _documentation_references(root: Path, target_path: Path, name: str) -> list[str]:
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.md")
        if path.resolve() != target_path
        and not path.is_symlink()
        and pattern.search(path.read_text(encoding="utf-8", errors="replace"))
    )


def _configuration_references(
    root: Path, target_path: Path, name: str, ignored_paths: set[Path]
) -> list[str]:
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.suffix.casefold() in CONFIGURATION_SUFFIXES
        and path.resolve() != target_path
        and path.resolve() not in ignored_paths
        and not _is_workflow_path(path, root)
        and not path.is_symlink()
        and pattern.search(path.read_text(encoding="utf-8", errors="replace"))
    )


def _is_workflow_path(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    return len(parts) >= 3 and parts[0:2] == (".github", "workflows")


def _workflow_references(root: Path, target_path: Path, name: str) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and path.resolve() != target_path
        and _is_workflow_path(path, root)
        and _text_mentions(path, name)
    )


def _analysis_capability(target_path: Path) -> str:
    if target_path.suffix == ".py":
        return "python_ast"
    if target_path.suffix in {".ts", ".tsx"}:
        return "typescript_basic"
    return "generic_analysis_only"


def evaluate(
    record: dict[str, Any], *, root: Path, ignored_paths: set[Path] | None = None
) -> dict[str, Any]:
    """Return a deterministic block, confirmation, or continue decision."""
    target = record.get("target")
    if not isinstance(target, dict) or record.get("version") != 1:
        raise ValueError("reference impact record version 1 and target are required")
    target_type = target.get("type")
    name, path, operation = target.get("name"), target.get("path"), target.get("operation")
    if (
        not isinstance(name, str)
        or not name
        or not isinstance(path, str)
        or not path
        or not isinstance(operation, str)
        or not operation
    ):
        raise ValueError("target name, path, and operation are required")
    if target_type not in TARGET_TYPES:
        raise ValueError("unsupported reference-impact target type")
    if operation not in OPERATIONS:
        raise ValueError("unsupported reference-impact operation")

    target_path = _safe_relative(root, path)
    if not target_path.is_file():
        raise ValueError("target path does not exist or is not a regular file")
    analysis = record.get("referenceAnalysis")
    analysis = dict(analysis) if isinstance(analysis, dict) else {}
    static, tests = _code_references(root, target_path, name)
    analysis["staticReferences"] = static
    analysis["testReferences"] = tests
    analysis["documentationReferences"] = _documentation_references(root, target_path, name)
    analysis["configurationReferences"] = _configuration_references(
        root, target_path, name, ignored_paths or set()
    )
    analysis["workflowReferences"] = _workflow_references(root, target_path, name)
    for category in EVIDENCE_CATEGORIES:
        value = analysis.get(category)
        analysis[category] = (
            value if isinstance(value, dict) else {"status": "unknown", "evidence": []}
        )

    requested_text = record.get("requestedText")
    requested_text = requested_text.lower() if isinstance(requested_text, str) else ""
    approval = record.get("approval")
    self_declared_approval = (
        isinstance(approval, dict)
        and approval.get("approved") is True
        and approval.get("identityLevel") in {"self_declared", "repository_recorded"}
    )
    live_references = any(
        analysis[key]
        for key in (
            "staticReferences",
            "testReferences",
            "documentationReferences",
            "configurationReferences",
            "workflowReferences",
        )
    )
    stale_evidence = any(analysis[key].get("stale") is True for key in EVIDENCE_CATEGORIES)
    governance = record.get("governanceEvidence")
    governance_complete = (
        isinstance(governance, dict)
        and governance.get("contractDeclared") is True
        and governance.get("acceptanceDeclared") is True
        and governance.get("destructiveChangeAllowed") is True
        and isinstance(governance.get("evidence"), list)
        and bool(governance["evidence"])
    )
    if any(term in requested_text for term in BYPASS_TERMS):
        decision, reason = (
            "block",
            "Requested wording attempts to bypass reference-impact analysis.",
        )
    elif self_declared_approval:
        decision, reason = (
            "block",
            "Self-declared or repository-recorded approval cannot authorize a destructive change.",
        )
    elif live_references:
        decision, reason = (
            "block",
            "Static, test, documentation, configuration, or workflow references remain for the target.",
        )
    elif operation in {"remove_public_api", "remove_configuration"}:
        decision, reason = (
            "needs_human_confirmation",
            "Public API or configuration removal requires owner-confirmed migration evidence.",
        )
    elif stale_evidence:
        decision, reason = (
            "needs_human_confirmation",
            "Dynamic, external, or monitoring evidence is stale.",
        )
    elif any(
        analysis[key].get("status") != "proven_absent"
        or not isinstance(analysis[key].get("evidence"), list)
        or not analysis[key]["evidence"]
        for key in EVIDENCE_CATEGORIES
    ):
        decision, reason = (
            "needs_human_confirmation",
            "Dynamic, external, or monitoring evidence is missing or not proven absent.",
        )
    elif not governance_complete:
        decision, reason = (
            "needs_human_confirmation",
            "Governance evidence does not prove Contract, acceptance, and destructive-policy authorization.",
        )
    else:
        decision, reason = (
            "continue",
            "Repository-local static and supplied non-static evidence are clear.",
        )
    return {
        "version": 1,
        "target": target,
        "analysisCapability": _analysis_capability(target_path),
        "referenceAnalysis": analysis,
        "decision": decision,
        "reason": reason,
        "recoveryCondition": "Remove live references or provide reliable migration and owner evidence.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate reference impact evidence.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Return exit 3 unless the evidence-backed decision is continue.",
    )
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise TypeError("record must be a JSON object")
        result = evaluate(
            record, root=args.root, ignored_paths={args.record.resolve(), args.output.resolve()}
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if not args.enforce or result["decision"] == "continue" else 3


if __name__ == "__main__":
    raise SystemExit(main())
