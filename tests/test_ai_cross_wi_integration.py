from __future__ import annotations

import json
from pathlib import Path

import pytest
from ai_cross_wi_integration import (
    OUTCOME_SECTIONS,
    REQUIRED_WORK_ITEMS,
    build_report,
    render_markdown,
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _fixture(root: Path, *, broken_task: str | None = None) -> None:
    archive = root / ".ai" / "work-items" / "archive" / "2026"
    for task in REQUIRED_WORK_ITEMS:
        status = "completed_with_warnings" if task != REQUIRED_WORK_ITEMS[1] else "completed"
        color = "yellow" if status.endswith("warnings") else "green"
        identity = "wrong-task" if task == broken_task else task
        prefix = archive / task
        contract = {"contractVersion": 2, "workItemId": identity}
        summary = {
            "summaryVersion": 2,
            "workItemId": identity,
            "knownGaps": [] if status == "completed" else ["explicit limitation"],
            "changedFiles": [],
        }
        outcome = {
            "format": "ai-cockpit-task-outcome",
            "schemaVersion": 1,
            "workItemId": identity,
            "status": status,
            "humanStatusColor": color,
            "sections": {"warnings": [] if status == "completed" else ["explicit limitation"]},
        }
        contract_path = prefix.with_suffix(".contract.json")
        summary_path = prefix.with_suffix(".summary.json")
        outcome_path = prefix.with_suffix(".outcome.json")
        outcome_markdown = prefix.with_suffix(".outcome.md")
        _write_json(contract_path, contract)
        _write_json(summary_path, summary)
        _write_json(outcome_path, outcome)
        outcome_markdown.parent.mkdir(parents=True, exist_ok=True)
        outcome_markdown.write_text("# Outcome\n", encoding="utf-8")
        manifest = {
            "format": "ai-cockpit-archive-manifest",
            "manifestVersion": 1,
            "workItemId": identity,
            "archiveSequence": 1,
            "contractPath": contract_path.relative_to(root).as_posix(),
            "summaryPath": summary_path.relative_to(root).as_posix(),
            "contractSha256": "placeholder",
            "summarySha256": "placeholder",
            "outcomeArtifacts": [],
        }
        _write_json(prefix.with_suffix(".archive-manifest.json"), manifest)


def test_current_archives_are_reconciled_with_explicit_outcome_and_performance_boundaries():
    root = Path(__file__).resolve().parents[1]

    report = build_report(root)

    assert report["overallStatus"] == "yellow"
    assert report["decisionImpact"] == "none"
    assert [item["taskId"] for item in report["workItems"]] == sorted(REQUIRED_WORK_ITEMS)
    outcome = report["outcomeDelivery"]
    assert outcome["directHandoffImplementation"] == "verified"
    assert outcome["directHandoffTest"] == "verified"
    assert outcome["conversationUiReceipt"] == "not_observable"
    assert outcome["agentHandoffProtocol"] == "required_for_every_agent_and_subagent"
    assert outcome["requiredOutcomeFields"] == list(OUTCOME_SECTIONS)
    assert report["performance"]["runtimeImprovement"] == "unverified"
    assert report["performance"]["comparableBaseline"] == "not_provided"
    assert report["performance"]["decisionImpact"] == "none"
    assert all(item["evidenceState"] == "valid" for item in report["workItems"])
    assert all(
        set(OUTCOME_SECTIONS) == set(item["outcomeSections"]) for item in report["workItems"]
    )


def test_report_is_deterministic_for_unchanged_sources():
    root = Path(__file__).resolve().parents[1]

    assert build_report(root) == build_report(root)


def test_missing_or_mismatched_archive_is_red_and_fail_closed(tmp_path: Path):
    _fixture(tmp_path, broken_task=REQUIRED_WORK_ITEMS[-1])

    report = build_report(tmp_path)

    assert report["overallStatus"] == "red"
    broken = next(item for item in report["workItems"] if item["taskId"] == REQUIRED_WORK_ITEMS[-1])
    assert broken["evidenceState"] == "invalid"
    assert any("identity" in finding.lower() for finding in broken["findings"])


def test_markdown_preserves_color_and_no_overclaim_language():
    root = Path(__file__).resolve().parents[1]

    markdown = render_markdown(build_report(root))

    assert "🟡" in markdown
    assert "conversation UI receipt is not observable" in markdown
    assert "runtime performance improvement is unverified" in markdown
    assert "decisionImpact=none" in markdown


@pytest.mark.parametrize("task", REQUIRED_WORK_ITEMS)
def test_required_work_item_list_is_unique(task: str):
    assert REQUIRED_WORK_ITEMS.count(task) == 1
