"""Validate and evaluate time-bound external enterprise control evidence.

Repository records can describe a control requirement, but cannot turn a local
receipt or a checklist entry into an enterprise compliance verdict.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

REQUIRED_FIELDS = (
    "controlId",
    "provider",
    "resource",
    "requiredState",
    "observedState",
    "evidenceType",
    "verifiedAt",
    "owner",
    "limitation",
    "expiresAt",
)
OBSERVED_STATES = {"not_verified", "observed"}
EXTERNAL_EVIDENCE_TYPES = {"external_provider", "external_enterprise"}


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_timestamp(value: Any) -> datetime | None:
    if not _non_empty(value):
        return None
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        return None
    return timestamp if timestamp.tzinfo else None


def validate_control_record(record: Any) -> list[str]:
    """Return structural and provenance errors for one observed-control record."""
    if not isinstance(record, dict):
        return ["control evidence record must be an object"]
    issues = [
        f"missing required field: {field}" for field in REQUIRED_FIELDS if field not in record
    ]
    if issues:
        return issues
    state = record["observedState"]
    if state not in OBSERVED_STATES:
        issues.append("observedState must be one of: not_verified, observed")
    if not _non_empty(record["controlId"]):
        issues.append("controlId must be non-empty")
    if not _non_empty(record["resource"]):
        issues.append("resource must be non-empty")
    if not _non_empty(record["requiredState"]):
        issues.append("requiredState must be non-empty")
    if not _non_empty(record["owner"]):
        issues.append("owner must be non-empty")
    if not _non_empty(record["limitation"]):
        issues.append("limitation must be non-empty")
    if state == "observed":
        if not _non_empty(record["provider"]):
            issues.append("observed control evidence requires a provider")
        if record["evidenceType"] not in EXTERNAL_EVIDENCE_TYPES:
            issues.append("observed control evidence must use an external evidence type")
        if _parse_timestamp(record["verifiedAt"]) is None:
            issues.append("observed control evidence requires a timezone-aware verifiedAt")
        if _parse_timestamp(record["expiresAt"]) is None:
            issues.append("observed control evidence requires a timezone-aware expiresAt")
    elif record["evidenceType"] not in {"none", *EXTERNAL_EVIDENCE_TYPES}:
        issues.append("not_verified control evidence must use none or an external evidence type")
    return issues


def evaluate_control(record: Any, *, now: datetime) -> dict[str, list[str] | str]:
    """Derive a fail-closed state without modifying any governance facts."""
    issues = validate_control_record(record)
    if issues:
        return {"state": "not_verified", "reasons": ["control_evidence_invalid"]}
    if not isinstance(record, dict):
        return {"state": "not_verified", "reasons": ["control_evidence_invalid"]}
    if record["observedState"] != "observed":
        return {"state": "not_verified", "reasons": ["external_evidence_missing"]}
    expires_at = _parse_timestamp(record["expiresAt"])
    if expires_at is None:
        return {"state": "not_verified", "reasons": ["control_evidence_invalid"]}
    if now.astimezone(UTC) > expires_at.astimezone(UTC):
        return {"state": "not_verified", "reasons": ["external_evidence_expired"]}
    return {"state": "observed", "reasons": []}
