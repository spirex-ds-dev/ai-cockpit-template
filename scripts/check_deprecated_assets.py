#!/usr/bin/env python3
"""Validate the deprecation registry without authorizing deletion."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

from ai_common import InvalidDataShapeError

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "reference" / "deprecated-assets-registry.json"
REQUIRED_FIELDS = {
    "id",
    "path",
    "type",
    "replacement",
    "deprecatedSince",
    "plannedRemoval",
    "reason",
    "currentReferences",
    "runtimeUsed",
    "migrationRequired",
}
PROTECTED_PREFIXES = (".ai/work-items/archive/", ".ai/decisions/", ".ai/events/", ".ai/release/")
SCAN_REQUIRED_FIELDS = {"paths", "excludePrefixes", "prohibitedCommandChains"}
TEXT_SUFFIXES = {
    ".cfg",
    ".ai",
    ".ini",
    ".json",
    ".md",
    ".mk",
    ".py",
    ".rst",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {"AGENTS.md", "Makefile", "README.md"}


def _date(value: Any) -> dt.date | None:
    if value == "never":
        return None
    if not isinstance(value, str):
        raise InvalidDataShapeError("date must be ISO YYYY-MM-DD or 'never'")
    return dt.date.fromisoformat(value)


def _relative_files(root: Path, relative: str) -> list[Path]:
    """Return deterministic text-candidate files below one declared scan path."""
    path = root / relative
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    return []


def _is_current_facing_text_asset(path: Path) -> bool:
    """Keep the command scan on source and maintained prose, never binary/cache artifacts."""
    return path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_SUFFIXES


def _scan_configuration_issues(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["registry must be an object"]
    scan = payload.get("currentFacingScan")
    if not isinstance(scan, dict):
        return ["currentFacingScan must be an object"]
    issues: list[str] = []
    missing = SCAN_REQUIRED_FIELDS - set(scan)
    issues.extend(f"currentFacingScan missing {field}" for field in sorted(missing))
    paths = scan.get("paths")
    if (
        not isinstance(paths, list)
        or not paths
        or any(not isinstance(path, str) or not path or Path(path).is_absolute() for path in paths)
    ):
        issues.append("currentFacingScan paths must be a non-empty relative-path list")
    excluded = scan.get("excludePrefixes")
    if not isinstance(excluded, list) or any(
        not isinstance(path, str) or not path or Path(path).is_absolute() for path in excluded
    ):
        issues.append("currentFacingScan excludePrefixes must be a relative-path list")
    chains = scan.get("prohibitedCommandChains")
    if not isinstance(chains, list) or not chains:
        issues.append("currentFacingScan prohibitedCommandChains must be a non-empty list")
        return issues
    seen: set[str] = set()
    for index, chain in enumerate(chains):
        prefix = f"currentFacingScan prohibitedCommandChains[{index}]"
        if not isinstance(chain, dict):
            issues.append(f"{prefix} must be an object")
            continue
        identifier, expression = chain.get("id"), chain.get("pattern")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            issues.append(f"{prefix} id must be non-empty and unique")
        else:
            seen.add(identifier)
        if not isinstance(expression, str) or not expression:
            issues.append(f"{prefix} pattern must be a non-empty string")
        else:
            try:
                re.compile(expression, flags=re.IGNORECASE | re.DOTALL)
            except re.error as exc:
                issues.append(f"{prefix} pattern is invalid: {exc}")
    return issues


def validate_current_facing_paths(root: Path, payload: Any) -> list[str]:
    """Reject prohibited lifecycle chains in declared current-facing assets only."""
    issues = _scan_configuration_issues(payload)
    if issues:
        return issues
    if not isinstance(payload, dict):
        return ["registry must be an object"]
    scan = payload.get("currentFacingScan")
    if not isinstance(scan, dict):
        return ["currentFacingScan must be an object"]
    files: list[Path] = []
    for relative in scan["paths"]:
        candidates = _relative_files(root, relative)
        if not candidates:
            issues.append(f"currentFacingScan path does not exist: {relative}")
            continue
        files.extend(candidates)
    exclusions = tuple(scan["excludePrefixes"])
    for candidate in sorted(set(files)):
        relative = candidate.relative_to(root).as_posix()
        if relative.startswith(exclusions) or not _is_current_facing_text_asset(candidate):
            continue
        try:
            content = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(f"currentFacingScan cannot read {relative}: {exc}")
            continue
        for chain in scan["prohibitedCommandChains"]:
            if re.search(chain["pattern"], content, flags=re.IGNORECASE | re.DOTALL):
                issues.append(f"{chain['id']}: {relative} matches prohibited command chain")
    return issues


def validate_registry(root: Path, payload: Any, *, today: dt.date | None = None) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict) or payload.get("schemaVersion") != 1:
        return ["registry schemaVersion must be 1"]
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        return ["registry entries must be a non-empty list"]
    seen: set[str] = set()
    today = today or dt.datetime.now(dt.UTC).date()
    for index, entry in enumerate(entries):
        prefix = f"entries[{index}]"
        if not isinstance(entry, dict):
            issues.append(f"{prefix} must be an object")
            continue
        missing = REQUIRED_FIELDS - set(entry)
        issues.extend(f"{prefix} missing {field}" for field in sorted(missing))
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            issues.append(f"{prefix} id must be non-empty and unique")
        else:
            seen.add(identifier)
        path = entry.get("path")
        if not isinstance(path, str) or not path or Path(path).is_absolute():
            issues.append(f"{prefix} path must be repository-relative")
        else:
            if not (root / path).is_file():
                issues.append(f"{prefix} path does not exist: {path}")
            if path.startswith(PROTECTED_PREFIXES) and entry.get("deletionAllowed") is not False:
                issues.append(f"{prefix} protected archive path must set deletionAllowed=false")
        replacement = entry.get("replacement")
        if not isinstance(replacement, str) or not replacement.strip():
            issues.append(f"{prefix} replacement must be explicit")
        elif replacement != "none" and not (root / replacement).is_file():
            issues.append(f"{prefix} replacement does not exist: {replacement}")
        try:
            deprecated = _date(entry.get("deprecatedSince"))
            planned = _date(entry.get("plannedRemoval"))
            if deprecated and deprecated > today:
                issues.append(f"{prefix} deprecatedSince is in the future")
            if planned and deprecated and planned < deprecated:
                issues.append(f"{prefix} plannedRemoval precedes deprecatedSince")
            if planned and planned < today and entry.get("runtimeUsed") is not False:
                issues.append(f"{prefix} stale plannedRemoval requires runtimeUsed=false")
        except (TypeError, ValueError) as exc:
            issues.append(f"{prefix} invalid date: {exc}")
        if not isinstance(entry.get("currentReferences"), list):
            issues.append(f"{prefix} currentReferences must be a list")
        if not isinstance(entry.get("runtimeUsed"), bool):
            issues.append(f"{prefix} runtimeUsed must be boolean")
        if not isinstance(entry.get("migrationRequired"), bool):
            issues.append(f"{prefix} migrationRequired must be boolean")
        for reference in entry.get("currentReferences", []):
            if not isinstance(reference, str) or not (root / reference).is_file():
                issues.append(f"{prefix} current reference does not exist: {reference}")
    return [*issues, *_scan_configuration_issues(payload)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        payload = json.loads(args.registry.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"deprecated asset registry load failed: {exc}", file=sys.stderr)
        return 1
    issues = validate_registry(args.root.resolve(), payload)
    if not issues:
        issues = validate_current_facing_paths(args.root.resolve(), payload)
    if issues:
        print("\n".join(f"[ERROR] {item}" for item in issues), file=sys.stderr)
        return 1
    print(f"deprecated asset registry check passed: {args.registry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
