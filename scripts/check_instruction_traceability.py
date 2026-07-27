#!/usr/bin/env python3
"""Fail-closed validation for instruction -> plan -> implementation -> acceptance evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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


def validate_manifest(manifest: dict[str, Any], repository: Path) -> list[str]:
    errors: list[str] = []
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
                elif not (repository / path).is_file():
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
            if not (repository / named_path).is_file():
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
