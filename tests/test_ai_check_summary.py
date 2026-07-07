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
