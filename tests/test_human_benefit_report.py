import json
from pathlib import Path

import ai_generate_human_report as human
import pytest

ROOT = Path(__file__).resolve().parents[1]


def outcome(*, status="completed", sections=None):
    default_sections = {
        "outcomeSummary": "Implemented the governed change.",
        "taskOverview": "Governed Work Item: example",
        "deliveredChanges": ["scripts/example.py"],
        "findings": [],
        "risks": [],
        "warnings": [],
        "limitations": [],
        "nonRiskExplanations": [],
        "forbiddenClaims": [],
        "interventions": [],
        "forcedStops": [],
        "resolutions": [],
        "recurrencePrevention": [],
        "avoidedImpact": [],
        "residualRisks": [],
        "humanDecisions": [],
        "evidence": [{"source": "contract.json", "subject": "Contract"}],
    }
    default_sections.update(sections or {})
    return {
        "format": "ai-cockpit-task-outcome",
        "schemaVersion": 1,
        "workItemId": "example",
        "status": status,
        "bindings": {
            "taskId": "example",
            "contractDigest": "a" * 64,
            "summaryDigest": "b" * 64,
            "verificationDigest": "c" * 64,
            "baseCommit": "d" * 40,
            "headCommit": "e" * 40,
            "lifecycleStage": "pre_merge",
            "pullRequest": {"state": "not_created"},
            "aiCockpitVersion": "repository-governance",
            "generatorVersion": "1.0",
        },
        "sections": default_sections,
    }


def test_review_report_derives_counts_risks_decisions_and_next_action():
    source = outcome(
        status="completed_with_warnings",
        sections={
            "findings": [
                {
                    "findingFingerprint": "fixed",
                    "category": "defect",
                    "severity": "high",
                    "title": "Test deletion",
                    "state": "resolved",
                    "description": "A required test was removed.",
                    "evidence": [{"source": "guard.json", "subject": "signal"}],
                }
            ],
            "risks": [
                {
                    "kind": "potential_risk",
                    "severity": "medium",
                    "title": "Dynamic use unknown",
                    "state": "unresolved",
                    "description": "Plugin use is not proven absent.",
                    "evidence": [{"source": "impact.json", "subject": "analysis"}],
                }
            ],
            "warnings": ["Hosted verification is pending."],
            "limitations": [
                {
                    "sourceWarning": "Hosted verification is pending.",
                    "title": "Hosted evidence is absent",
                    "affectedClaims": ["provider_verified"],
                    "requiredEvidence": ["provider receipt"],
                    "forbiddenClaims": ["Do not claim provider verification."],
                }
            ],
            "forbiddenClaims": ["Do not claim provider verification."],
            "forcedStops": [
                {
                    "stage": "before_edit",
                    "reason": "Reference evidence was incomplete.",
                    "policyOrGuard": "reference_impact_guard",
                    "attemptedAction": "delete API",
                    "conditionalImpact": "If not detected, could have broken consumers.",
                    "handoff": "Ask the API owner.",
                    "humanDecision": "Approve deprecation after migration.",
                    "recovery": "Provide owner evidence.",
                    "result": "resolved",
                    "evidence": [{"source": "stop.json", "subject": "stop"}],
                }
            ],
            "humanDecisions": ["Approve deprecation after migration."],
            "residualRisks": [
                {
                    "kind": "potential_risk",
                    "severity": "medium",
                    "title": "Dynamic use unknown",
                    "state": "unresolved",
                    "description": "Plugin use is not proven absent.",
                    "sourceWarning": "Hosted verification is pending.",
                    "evidence": [{"source": "impact.json", "subject": "analysis"}],
                }
            ],
        },
    )

    report = human.generate_human_report(source)

    assert report["phase"] == "review"
    assert report["issues"] == {
        "detected": 4,
        "hardStops": 1,
        "warnings": 1,
        "resolved": 2,
        "unresolved": 2,
    }
    assert report["preventedRisks"][0]["detectedBy"] == "reference_impact_guard"
    assert report["humanDecisions"] == ["Approve deprecation after migration."]
    assert report["limitations"][0]["title"] == "Hosted evidence is absent"
    assert report["forbiddenClaims"] == ["Do not claim provider verification."]
    assert report["remainingRisks"][0]["severity"] == "medium"
    assert report["nextSafeAction"] == "Provide owner evidence."
    assert human.validate_human_report(report, source) == []
    markdown = human.render_human_report(report)
    assert "AI Cockpit Task Report" in markdown
    assert "Detected issues: 4" in markdown
    assert "Provide owner evidence." in markdown
    assert "Do not claim provider verification." in markdown


def test_final_report_requires_and_binds_provider_closure_facts():
    source = outcome()
    facts = {
        "pullRequest": "https://example.invalid/pull/7",
        "mergeCommit": "f" * 40,
        "base": "origin/main",
        "baseCommit": "1" * 40,
        "workBranch": "codex/example",
        "cleanup": "scheduled",
        "continueFrom": "/workspace",
    }

    report = human.generate_human_report(source, phase="final", closure_facts=facts)

    assert report["closure"] == facts
    assert report["closureEvidenceState"] == "repository_recorded_only"
    assert report["nextSafeAction"] == "Continue from /workspace on synchronized origin/main."
    assert human.validate_human_report(report, source, closure_facts=facts) == []

    with pytest.raises(TypeError, match="closure facts"):
        human.generate_human_report(source, phase="final")


def test_validation_fails_closed_for_malformed_outcome_and_stale_report():
    source = outcome()
    source["bindings"]["contractDigest"] = "not-a-digest"
    with pytest.raises(ValueError, match="Task Outcome"):
        human.generate_human_report(source)

    source = outcome()
    report = human.generate_human_report(source)
    report["issues"]["detected"] = 99
    assert "report is stale or inconsistent with Task Outcome" in human.validate_human_report(
        report, source
    )


def test_cli_writes_and_checks_deterministic_json_and_markdown(tmp_path):
    source_path = tmp_path / "outcome.json"
    json_path = tmp_path / "task_report.json"
    markdown_path = tmp_path / "task_report.md"
    source_path.write_text(json.dumps(outcome()), encoding="utf-8")

    assert human.main([str(source_path), str(json_path), str(markdown_path)]) == 0
    assert human.main(["--check", str(source_path), str(json_path), str(markdown_path)]) == 0

    json_path.write_text(json.dumps({"reportVersion": 1}), encoding="utf-8")
    assert human.main(["--check", str(source_path), str(json_path), str(markdown_path)]) == 1


def test_installer_and_make_interfaces_distribute_human_report():
    catalog = json.loads((ROOT / "scripts/ai_installer_catalog.json").read_text(encoding="utf-8"))
    assert "ai_generate_human_report.py" in catalog["scripts"]
    for makefile in (ROOT / "Makefile", ROOT / "templates/make/Makefile.ai"):
        text = makefile.read_text(encoding="utf-8")
        assert "generate-human-benefit-report:" in text
        assert "check-human-benefit-report:" in text


def test_markdown_uses_the_fixed_human_decision_structure_without_stronger_claims():
    source = outcome(
        status="completed_with_warnings",
        sections={
            "interventions": ["Stopped the change until owner evidence was supplied."],
            "forcedStops": [
                {
                    "reason": "Owner evidence was missing.",
                    "result": "resolved",
                    "evidence": [{"source": "stop.json", "subject": "stop"}],
                }
            ],
            "limitations": [
                {
                    "title": "Hosted verification was not run",
                    "sourceWarning": "No hosted receipt is available.",
                }
            ],
            "forbiddenClaims": ["Do not claim this is safe."],
            "humanDecisions": ["A release owner must decide whether to proceed."],
        },
    )

    markdown = human.render_human_report(human.generate_human_report(source))

    headings = [
        "Task conclusion",
        "Completed work",
        "Findings",
        "AI Cockpit interventions",
        "Forced stops",
        "Resolved risks",
        "Avoided impact",
        "Unresolved risks",
        "Not-run verification",
        "Forbidden claims",
        "Human decisions",
        "Next safe action",
    ]
    positions = [markdown.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "Stopped the change until owner evidence was supplied." in markdown
    assert "Owner evidence was missing." in markdown
    assert "Hosted verification was not run" in markdown
    assert "A release owner must decide whether to proceed." in markdown
    assert "Evidence-derived report projection" not in markdown
