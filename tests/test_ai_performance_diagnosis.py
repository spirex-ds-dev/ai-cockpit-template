from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ai_performance_diagnosis import (
    PerformanceReportError,
    build_report,
    load_events,
    main,
    render_markdown,
)


def event(work_item: str, event_type: str, **kwargs: object) -> dict[str, object]:
    return {"workItemId": work_item, "eventType": event_type, **kwargs}


def test_report_preserves_observed_timing_and_ranks_top_three() -> None:
    report = build_report(
        [
            event(
                "item", "lifecycle_phase_finished", durationMs=30, fields={"phase": "verification"}
            ),
            event("item", "lifecycle_phase_finished", durationMs=10, fields={"phase": "preflight"}),
            event("item", "check_started", checkId="quality"),
            event("item", "check_passed", checkId="quality", durationMs=100),
            event("item", "check_started", checkId="aiScope"),
            event("item", "check_passed", checkId="aiScope", durationMs=20),
            event("item", "retry", fields={"retry": True}),
            event("item", "backtrack"),
        ],
        work_item_id="item",
    )
    assert report["time"]["providerWaitMs"] == "unknown"
    assert report["execution"] == {
        "gateRuns": 2,
        "verificationRuns": 1,
        "retries": 1,
        "backtracks": 1,
        "humanDecisions": 0,
    }
    assert report["topBottlenecks"][0]["name"] == "gate:quality"
    assert report["advisory"] is True
    assert "Top bottlenecks" in render_markdown(report)


def test_load_events_excludes_other_work_items_and_rejects_malformed(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps(event("item", "check_started"))
        + "\n"
        + json.dumps(event("other", "check_started"))
        + "\n",
        encoding="utf-8",
    )
    events, ignored = load_events(path, work_item_id="item")
    assert len(events) == 1 and ignored == 1
    path.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(PerformanceReportError, match="malformed"):
        load_events(path, work_item_id="item")


def test_load_events_rejects_missing_and_non_object_evidence(tmp_path: Path) -> None:
    with pytest.raises(PerformanceReportError, match="cannot read"):
        load_events(tmp_path / "missing.jsonl", work_item_id="item")
    path = tmp_path / "events.jsonl"
    path.write_text("\n[]\n", encoding="utf-8")
    with pytest.raises(PerformanceReportError, match="not an object"):
        load_events(path, work_item_id="item")


def test_report_covers_observed_event_variants_and_empty_markdown() -> None:
    report = build_report(
        [
            event("item", "work_item_finished", durationMs=4),
            event("item", "work_item_finished", durationMs=9),
            event("item", "lifecycle_phase_finished", phase="fallback", durationMs=3),
            event("item", "lifecycle_phase_finished", durationMs=2),
            event("item", "check_failed", checkId="quality-lint", fields={"durationMs": 7}),
            event("item", "check_passed", checkId=42, durationMs=5),
            event("item", "retry"),
            event("item", "backtrack_recorded"),
            event("item", "check_passed", checkId="aiBacktrack", durationMs=1),
            event("item", "human_decision_requested"),
            event("item", "human_decision_recorded"),
        ],
        work_item_id="item",
    )
    assert report["time"]["totalElapsedMs"] == 9
    assert report["time"]["phaseDurationsMs"] == {"fallback": 3, "unknown": 2}
    assert report["execution"]["retries"] == 1
    assert report["execution"]["backtracks"] == 2
    assert report["execution"]["humanDecisions"] == 2
    assert render_markdown(build_report([], work_item_id="empty")).endswith(
        "No measured bottlenecks.\n"
    )


def test_empty_report_has_no_estimates() -> None:
    report = build_report([], work_item_id="empty")
    assert report["time"]["totalElapsedMs"] == "unknown"
    assert report["topBottlenecks"] == []
    assert report["tokenUsage"] == {"input": "unknown", "output": "unknown", "total": "unknown"}


def test_cli_writes_json_and_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        json.dumps(event("item", "work_item_finished", durationMs=12)) + "\n", encoding="utf-8"
    )
    output_json = tmp_path / "out" / "report.json"
    output_md = tmp_path / "out" / "report.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "ai_performance_diagnosis.py",
            "--work-item",
            "item",
            "--events",
            str(events),
            "--json-output",
            str(output_json),
            "--markdown-output",
            str(output_md),
        ],
    )
    assert main() == 0
    assert json.loads(output_json.read_text(encoding="utf-8"))["time"]["totalElapsedMs"] == 12
    assert "# Governance Cost: item" in output_md.read_text(encoding="utf-8")
