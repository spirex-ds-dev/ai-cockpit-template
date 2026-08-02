from datetime import UTC, datetime

import pytest

from scripts.ai_enterprise_control_evidence import evaluate_control, validate_control_record


def external_record(**overrides):
    record = {
        "controlId": "branch_protection",
        "provider": "github",
        "resource": "spirex-ds-dev/ai-cockpit-template",
        "requiredState": "ruleset_enforced",
        "observedState": "observed",
        "evidenceType": "external_provider",
        "verifiedAt": "2026-08-02T00:00:00+00:00",
        "owner": "repository_administrator",
        "limitation": "Evidence is scoped to the named provider resource and expires.",
        "expiresAt": "2026-08-09T00:00:00+00:00",
    }
    record.update(overrides)
    return record


def test_missing_external_evidence_is_not_verified_with_a_reason():
    result = evaluate_control(
        external_record(
            provider=None,
            observedState="not_verified",
            evidenceType="none",
            verifiedAt=None,
            expiresAt=None,
            limitation="No current external provider receipt has been supplied.",
        ),
        now=datetime(2026, 8, 2, tzinfo=UTC),
    )

    assert result == {"state": "not_verified", "reasons": ["external_evidence_missing"]}


def test_expired_observed_evidence_is_not_verified():
    result = evaluate_control(
        external_record(expiresAt="2026-08-01T00:00:00+00:00"),
        now=datetime(2026, 8, 2, tzinfo=UTC),
    )

    assert result == {"state": "not_verified", "reasons": ["external_evidence_expired"]}


def test_repository_local_receipt_cannot_become_observed_control_evidence():
    issues = validate_control_record(
        external_record(evidenceType="repository_local", observedState="observed")
    )

    assert "observed control evidence must use an external evidence type" in issues


@pytest.mark.parametrize("value", ["compliant", "verified"])
def test_compliance_verdict_vocabulary_is_rejected(value):
    issues = validate_control_record(external_record(observedState=value))

    assert "observedState must be one of: not_verified, observed" in issues
