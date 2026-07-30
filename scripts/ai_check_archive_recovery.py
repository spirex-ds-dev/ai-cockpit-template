#!/usr/bin/env python3
"""Fail closed before rebasing archived Work Item evidence onto a newer base."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from ai_common import InvalidDataShapeError

ROOT = Path(__file__).resolve().parents[1]
INDEX = ".ai/work-items/archive/index.json"
TRACEABILITY = "docs/reference/remediation-instruction-traceability.json"


def _owners(index: dict[str, Any]) -> dict[int, str]:
    entries = index.get("entries", [])
    return {
        entry["archiveSequence"]: entry["contractPath"]
        for entry in entries
        if isinstance(entry, dict)
        and isinstance(entry.get("archiveSequence"), int)
        and isinstance(entry.get("contractPath"), str)
    }


def _traceability_owners(manifest: dict[str, Any]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for item in manifest.get("instructions", []):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        paths = item.get("contractPaths", [])
        if isinstance(paths, list) and paths and isinstance(paths[0], str):
            owners[item["id"]] = paths[0]
    return owners


def recovery_collisions(
    current_index: dict[str, Any],
    target_index: dict[str, Any],
    current_traceability: dict[str, Any],
    target_traceability: dict[str, Any],
) -> list[str]:
    """Return immutable-evidence collisions between a branch and its target base."""
    errors: list[str] = []
    for sequence, path in _owners(current_index).items():
        owner = _owners(target_index).get(sequence)
        if owner and owner != path:
            errors.append(
                f"archive sequence {sequence} is already owned on the target base by {owner}; "
                "do not rebase archived evidence, create a successor Work Item"
            )
    for identifier, path in _traceability_owners(current_traceability).items():
        owner = _traceability_owners(target_traceability).get(identifier)
        if owner and owner != path:
            errors.append(
                f"traceability id {identifier} is already owned on the target base by {owner}; "
                "do not overwrite or renumber archived evidence, create a successor Work Item"
            )
    return errors


def _load_current(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise InvalidDataShapeError(f"{path} must be a JSON object")
    return value


def _load_target(ref: str, path: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ValueError(f"cannot read target evidence {ref}:{path}: {result.stderr.strip()}")
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise InvalidDataShapeError(f"target evidence {ref}:{path} must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="target ref, e.g. origin/main")
    args = parser.parse_args()
    try:
        errors = recovery_collisions(
            _load_current(INDEX),
            _load_target(args.target, INDEX),
            _load_current(TRACEABILITY),
            _load_target(args.target, TRACEABILITY),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] archive recovery preflight cannot establish evidence: {exc}")
        return 1
    for error in errors:
        print(f"[ERROR] {error}")
    if errors:
        return 1
    print(f"archive recovery preflight passed against {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
