"""Focused tests for fail-closed Task Outcome validation."""

import json
from pathlib import Path

from scripts.ai_check_task_outcome import validate_outcome
from scripts.ai_generate_task_outcome import generate_outcome, render_markdown


def bindings() -> dict[str, object]:
    return {
        "taskId": "task-outcome-validator",
        "contractDigest": "a" * 64,
        "summaryDigest": "b" * 64,
        "verificationDigest": "c" * 64,
        "baseCommit": "1" * 40,
        "headCommit": "2" * 40,
        "lifecycleStage": "post_pr",
        "pullRequest": {"number": 16, "url": "https://example.test/pull/16"},
        "aiCockpitVersion": "1.0",
        "generatorVersion": "1.0",
    }


def outcome() -> dict[str, object]:
    return generate_outcome("task-outcome-validator", bindings())


def test_valid_empty_outcome_passes_and_all_statuses_are_allowed() -> None:
    for status in (
        "completed",
        "completed_with_warnings",
        "needs_human_confirmation",
        "blocked",
        "cancelled",
    ):
        candidate = outcome()
        candidate["status"] = status
        report = validate_outcome(
            candidate, render_markdown(candidate), expected_task_id="task-outcome-validator"
        )
        assert report.valid, report.errors


def test_contract_style_underscore_work_item_id_is_valid() -> None:
    task_id = "adopt_ai_cockpit"
    candidate_bindings = bindings()
    candidate_bindings["taskId"] = task_id
    candidate = generate_outcome(task_id, candidate_bindings)

    report = validate_outcome(candidate, render_markdown(candidate), expected_task_id=task_id)

    assert report.valid, report.errors


def test_schema_binding_and_provenance_fail_closed() -> None:
    candidate = outcome()
    candidate["workItemId"] = "other-task"
    candidate["bindings"]["headCommit"] = "bad"
    report = validate_outcome(candidate, expected_task_id="task-outcome-validator")
    assert not report.valid
    assert {error.code for error in report.errors} >= {"task_binding", "binding"}


def test_privacy_event_relationship_and_shape_fail_closed() -> None:
    candidate = outcome()
    candidate["sections"]["warnings"] = [{"password": "secret"}]
    events = [{"eventId": "one", "correctsEventId": "missing"}]
    report = validate_outcome(candidate, events=events, expected_task_id="task-outcome-validator")
    assert not report.valid
    assert {error.code for error in report.errors} >= {
        "privacy",
        "event_relationship",
        "section_shape",
    }


def test_claim_rules_and_residual_risk_visibility_are_enforced() -> None:
    candidate = outcome()
    risk = {
        "kind": "potential_risk",
        "severity": "high",
        "title": "Residual",
        "state": "accepted",
        "decisionOwner": "repository_administrator",
        "requiredEvidence": ["approval receipt"],
        "mitigation": "Keep the claim blocked.",
        "acceptanceStatus": "accepted",
        "evidence": [],
    }
    candidate["sections"]["risks"] = [risk]
    candidate["sections"]["residualRisks"] = []
    candidate["sections"]["avoidedImpact"] = ["This prevented 90% of incidents."]
    candidate["sections"]["outcomeSummary"] = "Score: 99"
    markdown = "## Findings\nNone\n"
    report = validate_outcome(candidate, markdown, expected_task_id="task-outcome-validator")
    assert not report.valid
    assert {error.code for error in report.errors} >= {
        "residual_risk",
        "conditional_claim",
        "unsupported_quantification",
        "markdown_parity",
    }


def test_warning_without_a_structured_limitation_is_rejected() -> None:
    candidate = outcome()
    candidate["sections"]["warnings"] = ["Hosted provider checks were not run."]

    report = validate_outcome(
        candidate, render_markdown(candidate), expected_task_id="task-outcome-validator"
    )

    assert not report.valid
    assert "warning_binding" in {error.code for error in report.errors}


def test_archived_wi_10_not_run_warning_cannot_bypass_structured_bindings() -> None:
    archived = Path(__file__).parents[1] / (
        ".ai/work-items/archive/2026/wi-10-end-to-end-adoption-validation.outcome.json"
    )
    candidate = json.loads(archived.read_text(encoding="utf-8"))

    report = validate_outcome(candidate, expected_task_id="wi-10-end-to-end-adoption-validation")

    assert not report.valid
    assert "warning_binding" in {error.code for error in report.errors}


def test_not_run_evidence_rejects_enterprise_or_platform_verified_claims() -> None:
    candidate = outcome()
    warning = "Hosted provider checks were not_run."
    candidate["sections"]["warnings"] = [warning]
    candidate["sections"]["limitations"] = [
        {
            "sourceWarning": warning,
            "title": "Hosted evidence is absent",
            "affectedClaims": ["provider_verified"],
            "requiredEvidence": ["provider receipt"],
            "forbiddenClaims": ["Do not claim provider verification."],
        }
    ]
    candidate["sections"]["nonRiskExplanations"] = [
        {"sourceWarning": warning, "reason": "The Provider was not contacted.", "evidence": []}
    ]
    candidate["sections"]["forbiddenClaims"] = ["Do not claim provider verification."]
    candidate["sections"]["outcomeSummary"] = "Platform-verified and enterprise-ready."

    report = validate_outcome(candidate, render_markdown(candidate))

    assert not report.valid
    assert "not_run_claim" in {error.code for error in report.errors}


def test_warning_with_a_limitation_risk_and_forbidden_claim_is_valid() -> None:
    candidate = outcome()
    warning = "Hosted provider checks were not run."
    candidate["status"] = "completed_with_warnings"
    candidate["sections"]["warnings"] = [warning]
    candidate["sections"]["limitations"] = [
        {
            "sourceWarning": warning,
            "title": "Provider checks are absent",
            "affectedClaims": ["provider_verified"],
            "requiredEvidence": ["provider receipt"],
            "forbiddenClaims": ["Do not claim provider verification."],
        }
    ]
    risk = {
        "kind": "potential_risk",
        "severity": "medium",
        "title": "Provider controls remain unverified",
        "state": "unresolved",
        "sourceWarning": warning,
        "affectedClaims": ["provider_verified"],
        "requiredEvidence": ["provider receipt"],
        "decisionOwner": "repository_administrator",
        "mitigation": "Do not make provider-backed claims.",
        "acceptanceStatus": "open",
        "blockingFor": ["enterprise_ready"],
        "evidence": [],
    }
    candidate["sections"]["risks"] = [risk]
    candidate["sections"]["residualRisks"] = [risk]
    candidate["sections"]["forbiddenClaims"] = ["Do not claim provider verification."]

    report = validate_outcome(
        candidate, render_markdown(candidate), expected_task_id="task-outcome-validator"
    )

    assert report.valid, report.errors


def test_valid_conditional_claim_and_matching_residual_risk_pass() -> None:
    candidate = outcome()
    risk = {
        "kind": "potential_risk",
        "severity": "high",
        "title": "Residual",
        "state": "accepted",
        "decisionOwner": "repository_administrator",
        "requiredEvidence": ["approval receipt"],
        "mitigation": "Keep the claim blocked.",
        "acceptanceStatus": "accepted",
        "evidence": [],
    }
    candidate["sections"]["risks"] = [risk]
    candidate["sections"]["residualRisks"] = [risk]
    candidate["sections"]["avoidedImpact"] = [
        "If not detected, could have led to a false success claim."
    ]
    report = validate_outcome(
        candidate, render_markdown(candidate), expected_task_id="task-outcome-validator"
    )
    assert report.valid, report.errors


def test_duplicate_event_ids_and_invalid_severity_fail_closed() -> None:
    candidate = outcome()
    candidate["sections"]["risks"] = [
        {"title": "Risk", "state": "unresolved", "severity": "urgent"}
    ]
    report = validate_outcome(
        candidate,
        events=[{"eventId": "evt-1"}, {"eventId": "evt-1"}],
        expected_task_id="task-outcome-validator",
    )
    assert not report.valid
    assert {error.code for error in report.errors} >= {"event_identity", "severity"}
