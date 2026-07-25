"""Focused tests for fail-closed Task Outcome validation."""

from scripts.ai_generate_task_outcome import generate_outcome, render_markdown
from scripts.ai_check_task_outcome import validate_outcome


def bindings() -> dict[str, object]:
    return {
        "taskId": "task-outcome-validator",
        "contractDigest": "a" * 64,
        "summaryDigest": "b" * 64,
        "verificationDigest": "c" * 64,
        "baseCommit": "1" * 40,
        "headCommit": "2" * 40,
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


def test_valid_conditional_claim_and_matching_residual_risk_pass() -> None:
    candidate = outcome()
    risk = {
        "kind": "potential_risk",
        "severity": "high",
        "title": "Residual",
        "state": "accepted",
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
