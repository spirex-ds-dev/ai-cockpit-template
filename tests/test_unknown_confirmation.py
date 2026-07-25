from datetime import datetime, timezone

import pytest

from ai_unknown_confirmation import (
    build_confirmation_request,
    validate_assessment,
    validate_confirmation,
)


def assessment(**overrides):
    value = {
        "schemaVersion": 1,
        "assessmentId": "unknown-1",
        "subject": "work-item",
        "state": "unknown",
        "knownUnknowns": [{"id": "u-1", "statement": "Provider evidence is unavailable"}],
        "unresolvedQuestions": [{"id": "q-1", "statement": "Which role can confirm?"}],
        "assumptions": [],
        "examinedAreas": ["local tests"],
        "unexaminedAreas": ["hosted provider"],
        "evidenceGaps": [{"id": "g-1", "statement": "No provider run"}],
    }
    value.update(overrides)
    return value


def test_unknown_assessment_preserves_explicit_state():
    assert validate_assessment(assessment()) == []


@pytest.mark.parametrize(
    "value,expected",
    [
        (assessment(state="not_applicable"), "notApplicableReason"),
        (assessment(state="known"), "known state"),
    ],
)
def test_unknown_states_fail_when_evidence_does_not_match(value, expected):
    assert any(expected in item for item in validate_assessment(value))


def test_confirmation_request_is_structured_and_stops_by_default():
    request = build_confirmation_request(
        problem="Need a decision",
        reason="Evidence gap",
        known_evidence=["ev-1"],
        unknown_evidence=["gap-1"],
        options=["wait", "use fixture"],
        recommendation="use fixture",
        consequences=["release remains blocked"],
        question="Proceed with fixture?",
    )
    assert request["status"] == "needs_human_confirmation"
    assert request["defaultAction"] == "STOP"


def test_confirmation_rejects_expiry_scope_digest_and_ok_only():
    record = {
        "role": "security",
        "objectId": "other",
        "scopeDigest": "sha256:" + "0" * 64,
        "evidenceDigest": "sha256:" + "1" * 64,
        "expiresAt": "2020-01-01T00:00:00Z",
        "decision": "approved",
        "response": "OK",
    }
    errors = validate_confirmation(
        record,
        object_id="work-item",
        scope_digest="sha256:" + "2" * 64,
        evidence_digest="sha256:" + "3" * 64,
        now=datetime(2026, 7, 25, tzinfo=timezone.utc),
        critical=True,
    )
    assert {
        "object scope mismatch",
        "scope digest mismatch",
        "evidence digest mismatch",
        "confirmation is expired",
        "critical confirmation cannot be an OK-only response",
    }.issubset(errors)
