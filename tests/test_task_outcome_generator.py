"""Focused tests for evidence-derived Task Outcome generation."""

import json

from scripts.ai_check_task_outcome import validate_outcome
from scripts.ai_generate_task_outcome import generate_outcome, render_markdown


def bindings() -> dict[str, object]:
    return {
        "taskId": "task-outcome-generator",
        "contractDigest": "a" * 64,
        "summaryDigest": "b" * 64,
        "verificationDigest": "c" * 64,
        "baseCommit": "1" * 40,
        "headCommit": "2" * 40,
        "lifecycleStage": "post_pr",
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


def implementation_approach() -> dict[str, object]:
    refs = [{"source": "scripts/ai_generate_task_outcome.py", "subject": "projection"}]
    return {
        "approachType": "implementation",
        "status": "complete",
        "summary": {
            "text": "Customers can see how the governed result is produced.",
            "status": "verified",
            "evidence": refs,
        },
        "mechanism": {
            "text": "Summary approach data is projected into the Outcome sections.",
            "status": "verified",
            "evidence": refs,
        },
        "affectedComponents": [
            {
                "component": "Task Outcome",
                "detail": "Carries the structured approach.",
                "status": "verified",
                "evidence": refs,
            }
        ],
        "designDecisions": [
            {
                "decision": "Use evidence references for factual claims.",
                "reason": "Reviewers can inspect the source.",
                "status": "verified",
                "evidence": refs,
            }
        ],
        "technicalDetails": [],
        "evidence": [
            {
                "claim": "The projection has a deterministic code path.",
                "status": "verified",
                "source": "scripts/ai_generate_task_outcome.py",
                "subject": "projection",
            }
        ],
    }


def test_generator_projects_summary_implementation_approach_and_evidence():
    approach = implementation_approach()
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={"implementationApproach": approach},
    )

    assert outcome["sections"]["implementationApproach"] == approach
    assert "Customers can see how the governed result is produced." in render_markdown(outcome)


def test_ai_finish_summary_source_is_projected_without_manual_approach_input(tmp_path, monkeypatch):
    import ai_finish

    contract_path = tmp_path / "task.contract.json"
    summary_path = tmp_path / "task.summary.json"
    contract_path.write_text(json.dumps({"baseCommit": "a" * 40}), encoding="utf-8")
    summary_path.write_text(
        json.dumps(
            {
                "changedFiles": [],
                "verification": [],
                "implementationApproach": implementation_approach(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "current_head", lambda: "b" * 40)
    monkeypatch.chdir(tmp_path)

    payload = ai_finish._pre_merge_outcome_input(
        "task-outcome-generator", contract_path, summary_path, "en"
    )
    outcome = generate_outcome(
        "task-outcome-generator", payload["bindings"], evidence=payload["evidence"]
    )

    assert outcome["sections"]["implementationApproach"] == implementation_approach()


def test_missing_implementation_approach_becomes_a_yellow_incomplete_warning():
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={"sources": [{"source": "task.summary.json", "subject": "Summary"}]},
    )

    assert outcome["sections"]["implementationApproach"]["status"] == "incomplete"
    assert outcome["status"] == "completed_with_warnings"
    assert outcome["humanStatusColor"] == "yellow"
    assert any("Implementation Approach" in warning for warning in outcome["sections"]["warnings"])


def test_legacy_contract_without_approach_signal_remains_not_applicable(tmp_path):
    contract = tmp_path / "task.contract.json"
    summary = tmp_path / "task.summary.json"
    contract.write_text(json.dumps({"workItemId": "task-outcome-generator"}), encoding="utf-8")
    summary.write_text(json.dumps({}), encoding="utf-8")

    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "sources": [
                {"source": str(contract), "subject": "Contract"},
                {"source": str(summary), "subject": "Summary"},
            ]
        },
    )

    assert outcome["sections"]["implementationApproach"]["status"] == "not_applicable"
    assert outcome["status"] == "completed"


def test_unverified_approach_does_not_claim_benchmark_performance():
    approach = implementation_approach()
    approach["summary"] = {
        "text": "The path changed; no benchmark was run.",
        "status": "unverified",
        "evidence": [],
    }
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={"implementationApproach": approach},
    )

    rendered = render_markdown(outcome)
    assert "performance improved" not in rendered.lower()
    assert "no benchmark was run" in rendered


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
        "limitations",
        "nonRiskExplanations",
        "forbiddenClaims",
        "interventions",
        "forcedStops",
        "resolutions",
        "recurrencePrevention",
        "avoidedImpact",
        "residualRisks",
        "humanDecisions",
        "evidence",
        "implementationApproach",
    }
    markdown = render_markdown(outcome)
    assert "## Findings\nNone" in markdown
    assert "## Residual Risks\nNone" in markdown


def test_human_handoff_answers_the_required_human_questions() -> None:
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "locale": "zh-CN",
            "completed": [
                {
                    "title": "Added the handoff projection",
                    "detail": "The Outcome now carries human-readable completion facts.",
                    "evidence": [{"source": "summary", "subject": "changedFiles"}],
                }
            ],
            "passedChecks": [
                {
                    "title": "Focused tests",
                    "detail": "The generator and renderer tests passed.",
                    "evidence": [{"source": "pytest", "subject": "focused-suite"}],
                }
            ],
            "retained": [
                {
                    "title": "Provider verification scope",
                    "detail": "No provider-specific claim is made in this local run.",
                    "evidence": [{"source": "summary", "subject": "knownGaps"}],
                }
            ],
            "risks": [
                {
                    "severity": "medium",
                    "title": "Environment-specific evidence",
                    "detail": "Results are bounded to the measured environment.",
                    "state": "unresolved",
                    "evidence": [{"source": "summary", "subject": "residualRisks"}],
                }
            ],
            "handoffQuestions": {
                "problemCount": 1,
                "blockedProblems": [],
                "resolvedProblems": ["Missing human-readable completion details"],
                "resolutionApproach": ["Added a versioned evidence-derived handoff."],
                "avoidedRisks": ["A false green archive claim"],
                "remainingRisks": ["Locale still requires explicit agent binding"],
                "agentUnknowns": ["Provider UI transport is intentionally unspecified"],
                "humanConfirmations": ["Review the bounded provider-claim limitation"],
                "recurrenceLikelihood": "低：validator and finish gate now enforce the handoff.",
                "nextTime": "Pass the conversation locale and retain evidence details from the start.",
            },
        },
    )
    handoff = outcome["humanHandoff"]
    assert handoff["locale"] == "zh-CN"
    assert handoff["completed"][0]["detail"]
    assert handoff["passed"][0]["evidence"]
    assert handoff["questions"]["problemCount"] == 1
    assert validate_outcome(outcome, render_markdown(outcome)).valid


def test_handoff_preserves_evidence_bound_resolution_claims() -> None:
    refs = [{"source": "summary.json", "subject": "observedIssues[0]"}]
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "locale": "en",
            "handoffQuestions": {
                "problemCount": 1,
                "problemCountEvidenceRefs": refs,
                "resolvedProblems": [
                    {
                        "claim": "The projection was synchronized.",
                        "evidenceRefs": refs,
                        "inference": False,
                    }
                ],
                "resolutionApproach": [
                    {
                        "claim": "Used the canonical synchronizer.",
                        "evidenceRefs": refs,
                        "inference": False,
                    }
                ],
            },
        },
    )
    questions = outcome["humanHandoff"]["questions"]
    assert questions["resolvedProblems"][0]["evidenceRefs"] == refs
    assert questions["resolvedProblems"][0]["inference"] is False
    assert questions["resolutionApproach"][0]["evidenceRefs"] == refs
    assert validate_outcome(outcome, render_markdown(outcome)).valid


def test_structured_resolution_and_risk_records_populate_top_level_sections() -> None:
    refs = [{"source": "summary.json", "subject": "observedIssues[0]"}]
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "locale": "en",
            "resolutions": [
                {
                    "problem": "The projection was stale.",
                    "action": "Synchronized the projection.",
                    "verification": "Projection digest matched.",
                    "result": "resolved",
                    "evidence": refs,
                }
            ],
            "handoffRisks": [
                {
                    "severity": "medium",
                    "title": "Historical archive",
                    "detail": "Prior Outcomes remain immutable.",
                    "state": "unresolved",
                    "evidence": [{"source": "archive", "subject": "manifest"}],
                }
            ],
            "humanDecisions": [
                "Continue with the bounded correction",
                "Continue with the bounded correction",
            ],
        },
    )
    sections = outcome["sections"]
    assert sections["resolutions"][0]["problem"] == "The projection was stale."
    assert sections["resolutions"][0]["evidence"] == refs
    assert sections["residualRisks"][0]["detail"] == "Prior Outcomes remain immutable."
    assert sections["humanDecisions"] == ["Continue with the bounded correction"]
    markdown = render_markdown(outcome)
    assert "## Resolutions\n- The projection was stale.: Synchronized the projection." in markdown
    assert "## Residual Risks\n- Historical archive: Prior Outcomes remain immutable." in markdown
    assert validate_outcome(outcome, markdown).valid


def test_handoff_risk_controls_survive_outcome_normalization() -> None:
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "handoffRisks": [
                {
                    "severity": "high",
                    "title": "Provider publication",
                    "detail": "Provider evidence is pending.",
                    "state": "unresolved",
                    "decisionOwner": "release maintainer",
                    "requiredEvidence": ["same-SHA rehearsal receipt"],
                    "mitigation": "Do not publish until the receipt passes.",
                    "acceptanceStatus": "pending",
                    "evidence": [{"source": "summary.json", "subject": "residualRisks"}],
                }
            ]
        },
    )

    risk = outcome["humanHandoff"]["risks"][0]
    assert risk["decisionOwner"] == "release maintainer"
    assert risk["requiredEvidence"] == ["same-SHA rehearsal receipt"]
    assert risk["mitigation"] == "Do not publish until the receipt passes."
    assert risk["acceptanceStatus"] == "pending"
    assert validate_outcome(outcome, render_markdown(outcome)).valid


def test_red_handoff_contains_gate_cause_location_and_recovery() -> None:
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "locale": "zh-CN",
            "status": "blocked",
            "failedGate": "quality",
            "recoveryCondition": "Run the quality retry after fixing the failing test.",
            "redReasons": [
                {
                    "gate": "quality",
                    "cause": "The project test failed.",
                    "location": "tests/test_example.py::test_failure",
                    "recovery": "Fix the failing assertion and rerun quality.",
                    "evidence": [{"source": "pytest", "subject": "failure"}],
                }
            ],
        },
    )
    reason = outcome["humanHandoff"]["redReasons"][0]
    assert reason["gate"] == "quality"
    assert reason["location"]
    assert reason["recovery"]
    assert validate_outcome(outcome, render_markdown(outcome)).valid


def test_evidence_free_claims_are_marked_as_inference_and_handoff_is_required() -> None:
    outcome = generate_outcome("task-outcome-generator", bindings(), evidence={"locale": "en"})
    assert outcome["humanHandoff"]["completed"][0]["inference"] is True
    assert outcome["humanHandoff"]["completed"][0]["evidenceRefs"] == []
    missing = dict(outcome)
    missing.pop("humanHandoff")
    report = validate_outcome(missing, render_markdown(outcome))
    assert any(error.code == "human_handoff" for error in report.errors)


def test_self_praise_is_rejected_without_quantitative_evidence() -> None:
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "locale": "en",
            "completed": [
                {
                    "title": "dramatically improved project quality",
                    "detail": "dramatically improved project quality",
                    "evidence": [],
                }
            ],
        },
    )
    report = validate_outcome(outcome, render_markdown(outcome))
    assert any(error.code == "unsupported_self_praise" for error in report.errors)


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


def test_warning_mapping_is_preserved_from_evidence_and_risk_event():
    warning = "Hosted provider checks were not run."
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        events=[
            event(
                "risk-1",
                "risk",
                severity="medium",
                title="Provider evidence is absent",
                sourceWarning=warning,
                affectedClaims=["provider_verified"],
                requiredEvidence=["provider receipt"],
                decisionOwner="repository_administrator",
                mitigation="Do not make provider claims.",
                acceptanceStatus="open",
                blockingFor=["enterprise_ready"],
            )
        ],
        evidence={
            "warnings": [warning],
            "limitations": [
                {
                    "sourceWarning": warning,
                    "title": "Hosted evidence is absent",
                    "affectedClaims": ["provider_verified"],
                    "requiredEvidence": ["provider receipt"],
                    "forbiddenClaims": ["Do not claim provider verification."],
                }
            ],
            "forbiddenClaims": ["Do not claim provider verification."],
        },
    )

    assert outcome["sections"]["residualRisks"][0]["sourceWarning"] == warning
    assert validate_outcome(outcome, render_markdown(outcome)).valid


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


def test_resolved_stop_does_not_keep_current_outcome_yellow() -> None:
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        events=[
            event(
                "resolved-stop",
                "stop",
                reason="quality failed before the retry",
                state="resolved",
            ),
            event(
                "resolution",
                "resolution",
                problem="quality failed before the retry",
                action="The retry passed",
                state="resolved",
            ),
        ],
    )

    assert outcome["status"] == "completed"
    assert outcome["humanStatusColor"] == "green"
    assert outcome["sections"]["forcedStops"][0]["result"] == "resolved"


def test_unresolved_stop_keeps_current_outcome_yellow() -> None:
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        events=[event("unresolved-stop", "stop", result="unresolved")],
    )

    assert outcome["status"] == "needs_human_confirmation"
    assert outcome["humanStatusColor"] == "yellow"


def test_external_handoff_timeout_is_a_red_blocked_outcome() -> None:
    outcome = generate_outcome(
        "task-outcome-generator",
        bindings(),
        events=[event("timeout-1", "external_handoff_timeout", reason="receipt deadline expired")],
    )
    assert outcome["status"] == "blocked"
    assert outcome["humanStatusColor"] == "red"


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


def test_generated_outcome_projects_canonical_human_status_diagnostics() -> None:
    blocked = generate_outcome(
        "task-outcome-generator",
        bindings(),
        evidence={
            "status": "blocked",
            "failedGate": "quality",
            "recoveryCondition": "Run a passing quality retry.",
        },
    )
    completed = generate_outcome("task-outcome-generator", bindings())
    warning = generate_outcome(
        "task-outcome-generator", bindings(), evidence={"status": "completed_with_warnings"}
    )

    assert blocked["humanStatusColor"] == "red"
    assert blocked["failedGate"] == "quality"
    assert blocked["recoveryCondition"] == "Run a passing quality retry."
    assert completed["humanStatusColor"] == "green"
    assert completed["failedGate"] == ""
    assert completed["recoveryCondition"] == ""
    assert warning["humanStatusColor"] == "yellow"


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
