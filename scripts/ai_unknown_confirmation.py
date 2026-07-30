"""Validate explicit unknown assessments and scoped human confirmations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

STATES = {"known", "unknown", "needs_human_confirmation", "not_applicable"}
ROLES = {"reviewer", "owner", "security", "release"}


def validate_assessment(assessment: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if assessment.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if not assessment.get("assessmentId") or not assessment.get("subject"):
        errors.append("assessmentId and subject are required")
    state = assessment.get("state")
    if state not in STATES:
        errors.append("state is invalid")
    required_arrays = (
        "knownUnknowns",
        "unresolvedQuestions",
        "assumptions",
        "examinedAreas",
        "unexaminedAreas",
        "evidenceGaps",
    )
    for name in required_arrays:
        if not isinstance(assessment.get(name), list):
            errors.append(f"{name} must be an array")
    if state == "not_applicable" and not assessment.get("notApplicableReason"):
        errors.append("not_applicable requires notApplicableReason")
    if state == "known" and (
        assessment.get("knownUnknowns")
        or assessment.get("unresolvedQuestions")
        or assessment.get("evidenceGaps")
    ):
        errors.append("known state cannot contain unresolved unknowns or evidence gaps")
    return sorted(set(errors))


def build_confirmation_request(
    *,
    problem: str,
    reason: str,
    known_evidence: list[str],
    unknown_evidence: list[str],
    options: list[str],
    recommendation: str,
    consequences: list[str],
    question: str,
) -> dict[str, Any]:
    """Return the structured handoff; STOP is always the default action."""

    fields = {
        "problem": problem,
        "reason": reason,
        "knownEvidence": known_evidence,
        "unknownEvidence": unknown_evidence,
        "options": options,
        "recommendation": recommendation,
        "consequences": consequences,
        "question": question,
    }
    if not problem or not reason or not options or not recommendation or not question:
        raise ValueError(
            "confirmation request requires problem, reason, options, recommendation and question"
        )
    return {"status": "needs_human_confirmation", **fields, "defaultAction": "STOP"}


def validate_confirmation(
    record: dict[str, Any],
    *,
    object_id: str,
    scope_digest: str,
    evidence_digest: str,
    now: datetime | None = None,
    critical: bool = False,
) -> list[str]:
    errors: list[str] = []
    if record.get("role") not in ROLES:
        errors.append("role is invalid")
    if record.get("objectId") != object_id:
        errors.append("object scope mismatch")
    if record.get("scopeDigest") != scope_digest:
        errors.append("scope digest mismatch")
    if record.get("evidenceDigest") != evidence_digest:
        errors.append("evidence digest mismatch")
    if record.get("decision") not in {"approved", "rejected"}:
        errors.append("decision is required")
    try:
        expiry = datetime.fromisoformat(str(record.get("expiresAt", "")))
        if expiry <= (now or datetime.now(UTC)):
            errors.append("confirmation is expired")
    except ValueError:
        errors.append("expiresAt is invalid")
    if critical and record.get("response", "").strip().casefold() in {"ok", "approved"}:
        errors.append("critical confirmation cannot be an OK-only response")
    return sorted(set(errors))
