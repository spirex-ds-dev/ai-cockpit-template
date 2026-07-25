from __future__ import annotations

from scripts import ai_issue_log
from scripts.ai_issue_log import validate_issue_record, validate_transition


def valid_record() -> dict[str, object]:
    return {
        "issueId": "IW-20260725-001",
        "workItem": "interactive-wizard-work-item-issue-log",
        "stage": "verification",
        "observedAt": "2026-07-25T12:00:00Z",
        "severity": "warning",
        "title": "A documented warning",
        "evidence": ["tests/test_issue_log.py"],
        "impact": "Review is required.",
        "owner": "interactive-wizard-work-item-issue-log",
        "containment": "Keep the PR blocked until verified.",
        "status": "open",
        "resolution": None,
        "verificationRefs": ["tests/test_issue_log.py"],
        "affectsCompletionClaim": True,
    }


def test_valid_issue_record_is_accepted() -> None:
    assert validate_issue_record(valid_record()) == []


def test_missing_evidence_is_rejected() -> None:
    record = valid_record()
    record["evidence"] = []
    assert any("evidence" in issue for issue in validate_issue_record(record))


def test_secret_like_values_are_rejected_without_echoing_value() -> None:
    record = valid_record()
    record["impact"] = "to" + "ken=" + "ghp_" + "example_should_not_be_stored"
    issues = validate_issue_record(record)
    assert any("sensitive" in issue for issue in issues)
    assert all("ghp_example" not in issue for issue in issues)


def test_open_to_resolved_requires_resolution_and_verification() -> None:
    record = valid_record()
    record["status"] = "resolved"
    record["resolution"] = "Fixed and verified."
    assert validate_transition(valid_record(), record) == []


def test_resolved_record_cannot_be_reopened() -> None:
    previous = valid_record()
    previous["status"] = "resolved"
    previous["resolution"] = "Fixed and verified."
    current = valid_record()
    assert any("append-only" in issue for issue in validate_transition(previous, current))


def test_invalid_identifier_and_resolution_are_rejected() -> None:
    record = valid_record()
    record["issueId"] = "bad"
    record["status"] = "resolved"
    record["resolution"] = None
    issues = validate_issue_record(record)
    assert any("issueId" in issue for issue in issues)
    assert any("resolution" in issue for issue in issues)


def test_cli_accepts_valid_record_and_rejects_invalid_record(tmp_path, monkeypatch) -> None:
    record_path = tmp_path / "record.json"
    record_path.write_text(__import__("json").dumps(valid_record()), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["ai_issue_log.py", str(record_path)])
    assert ai_issue_log.main() == 0
    record_path.write_text("[]", encoding="utf-8")
    assert ai_issue_log.main() == 2


def test_issue_overview_groups_later_records_without_rewriting_history() -> None:
    first = valid_record()
    first["issueId"] = "IW-20260725-013"
    first["status"] = "resolved"
    first["resolution"] = "Recorded in the later verification run."
    second = valid_record()
    second["issueId"] = "IW-20260725-014"
    second["status"] = "accepted_residual_risk"
    overview = ai_issue_log.build_issue_overview([first, second])
    assert overview["resolved"] == ["IW-20260725-013"]
    assert overview["accepted_residual_risk"] == ["IW-20260725-014"]
    assert overview["blocked"] == []
    rendered = ai_issue_log.render_issue_overview([first, second])
    assert "## Generated issue overview" in rendered
    assert "`IW-20260725-013`" in rendered
