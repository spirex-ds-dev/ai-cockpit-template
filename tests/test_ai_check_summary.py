import json

import ai_check_summary
from ai_common import PROJECT_ROOT


ARCHIVE_SUMMARY = PROJECT_ROOT / ".ai" / "work-items" / "archive" / "2026" / "realign_ai_cockpit_v2.summary.json"


def test_intent_alignment_validator_accepts_empty_and_partial_payloads():
    assert ai_check_summary.validate_intent_alignment({"intentAlignment": {}}) == []
    assert ai_check_summary.validate_intent_alignment({"intentAlignment": None}) == []
    assert ai_check_summary.validate_intent_alignment({"intentAlignment": {"problemResolved": True}}) == []
    assert ai_check_summary.validate_intent_alignment(
        {"intentAlignment": {"problemResolutionEvidence": "legacy evidence text"}}
    ) == []
    assert ai_check_summary.validate_intent_alignment(
        {"intentAlignment": {"constraintsRespectEvidence": "legacy evidence text"}}
    ) == []


def test_intent_alignment_validator_accepts_legacy_archive_payload():
    archive_summary = json.loads(ARCHIVE_SUMMARY.read_text(encoding="utf-8"))
    assert ai_check_summary.validate_intent_alignment(
        {"intentAlignment": archive_summary["intentAlignment"]}
    ) == []


def test_intent_alignment_validator_rejects_unknown_keys():
    issues = ai_check_summary.validate_intent_alignment(
        {"intentAlignment": {"problemResolved": True, "unknownKey": False}}
    )
    assert "intentAlignment.unknownKey is not a recognized field" in issues


def test_scenario_coverage_validator_accepts_valid_payload():
    summary = {
        "workItemId": "task",
        "contractPath": ".ai/work-items/active/task.contract.json",
        "changedFiles": [{"path": "src/app.py", "reason": "fixture"}],
        "sourcesUsed": ["spec"],
        "scenarioCoverage": [
            {
                "scenario": "example verified scenario",
                "required": True,
                "status": "verified",
                "evidence": ["make example-check"],
            },
            {
                "scenario": "example unverified scenario",
                "required": True,
                "status": "unverified",
                "evidence": [],
                "reason": "Waiting on an external run.",
            },
            {
                "scenario": "example not applicable scenario",
                "required": False,
                "status": "not_applicable",
                "evidence": [],
                "reason": "Legacy path not touched.",
            },
        ],
        "verification": [{"check": "quality", "result": "not_run"}],
        "unknownsRemaining": [],
        "risk": {"level": "low", "detail": "fixture"},
        "generatedFiles": [],
        "destructiveChanges": [],
        "observedIssues": [],
        "reviewReadiness": {"status": "ready", "reason": "fixture", "expectedReviewFocus": []},
        "boundaryChecks": {
            "runtimeEntrypoints": "not_applicable",
            "userVisibleOutput": "not_applicable",
            "persistence": "not_applicable",
            "localization": "not_applicable",
            "generatedArtifacts": "not_applicable",
            "makeEntrypoints": "not_applicable",
        },
        "knownGaps": [],
        "overclaimPrevention": "fixture",
    }

    assert ai_check_summary.validate_summary(summary, {"workItemId": "task", "contractVersion": 2}) == []


def test_scenario_coverage_validator_rejects_invalid_required_entries():
    summary = {
        "workItemId": "task",
        "contractPath": ".ai/work-items/active/task.contract.json",
        "changedFiles": [{"path": "src/app.py", "reason": "fixture"}],
        "sourcesUsed": ["spec"],
        "scenarioCoverage": [
            {
                "scenario": "example verified scenario",
                "required": True,
                "status": "verified",
                "evidence": [],
            },
            {
                "scenario": "example not applicable scenario",
                "required": True,
                "status": "not_applicable",
                "evidence": [],
            },
        ],
        "verification": [{"check": "quality", "result": "not_run"}],
        "unknownsRemaining": [],
        "risk": {"level": "low", "detail": "fixture"},
        "generatedFiles": [],
        "destructiveChanges": [],
        "observedIssues": [],
        "reviewReadiness": {"status": "ready", "reason": "fixture", "expectedReviewFocus": []},
        "boundaryChecks": {
            "runtimeEntrypoints": "not_applicable",
            "userVisibleOutput": "not_applicable",
            "persistence": "not_applicable",
            "localization": "not_applicable",
            "generatedArtifacts": "not_applicable",
            "makeEntrypoints": "not_applicable",
        },
        "knownGaps": [],
        "overclaimPrevention": "fixture",
    }

    issues = ai_check_summary.validate_summary(summary, {"workItemId": "task", "contractVersion": 2})
    assert "scenarioCoverage[0].evidence must contain at least one item when status is verified" in issues
    assert "scenarioCoverage[1].reason is required when status is not_applicable" in issues
