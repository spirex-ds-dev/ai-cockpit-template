"""Build the evidence-bound Implementation Knowledge projection."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

STATUSES = {"verified", "unknown", "incomplete"}
KNOWLEDGE_STATES = {"verified", "partial", "unknown", "superseded"}
EFFECTIVE_STATES = {"current", "superseded", "unknown", "historical_or_current_unknown"}
DATE_PATTERN = "%Y-%m-%d"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _claim_status(value: Any) -> str:
    if not isinstance(value, dict):
        return "unknown"
    status = value.get("status")
    if status == "complete":
        return "verified"
    if status in STATUSES:
        return status
    return "unknown"


def _approach_is_verified(value: Any) -> bool:
    if not isinstance(value, dict) or value.get("status") != "complete":
        return False
    claims: list[Any] = [value.get("summary"), value.get("mechanism")]
    claims.extend(value.get("affectedComponents", []))
    claims.extend(value.get("designDecisions", []))
    claims.extend(value.get("technicalDetails", []))
    claims.append(value)
    for claim in claims:
        if isinstance(claim, dict) and "status" in claim and _claim_status(claim) != "verified":
            return False
    return True


def _evidence_items(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if isinstance(value.get("evidence"), list):
            for item in value["evidence"]:
                if isinstance(item, dict):
                    items.append(item)
        for child in value.values():
            if isinstance(child, (dict, list)):
                items.extend(_evidence_items(child))
    elif isinstance(value, list):
        for child in value:
            if isinstance(child, (dict, list)):
                items.extend(_evidence_items(child))
    return items


def _evidence_path(item: dict[str, Any]) -> str | None:
    for key in ("source", "path"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _safe_evidence(path_text: str, root: Path) -> tuple[Path | None, str | None]:
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts or "" in path.parts:
        return None, "evidence path must be normalized and repository-relative"
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None, "evidence path escapes repository"
    if not candidate.is_file():
        return None, "evidence path does not exist"
    return candidate, None


def _record_evidence(approach: Any, root: Path, issues: list[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in _evidence_items(approach):
        path_text = _evidence_path(item)
        if path_text is None or path_text in seen:
            continue
        seen.add(path_text)
        candidate, error = _safe_evidence(path_text, root)
        if error:
            issues.append(f"{path_text}: {error}")
            continue
        if candidate is None:
            issues.append(f"{path_text}: evidence path resolution returned no file")
            continue
        declared = item.get("digest")
        actual = _digest(candidate)
        if declared is not None and declared != actual:
            issues.append(f"{path_text}: evidence digest is stale")
        evidence_type = item.get("type")
        if not isinstance(evidence_type, str):
            evidence_type = "test" if path_text.startswith("tests/") else "code"
        entry: dict[str, Any] = {"type": evidence_type, "path": path_text}
        # Always freeze the observed evidence digest.  A later checker can
        # therefore detect a changed file even when the source claim omitted a
        # digest, while a stale declared digest still invalidates the claim.
        entry["digest"] = actual
        result.append(entry)
    return result


def _changes(summary: dict[str, Any]) -> list[str]:
    values = summary.get("actualChanges", summary.get("changedFiles", []))
    result: list[str] = []
    if isinstance(values, list):
        for value in values:
            path = value.get("path") if isinstance(value, dict) else value
            if isinstance(path, str) and path not in result:
                result.append(path)
    return result


def _explicit_field(
    name: str,
    sources: list[tuple[str, Any]],
    issues: list[str],
) -> tuple[Any, bool]:
    """Read a field only when an authoritative source explicitly supplies it."""
    values: list[tuple[str, Any]] = []
    for label, source in sources:
        if isinstance(source, dict) and name in source and source[name] is not None:
            values.append((label, source[name]))
    if not values:
        return None, False
    first = values[0][1]
    if any(_canonical(value) != _canonical(first) for _, value in values[1:]):
        labels = ", ".join(label for label, _ in values)
        issues.append(f"explicit {name} values disagree across sources: {labels}")
    return first, True


def _explicit_date(value: Any, issues: list[str]) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        issues.append("explicit date must be a YYYY-MM-DD string")
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        issues.append("explicit date must be a calendar date in YYYY-MM-DD format")
        return None
    normalized = parsed.strftime(DATE_PATTERN)
    if value != normalized:
        issues.append("explicit date must be normalized as YYYY-MM-DD")
        return None
    return value


def _explicit_supersedes(value: Any, issues: list[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        issues.append("supersedes must be an array of non-empty Work Item IDs")
        return []
    return list(dict.fromkeys(value))


def build_record(
    contract_path: Path,
    summary_path: Path,
    outcome_path: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    contract = _load(contract_path)
    summary = _load(summary_path)
    outcome = _load(outcome_path)
    work_item_id = contract.get("workItemId")
    if not isinstance(work_item_id, str) or not work_item_id:
        raise ValueError("Contract workItemId is required")

    issues: list[str] = []
    if summary.get("workItemId") != work_item_id:
        issues.append("Summary workItemId does not match Contract")
    outcome_id = outcome.get("workItemId")
    bindings = outcome.get("bindings")
    if outcome_id is None and isinstance(bindings, dict):
        outcome_id = bindings.get("taskId")
    if outcome_id != work_item_id:
        issues.append("Outcome workItemId does not match Contract")

    summary_approach = summary.get("implementationApproach")
    outcome_sections = outcome.get("sections")
    outcome_approach = (
        outcome_sections.get("implementationApproach")
        if isinstance(outcome_sections, dict)
        else None
    )
    if summary_approach is not None and outcome_approach is not None:
        if _canonical(summary_approach) != _canonical(outcome_approach):
            issues.append("Summary and Outcome Implementation Approach disagree")
    elif summary_approach is not None or outcome_approach is not None:
        issues.append("Summary and Outcome Implementation Approach are incomplete")

    approach = summary_approach if summary_approach is not None else outcome_approach
    evidence = _record_evidence(approach, repo_root, issues) if approach is not None else []
    approach_verified = _approach_is_verified(approach) and bool(evidence) and not issues
    if approach is None:
        implementation = {"summary": "unknown", "status": "unknown"}
        unknowns = ["Implementation Approach was not recorded in Summary/Outcome"]
    else:
        summary_claim = approach.get("summary") if isinstance(approach, dict) else None
        implementation = {
            "summary": summary_claim.get("text", "unknown")
            if isinstance(summary_claim, dict)
            else "unknown",
            "status": "verified" if approach_verified else "incomplete",
        }
        unknowns = list(issues)
        if not approach_verified and not unknowns:
            unknowns.append("Implementation Approach is not evidence-complete")

    decisions = summary.get("designDecisions")
    if not isinstance(decisions, list) and isinstance(approach, dict):
        decisions = approach.get("designDecisions", [])
    if not isinstance(decisions, list):
        decisions = []
    projected_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        projected_decisions.append(
            {
                "decision": decision.get("decision", "unknown"),
                "reason": decision.get("reason", "unknown"),
                "status": "verified"
                if approach_verified and decision.get("status") == "verified"
                else "unknown",
            }
        )

    source_values = [
        ("Summary", summary),
        ("Outcome", outcome),
        ("Outcome sections", outcome_sections),
        ("Contract", contract),
    ]
    explicit_date_value, has_date = _explicit_field("date", source_values, issues)
    explicit_date = _explicit_date(explicit_date_value, issues)
    explicit_effective_state, has_effective_state = _explicit_field(
        "effectiveState", source_values, issues
    )
    if not has_effective_state:
        effective_state = "historical_or_current_unknown"
    elif explicit_effective_state not in EFFECTIVE_STATES:
        issues.append("effectiveState is not a supported explicit state")
        effective_state = "historical_or_current_unknown"
    else:
        effective_state = explicit_effective_state
    explicit_supersedes, _ = _explicit_field("supersedes", source_values, issues)
    supersedes = _explicit_supersedes(explicit_supersedes, issues)

    generated_from = {
        "contractPath": _relative(contract_path, repo_root),
        "contractDigest": _digest(contract_path),
        "summaryPath": _relative(summary_path, repo_root),
        "summaryDigest": _digest(summary_path),
        "outcomePath": _relative(outcome_path, repo_root),
        "outcomeDigest": _digest(outcome_path),
    }
    merged_commit = None
    if isinstance(bindings, dict) and bindings.get("lifecycleStage") == "post_merge":
        candidate = bindings.get("headCommit")
        if isinstance(candidate, str) and len(candidate) == 40:
            merged_commit = candidate

    # A legacy Work Item is known to exist but lacks the new projection fields.
    # Preserve that distinction: ``partial`` means the record is usable but
    # incomplete, while ``unknown`` is reserved for an unusable/undetermined
    # knowledge state supplied by a future source adapter.
    state = "verified" if approach_verified else "partial"
    record = {
        "schemaVersion": 1,
        "workItemId": work_item_id,
        "title": contract.get("title", work_item_id),
        "topics": summary.get("topics", []) if isinstance(summary.get("topics"), list) else [],
        "components": summary.get("components", [])
        if isinstance(summary.get("components"), list)
        else [],
        "implementation": implementation,
        "configuration": summary.get("configurationApproach"),
        "changes": _changes(summary),
        "designDecisions": projected_decisions,
        "effects": summary.get("effects", []) if isinstance(summary.get("effects"), list) else [],
        "evidence": evidence,
        "mergedCommit": merged_commit,
        "effectiveState": effective_state,
        "currentValidity": "unknown",
        "supersedes": supersedes,
        "generatedFrom": generated_from,
        "knowledgeState": state,
        "unknowns": unknowns,
    }
    if has_date and explicit_date is not None:
        record["date"] = explicit_date
    return record


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def build_index(records_dir: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for record_path in sorted(records_dir.glob("*.json")):
        record = _load(record_path)
        work_item_id = record.get("workItemId")
        if not isinstance(work_item_id, str):
            raise TypeError(f"record workItemId is required: {record_path}")
        items.append(
            {
                "workItemId": work_item_id,
                "title": record.get("title", work_item_id),
                "topics": record.get("topics", []),
                "components": record.get("components", []),
                "state": record.get("knowledgeState", "unknown"),
                "knowledgePath": f".ai/knowledge/work-items/{record_path.name}",
            }
        )
    items.sort(key=lambda item: item["workItemId"])
    return {"schemaVersion": 1, "workItems": items}


def rebuild_index(records_dir: Path, output_path: Path) -> dict[str, Any]:
    result = build_index(records_dir)
    _atomic_write(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--outcome", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    record = build_record(args.contract, args.summary, args.outcome, repo_root=args.repo_root)
    _atomic_write(args.output, record)
    rebuild_index(args.output.parent, args.index)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
