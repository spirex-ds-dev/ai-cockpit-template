from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ai_governance_cost import (
    PerformanceReportError,
    build_report,
    load_events,
    main,
    render_markdown,
)


def event(work_item: str, event_type: str, **kwargs: object) -> dict[str, object]:
    return {"workItemId": work_item, "eventType": event_type, **kwargs}


def test_complete_report_records_observed_cost_categories() -> None:
    report = build_report(
        [
            event("item", "lifecycle_phase_finished", durationMs=12, fields={"phase": "preflight"}),
            event("item", "check_started", checkId="quality"),
            event("item", "check_passed", checkId="quality", durationMs=30),
            event("item", "retry"),
            event("item", "backtrack"),
            event("item", "human_decision_recorded"),
        ],
        work_item_id="item",
        ignored_cross_work_item_events=2,
        source_path="events.jsonl",
        source_digest="sha256:" + "a" * 64,
    )
    assert report["observed"] == {
        "localComputeMs": 12,
        "gateDurationMs": 30,
        "phaseDurationsMs": {"preflight": 12},
        "gateRuns": 1,
        "verificationRuns": 1,
        "retries": 1,
        "backtracks": 1,
        "humanDecisions": 1,
    }
    assert report["source"]["ignoredCrossWorkItemEvents"] == 2
    assert report["advisory"] is True
    assert report["decisionImpact"] == "none"
    assert report["reportDigest"].startswith("sha256:")
    assert "Local compute" in render_markdown(report)


def test_empty_and_partial_evidence_stays_unknown() -> None:
    empty = build_report([], work_item_id="empty")
    assert empty["observed"]["localComputeMs"] == "unknown"
    assert empty["observed"]["gateDurationMs"] == "unknown"
    assert empty["unknown"]["tokenUsage"] == {
        "input": "unknown",
        "output": "unknown",
        "total": "unknown",
    }
    fields_only = build_report(
        [
            event(
                "item",
                "lifecycle_phase_finished",
                fields={"phase": "verification", "durationMs": 4},
            )
        ],
        work_item_id="item",
    )
    assert fields_only["observed"]["phaseDurationsMs"] == {"verification": 4}
    assert build_report([], work_item_id="empty")["reportDigest"] == empty["reportDigest"]


def test_loader_rejects_malformed_and_excludes_cross_item(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n"
        + json.dumps(event("item", "check_started"))
        + "\n"
        + json.dumps(event("other", "check_started"))
        + "\n",
        encoding="utf-8",
    )
    events, ignored = load_events(path, work_item_id="item")
    assert len(events) == 1 and ignored == 1
    path.write_text("bad-json\n", encoding="utf-8")
    with pytest.raises(PerformanceReportError, match="malformed"):
        load_events(path, work_item_id="item")


def test_cli_writes_report_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        json.dumps(event("item", "check_started", checkId="aiScope")) + "\n", encoding="utf-8"
    )
    output_json = tmp_path / "nested" / "report.json"
    output_md = tmp_path / "nested" / "report.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "ai_governance_cost.py",
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
    saved = json.loads(output_json.read_text(encoding="utf-8"))
    assert saved["observed"]["gateRuns"] == 1
    assert output_md.exists()


def test_lifecycle_report_separates_explicit_waits_and_ranks_bottlenecks() -> None:
    report = build_report(
        [
            event("item", "work_item_started"),
            event("item", "lifecycle_phase_finished", durationMs=100, fields={"phase": "verify"}),
            event("item", "check_started", checkId="quality"),
            event("item", "check_passed", checkId="quality", durationMs=80),
            event("item", "wait_finished", fields={"category": "ci", "durationMs": 300}),
            event("item", "wait_finished", fields={"category": "human", "durationMs": 200}),
            event("item", "retry", fields={"durationMs": 50}),
            event("item", "work_item_finished", result="passed", durationMs=1000),
        ],
        work_item_id="item",
    )

    assert report["time"] == {
        "totalElapsedMs": 1000,
        "agentActiveMs": 100,
        "verificationMs": 80,
        "ciWaitMs": 300,
        "humanWaitMs": 200,
        "recoveryRetryMs": 50,
        "phaseDurationsMs": {"verify": 100},
    }
    assert report["topBottlenecks"][0] == {
        "name": "wait:ci",
        "durationMs": 300,
        "source": "explicit_wait",
    }
    assert report["decisionImpact"] == "none"


def test_lifecycle_report_keeps_unavailable_categories_unknown() -> None:
    report = build_report(
        [event("item", "work_item_finished", result="passed", durationMs=7)],
        work_item_id="item",
    )

    assert report["time"] == {
        "totalElapsedMs": 7,
        "agentActiveMs": "unknown",
        "verificationMs": "unknown",
        "ciWaitMs": "unknown",
        "humanWaitMs": "unknown",
        "recoveryRetryMs": "unknown",
        "phaseDurationsMs": {},
    }
    assert report["topBottlenecks"] == []
