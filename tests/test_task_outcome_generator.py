"""Focused tests for evidence-derived Task Outcome generation."""

from scripts.ai_generate_task_outcome import generate_outcome, render_markdown


def bindings() -> dict[str, object]:
    return {
        "taskId": "task-outcome-generator",
        "contractDigest": "a" * 64,
        "summaryDigest": "b" * 64,
        "verificationDigest": "c" * 64,
        "baseCommit": "1" * 40,
        "headCommit": "2" * 40,
        "pullRequest": {"number": 15, "url": "https://example.test/pull/15"},
        "aiCockpitVersion": "1.0",
        "generatorVersion": "1.0",
    }


def event(event_id: str, event_type: str, **extra: object) -> dict[str, object]:
    return {
        "eventId": event_id,
        "eventType": event_type,
        "workItemId": "task-outcome-generator",
        "occurredAt": "2026-07-25T00:00:00Z",
        "evidence": [{"source": "pytest", "subject": event_id}],
        **extra,
    }


def test_empty_evidence_has_all_sections_and_none_markdown() -> None:
    outcome = generate_outcome("task-outcome-generator", bindings(), events=[])
    assert outcome["status"] == "completed"
    assert set(outcome["sections"]) == {
        "outcomeSummary",
        "taskOverview",
        "deliveredChanges",
        "findings",
        "risks",
        "warnings",
        "interventions",
        "forcedStops",
        "resolutions",
        "recurrencePrevention",
        "avoidedImpact",
        "residualRisks",
        "humanDecisions",
        "evidence",
    }
    markdown = render_markdown(outcome)
    assert "## Findings\nNone" in markdown
    assert "## Residual Risks\nNone" in markdown


def test_publication_evidence_is_bound_into_final_outcome_evidence():
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "publication": {
                "releaseUrl": "https://example.test/releases/v1.0.0",
                "tag": "v1.0.0",
                "targetSha": "2" * 40,
                "workflowRunId": "123",
                "assetDigest": "a" * 64,
                "quickInstall": "passed",
            }
        },
    )
    publication = outcome["sections"]["evidence"][0]
    assert publication["source"] == "release-workflow"
    assert publication["subject"] == "v1.0.0"
    assert publication["digest"] == "a" * 64


def test_findings_are_deduplicated_but_post_fix_recurrence_is_new() -> None:
    base = {
        "findingFingerprint": "fingerprint-1",
        "category": "defect",
        "severity": "medium",
        "title": "A finding",
        "description": "Observed once",
    }
    events = [
        event("finding-1", "finding", **base),
        event("finding-duplicate", "finding", **base),
        event("finding-recurrence", "finding", **base, recurrence="post_fix"),
    ]
    findings = generate_outcome("task-outcome-generator", bindings(), events=events)["sections"][
        "findings"
    ]
    assert len(findings) == 2
    assert any(item["findingFingerprint"] == "fingerprint-1" for item in findings)


def test_stop_human_decision_resolution_prevention_and_conditional_impact() -> None:
    events = [
        event(
            "stop-1",
            "stop",
            stage="preflight",
            reason="Missing evidence",
            policyOrGuard="Evidence Guard",
            attemptedAction="Continue",
            result="unresolved",
            avoidedImpact="a false success claim",
        ),
        event("confirm-1", "confirmation", decision="User authorized continuation"),
        event(
            "resolve-1",
            "resolution",
            problem="Missing evidence",
            action="Added evidence",
            verification="Focused test",
            result="resolved",
        ),
        event(
            "prevent-1",
            "prevention",
            kind="Automated Check",
            coverage="The check detects recurrence",
            humanDependency="Review remains required",
        ),
        event(
            "risk-1",
            "risk",
            kind="potential_risk",
            severity="high",
            title="Residual risk",
            state="accepted",
        ),
    ]
    sections = generate_outcome("task-outcome-generator", bindings(), events=events)["sections"]
    assert sections["forcedStops"][0]["policyOrGuard"] == "Evidence Guard"
    assert sections["humanDecisions"] == ["User authorized continuation"]
    assert sections["resolutions"][0]["result"] == "resolved"
    assert sections["recurrencePrevention"][0]["kind"] == "Automated Check"
    assert sections["avoidedImpact"] == [
        "If not detected, could have led to a false success claim."
    ]
    assert sections["residualRisks"][0]["title"] == "Residual risk"


def test_statuses_and_output_are_deterministic() -> None:
    events = [event("warning-1", "warning", message="A warning")]
    first = generate_outcome("task-outcome-generator", bindings(), events=events)
    second = generate_outcome("task-outcome-generator", bindings(), events=list(reversed(events)))
    assert first == second
    assert first["status"] == "completed_with_warnings"
    assert "score" not in repr(first).lower()


def test_structured_evidence_is_carried_without_secret_fields() -> None:
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "deliveredChanges": ["scripts/ai_generate_task_outcome.py"],
            "warnings": ["A documented warning"],
            "humanDecisions": ["Owner approved the bounded change"],
            "sources": [{"source": "contract", "subject": "acceptance"}],
            "password": "must never be copied",
        },
    )
    assert outcome["sections"]["deliveredChanges"] == ["scripts/ai_generate_task_outcome.py"]
    assert outcome["sections"]["warnings"] == ["A documented warning"]
    assert outcome["sections"]["humanDecisions"] == ["Owner approved the bounded change"]
    assert "password" not in repr(outcome).lower()


def test_explicit_final_statuses_are_preserved() -> None:
    for status in (
        "completed",
        "completed_with_warnings",
        "needs_human_confirmation",
        "blocked",
        "cancelled",
    ):
        assert (
            generate_outcome("task-outcome-generator", bindings(), evidence={"status": status})[
                "status"
            ]
            == status
        )


def test_invalid_event_values_use_safe_defaults_and_interventions_are_visible() -> None:
    events = [
        event(
            "finding-1",
            "finding",
            findingFingerprint="fp",
            category="unsupported",
            severity="unsupported",
        ),
        event("risk-1", "risk", kind="unsupported", severity="unsupported", title="Risk"),
        event(
            "intervention-1",
            "intervention",
            kind="unsupported",
            avoidedImpact="a claim",
            evidence=[],
        ),
        event(
            "intervention-2",
            "intervention",
            kind="prevented",
            title="Guard",
            description="Guard ran",
        ),
        event("confirmation-2", "confirmation", decision=" ", description="Fallback decision"),
    ]
    sections = generate_outcome("task-outcome-generator", bindings(), events=events)["sections"]
    assert sections["findings"][0]["category"] == "other"
    assert sections["findings"][0]["severity"] == "medium"
    assert sections["risks"][0]["kind"] == "potential_risk"
    assert sections["interventions"][0]["kind"] == "observed"
    assert sections["interventions"][1]["kind"] == "prevented"
    assert sections["humanDecisions"] == ["Fallback decision"]


def test_evidence_reference_forms_and_conditional_language_are_normalized() -> None:
    events = [
        event(
            "warning-1",
            "warning",
            evidence=[{"source": "check", "subject": "warning", "digest": "d" * 64}, "plain"],
        ),
        event("risk-1", "risk", avoidedImpact="If not detected, could have exposed a gap"),
        event("resolution-1", "resolution", avoidedImpact="如果未被发现，可能导致风险"),
    ]
    outcome = generate_outcome("task-outcome-generator", bindings(), events=events)
    assert any(ref.get("digest") == "d" * 64 for ref in outcome["sections"]["evidence"])
    assert any(item.startswith("If not detected") for item in outcome["sections"]["avoidedImpact"])
    assert any(item.startswith("如果未被发现") for item in outcome["sections"]["avoidedImpact"])
