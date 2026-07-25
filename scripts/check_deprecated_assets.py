#!/usr/bin/env python3
"""Validate the deprecation registry without authorizing deletion."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


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


def _date(value: Any) -> dt.date | None:
    if value == "never":
        return None
    if not isinstance(value, str):
        raise ValueError("date must be ISO YYYY-MM-DD or 'never'")
    return dt.date.fromisoformat(value)


def validate_registry(root: Path, payload: Any, *, today: dt.date | None = None) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict) or payload.get("schemaVersion") != 1:
        return ["registry schemaVersion must be 1"]
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        return ["registry entries must be a non-empty list"]
    seen: set[str] = set()
    today = today or dt.date.today()
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
    return issues


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
    if issues:
        print("\n".join(f"[ERROR] {item}" for item in issues), file=sys.stderr)
        return 1
    print(f"deprecated asset registry check passed: {args.registry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
