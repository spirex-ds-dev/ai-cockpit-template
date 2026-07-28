#!/usr/bin/env python3
"""Fail-closed validation for instruction -> plan -> implementation -> acceptance evidence."""

from __future__ import annotations

import argparse
import hashlib
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
EXPECTED_AUDIT_WORK_ITEMS = {f"WI-{number:02d}" for number in range(1, 21)}
AUDIT_EVIDENCE_FIELDS = (
    "instructionEvidence",
    "planEvidence",
    "contractEvidence",
    "implementationEvidence",
    "acceptanceEvidence",
    "verificationEvidence",
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


def _audit_path_errors(
    repository: Path,
    work_item_id: str,
    field: str,
    records: Any,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Validate evidence records that own repository paths."""
    if not isinstance(records, list) or not records:
        return [f"{work_item_id}: {field} must be a non-empty list"], []
    errors: list[str] = []
    valid: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        prefix = f"{work_item_id}: {field}[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        path = record.get("path")
        if not isinstance(path, str) or not path:
            errors.append(f"{prefix}.path must be non-empty")
            continue
        if _resolved_path(repository, path) is None:
            errors.append(f"{prefix} path does not exist: {path}")
        valid.append(record)
    return errors, valid


def _audit_reverse_ref_errors(
    work_item_id: str,
    field: str,
    records: list[dict[str, Any]],
    instruction_refs: set[str],
    plan_refs: set[str],
) -> list[str]:
    """Require every claimed artifact to map back to instruction and plan evidence."""
    errors: list[str] = []
    for index, record in enumerate(records):
        prefix = f"{work_item_id}: {field}[{index}]"
        if not str(record.get("reason", "")).strip():
            errors.append(f"{prefix}.reason must be non-empty")
        for key, allowed in (
            ("instructionRefs", instruction_refs),
            ("planRefs", plan_refs),
        ):
            refs = record.get(key)
            if (
                not isinstance(refs, list)
                or not refs
                or not all(isinstance(ref, str) and ref in allowed for ref in refs)
            ):
                errors.append(f"{prefix}.{key} must reference this row's evidence")
    return errors


def _archive_entries(repository: Path) -> dict[str, dict[str, Any]]:
    index_path = repository / ".ai/work-items/archive/index.json"
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return {}
    return {
        str(entry.get("contractPath")): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("contractPath"), str)
    }


def validate_audit(audit: dict[str, Any], repository: Path) -> list[str]:
    """Validate the canonical WI-01 through WI-20 bidirectional audit."""
    errors: list[str] = []
    if audit.get("auditVersion") != 1:
        errors.append("auditVersion must be 1")
    status = audit.get("status")
    if status not in {"in_progress", "complete"}:
        errors.append("audit status must be in_progress or complete")

    plan_path = audit.get("planPath")
    if not isinstance(plan_path, str) or _resolved_path(repository, plan_path) is None:
        errors.append(f"audit planPath does not exist: {plan_path}")

    rows = audit.get("workItems")
    if not isinstance(rows, list):
        return errors + ["audit workItems must be a list"]

    row_ids = [
        row.get("workItemId")
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("workItemId"), str)
    ]
    duplicates = sorted({item for item in row_ids if row_ids.count(item) > 1})
    if duplicates:
        errors.append(f"audit contains duplicate Work Items: {', '.join(duplicates)}")
    missing = sorted(EXPECTED_AUDIT_WORK_ITEMS - set(row_ids))
    unknown = sorted(set(row_ids) - EXPECTED_AUDIT_WORK_ITEMS)
    if missing:
        errors.append(f"audit is missing Work Items: {', '.join(missing)}")
    if unknown:
        errors.append(f"audit contains unknown Work Items: {', '.join(unknown)}")

    archive_entries = _archive_entries(repository)
    path_owners: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = {}
    top_findings = audit.get("findings")
    if not isinstance(top_findings, list):
        errors.append("audit findings must be a list")
        top_findings = []
    finding_by_id = {
        finding.get("findingId"): finding
        for finding in top_findings
        if isinstance(finding, dict) and isinstance(finding.get("findingId"), str)
    }

    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"workItems[{row_index}] must be an object")
            continue
        work_item_id = row.get("workItemId")
        if not isinstance(work_item_id, str) or not work_item_id:
            errors.append(f"workItems[{row_index}].workItemId must be non-empty")
            continue
        row_status = row.get("status")
        if row_status not in {"verified", "deferred", "open"}:
            errors.append(f"{work_item_id}: status must be verified, deferred, or open")

        instruction_errors, instruction_records = _audit_path_errors(
            repository,
            work_item_id,
            "instructionEvidence",
            row.get("instructionEvidence"),
        )
        plan_errors, plan_records = _audit_path_errors(
            repository,
            work_item_id,
            "planEvidence",
            row.get("planEvidence"),
        )
        errors.extend(instruction_errors)
        errors.extend(plan_errors)
        instruction_refs = {
            str(record.get("ref"))
            for record in instruction_records
            if isinstance(record.get("ref"), str) and record.get("ref")
        }
        plan_refs = {
            str(record.get("ref"))
            for record in plan_records
            if isinstance(record.get("ref"), str) and record.get("ref")
        }
        for field, records in (
            ("instructionEvidence", instruction_records),
            ("planEvidence", plan_records),
        ):
            for index, record in enumerate(records):
                locator = record.get("locator")
                reference = record.get("ref")
                if not isinstance(reference, str) or not reference:
                    errors.append(f"{work_item_id}: {field}[{index}].ref must be non-empty")
                if not isinstance(locator, str) or not locator:
                    errors.append(f"{work_item_id}: {field}[{index}].locator must be non-empty")
                    continue
                resolved = _resolved_path(repository, str(record["path"]))
                if resolved is not None:
                    try:
                        text = resolved.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        errors.append(f"{work_item_id}: {field}[{index}] is not readable text")
                    else:
                        if locator not in text:
                            errors.append(
                                f"{work_item_id}: {field}[{index}] locator is missing: {locator}"
                            )

        contracts = row.get("contractEvidence")
        if not isinstance(contracts, list) or not contracts:
            errors.append(f"{work_item_id}: contractEvidence must be a non-empty list")
        else:
            for index, record in enumerate(contracts):
                prefix = f"{work_item_id}: contractEvidence[{index}]"
                if not isinstance(record, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                contract_path = record.get("contractPath")
                summary_path = record.get("summaryPath")
                manifest_path = record.get("manifestPath")
                for key, value in (
                    ("contractPath", contract_path),
                    ("summaryPath", summary_path),
                    ("manifestPath", manifest_path),
                ):
                    if not isinstance(value, str) or _resolved_path(repository, value) is None:
                        errors.append(f"{prefix}.{key} path does not exist: {value}")
                indexed = archive_entries.get(str(contract_path))
                if (
                    indexed is None
                    or indexed.get("summaryPath") != summary_path
                    or indexed.get("manifestPath") != manifest_path
                ):
                    errors.append(f"{prefix} does not match one archive index entry")

        reverse_records: dict[str, list[dict[str, Any]]] = {}
        for field in ("implementationEvidence", "acceptanceEvidence"):
            field_errors, records = _audit_path_errors(
                repository,
                work_item_id,
                field,
                row.get(field),
            )
            errors.extend(field_errors)
            errors.extend(
                _audit_reverse_ref_errors(
                    work_item_id,
                    field,
                    records,
                    instruction_refs,
                    plan_refs,
                )
            )
            reverse_records[field] = records
            for record in records:
                path_owners.setdefault((field, str(record.get("path"))), []).append(
                    (work_item_id, record)
                )

        verification = row.get("verificationEvidence")
        if not isinstance(verification, list) or not verification:
            errors.append(f"{work_item_id}: verificationEvidence must be a non-empty list")
        else:
            for index, record in enumerate(verification):
                prefix = f"{work_item_id}: verificationEvidence[{index}]"
                if not isinstance(record, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                if not str(record.get("command", "")).strip():
                    errors.append(f"{prefix}.command must be non-empty")
                if record.get("result") not in {"passed", "not_applicable", "deferred"}:
                    errors.append(f"{prefix}.result is invalid")
                source_path = record.get("sourcePath")
                if (
                    not isinstance(source_path, str)
                    or _resolved_path(repository, source_path) is None
                ):
                    errors.append(f"{prefix}.sourcePath does not exist: {source_path}")
                errors.extend(
                    _audit_reverse_ref_errors(
                        work_item_id,
                        "verificationEvidence",
                        [record],
                        instruction_refs,
                        plan_refs,
                    )
                )

        rationales = row.get("noChangeRationales", [])
        if not isinstance(rationales, list):
            errors.append(f"{work_item_id}: noChangeRationales must be a list")
            rationales = []
        rationale_by_path: dict[str, dict[str, Any]] = {}
        for index, record in enumerate(rationales):
            prefix = f"{work_item_id}: noChangeRationales[{index}]"
            if not isinstance(record, dict):
                errors.append(f"{prefix} must be an object")
                continue
            path = record.get("path")
            if not isinstance(path, str) or not path:
                errors.append(f"{prefix}.path must be non-empty")
                continue
            if not str(record.get("reason", "")).strip():
                errors.append(f"{prefix}.reason must be non-empty")
            evidence = record.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{prefix}.evidence must be a non-empty list")
            else:
                for evidence_path in evidence:
                    if (
                        not isinstance(evidence_path, str)
                        or _resolved_path(repository, evidence_path) is None
                    ):
                        errors.append(f"{prefix} evidence path does not exist: {evidence_path}")
            rationale_by_path[path] = record

        implementation_paths = {
            str(record.get("path")) for record in reverse_records["implementationEvidence"]
        }
        acceptance_paths = {
            str(record.get("path")) for record in reverse_records["acceptanceEvidence"]
        }
        named_paths = row.get("namedPaths", [])
        if not isinstance(named_paths, list):
            errors.append(f"{work_item_id}: namedPaths must be a list")
            named_paths = []
        for index, record in enumerate(named_paths):
            prefix = f"{work_item_id}: namedPaths[{index}]"
            if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                errors.append(f"{prefix} must contain a path")
                continue
            named_path = str(record["path"])
            disposition = record.get("disposition")
            if disposition == "implemented" and named_path not in implementation_paths:
                errors.append(f"{prefix} lacks exact implementation evidence: {named_path}")
            elif disposition == "acceptance" and named_path not in acceptance_paths:
                errors.append(f"{prefix} lacks exact acceptance evidence: {named_path}")
            elif disposition == "no_change" and named_path not in rationale_by_path:
                errors.append(f"{prefix} lacks an evidence-backed no-change rationale")
            elif disposition not in {"implemented", "acceptance", "no_change"}:
                errors.append(f"{prefix}.disposition is invalid")

        row_findings = row.get("findings", [])
        if not isinstance(row_findings, list) or not all(
            isinstance(finding_id, str) and finding_id in finding_by_id
            for finding_id in row_findings
        ):
            errors.append(f"{work_item_id}: findings must reference top-level finding IDs")
            row_findings = []
        for finding_id in row_findings:
            finding_work_item = finding_by_id[finding_id].get("workItemId")
            if finding_work_item != work_item_id:
                errors.append(
                    f"{work_item_id}: finding {finding_id} belongs to {finding_work_item}"
                )
        open_row_findings = [
            finding_id
            for finding_id in row_findings
            if finding_by_id[finding_id].get("status") not in {"resolved", "not_applicable"}
        ]
        if row_status == "verified" and open_row_findings:
            errors.append(f"{work_item_id}: verified row contains open findings")

    for (field, path), owners in path_owners.items():
        if len({owner for owner, _ in owners}) <= 1:
            continue
        if any(not str(record.get("sharedEvidenceReason", "")).strip() for _, record in owners):
            owner_names = ", ".join(sorted({owner for owner, _ in owners}))
            errors.append(
                f"{field} path has duplicate ownership without sharedEvidenceReason: "
                f"{path} ({owner_names})"
            )

    open_findings = []
    for index, finding in enumerate(top_findings):
        prefix = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required = (
            "findingId",
            "workItemId",
            "severity",
            "missingDomain",
            "fact",
            "evidence",
            "status",
            "releaseBlocking",
            "correctiveWorkItemId",
            "reverification",
        )
        missing_fields = [key for key in required if key not in finding]
        if missing_fields:
            errors.append(f"{prefix} missing fields: {', '.join(missing_fields)}")
        if finding.get("status") not in {
            "open",
            "corrective_required",
            "resolved",
            "not_applicable",
        }:
            errors.append(f"{prefix}.status is invalid")
        if finding.get("workItemId") not in EXPECTED_AUDIT_WORK_ITEMS:
            errors.append(f"{prefix}.workItemId is invalid")
        if finding.get("status") not in {"resolved", "not_applicable"}:
            open_findings.append(finding)
    if status == "complete":
        incomplete_rows = [
            str(row.get("workItemId"))
            for row in rows
            if isinstance(row, dict) and row.get("status") not in {"verified", "deferred"}
        ]
        if incomplete_rows:
            errors.append(f"complete audit contains incomplete rows: {', '.join(incomplete_rows)}")
        if open_findings:
            errors.append("complete audit contains open findings")
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
    parser.add_argument(
        "--audit",
        default="docs/reference/wi01-wi20-bidirectional-traceability-audit.json",
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
    audit_path = repository / args.audit
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[ERROR] unable to read WI-01 through WI-20 audit: {exc}")
        return 1
    errors.extend(validate_audit(audit, repository))
    if errors:
        for issue in errors:
            print(f"[ERROR] {issue}")
        return 1
    print(
        "instruction traceability check passed: "
        f"{manifest_path}; WI-01 through WI-20 audit: {audit_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
