#!/usr/bin/env python3
"""Fail-closed validation for instruction -> plan -> implementation -> acceptance evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import hashlib


REQUIRED_FIELDS = (
    "id",
    "summary",
    "planWorkItems",
    "contractPaths",
    "implementationEvidence",
    "acceptanceEvidence",
    "verificationCommands",
)


def _path(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("path"), str):
        return value["path"]
    return None


def _resolved_path(repository: Path, path: str) -> Path | None:
    """Resolve an evidence path, including a deterministic archived fallback."""
    direct = repository / path
    if direct.is_file():
        return direct
    active = Path(".ai/work-items/active")
    try:
        relative = Path(path).relative_to(active)
    except ValueError:
        return None
    candidates = sorted((repository / ".ai/work-items/archive").glob(f"*/{relative.name}"))
    return candidates[0] if len(candidates) == 1 and candidates[0].is_file() else None


def _validate_archive_integrity(repository: Path) -> list[str]:
    """Validate archive index/manifest bindings so post-finish edits cannot drift silently."""
    index_path = repository / ".ai/work-items/archive/index.json"
    if not index_path.is_file():
        return []
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"archive index cannot be read: {exc}"]
    entries = index.get("entries") if isinstance(index, dict) else None
    if not isinstance(entries, list):
        return ["archive index entries must be a list"]
    errors: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("archive index contains a non-object entry")
            continue
        for kind in ("contract", "summary", "manifest"):
            path = entry.get(f"{kind}Path")
            recorded = entry.get(f"{kind}Sha256")
            if not isinstance(path, str) or not isinstance(recorded, str):
                continue
            target = repository / path
            if not target.is_file():
                errors.append(f"archive index {kind} path does not exist: {path}")
            elif hashlib.sha256(target.read_bytes()).hexdigest() != recorded:
                errors.append(f"archive index {kind} digest mismatch: {path}")
        manifest_path = entry.get("manifestPath")
        if isinstance(manifest_path, str) and (repository / manifest_path).is_file():
            try:
                manifest = json.loads((repository / manifest_path).read_text(encoding="utf-8"))
                for kind in ("contract", "summary"):
                    path = manifest.get(f"{kind}Path")
                    recorded = manifest.get(f"{kind}Sha256")
                    manifest_target: Path | None = (
                        repository / path if isinstance(path, str) else None
                    )
                    if manifest_target is None or not manifest_target.is_file():
                        errors.append(f"archive manifest {kind} path does not exist: {path}")
                    elif hashlib.sha256(manifest_target.read_bytes()).hexdigest() != recorded:
                        errors.append(f"archive manifest {kind} digest mismatch: {path}")
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"archive manifest cannot be read: {manifest_path}: {exc}")
    return errors


def validate_manifest(manifest: dict[str, Any], repository: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_archive_integrity(repository))
    if manifest.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")

    plan_path = manifest.get("planPath")
    if not isinstance(plan_path, str) or not plan_path:
        errors.append("planPath must be a non-empty repository-relative path")
        plan_text = ""
    else:
        plan_file = repository / plan_path
        if not plan_file.is_file():
            errors.append(f"planPath does not exist: {plan_path}")
            plan_text = ""
        else:
            plan_text = plan_file.read_text(encoding="utf-8")

    instructions = manifest.get("instructions")
    if not isinstance(instructions, list) or not instructions:
        return errors + ["instructions must be a non-empty list"]

    ids: set[str] = set()
    for index, instruction in enumerate(instructions):
        prefix = f"instructions[{index}]"
        if not isinstance(instruction, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = [field for field in REQUIRED_FIELDS if not instruction.get(field)]
        if missing:
            errors.append(f"{prefix} missing required fields: {', '.join(missing)}")

        instruction_id = instruction.get("id")
        if not isinstance(instruction_id, str) or not instruction_id:
            errors.append(f"{prefix}.id must be non-empty")
        elif instruction_id in ids:
            errors.append(f"duplicate instruction id: {instruction_id}")
        else:
            ids.add(instruction_id)

        work_items = instruction.get("planWorkItems", [])
        if not isinstance(work_items, list) or not all(
            isinstance(item, str) and item for item in work_items
        ):
            errors.append(f"{prefix}.planWorkItems must contain non-empty strings")
        else:
            for item in work_items:
                if item not in plan_text:
                    errors.append(
                        f"{instruction_id}: plan Work Item is not present in plan: {item}"
                    )

        for field in ("contractPaths", "implementationEvidence", "acceptanceEvidence"):
            values = instruction.get(field, [])
            if not isinstance(values, list) or not values:
                continue
            for value in values:
                path = _path(value)
                if not path:
                    errors.append(f"{instruction_id}: {field} contains an invalid path record")
                elif _resolved_path(repository, path) is None:
                    errors.append(f"{instruction_id}: {field} path does not exist: {path}")

        commands = instruction.get("verificationCommands", [])
        if not isinstance(commands, list) or not all(
            isinstance(command, str) and command.strip() for command in commands
        ):
            errors.append(f"{instruction_id}: verificationCommands must contain non-empty commands")

        implementation_paths = {
            _path(value) for value in instruction.get("implementationEvidence", [])
        }
        for named in instruction.get("requiredNamedPaths", []):
            if not isinstance(named, dict) or not isinstance(named.get("path"), str):
                errors.append(f"{instruction_id}: requiredNamedPaths contains an invalid record")
                continue
            named_path = named["path"]
            if _resolved_path(repository, named_path) is None:
                errors.append(f"{instruction_id}: required named path does not exist: {named_path}")
            if (
                named_path not in implementation_paths
                and not str(named.get("noChangeRationale", "")).strip()
            ):
                errors.append(
                    f"{instruction_id}: required named path lacks implementation evidence or no-change rationale: {named_path}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", default="docs/reference/remediation-instruction-traceability.json"
    )
    parser.add_argument("--repository", default=".")
    args = parser.parse_args()
    repository = Path(args.repository).resolve()
    manifest_path = repository / args.manifest
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[ERROR] unable to read traceability manifest: {exc}")
        return 1
    errors = validate_manifest(manifest, repository)
    if errors:
        for issue in errors:
            print(f"[ERROR] {issue}")
        return 1
    print(f"instruction traceability check passed: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
