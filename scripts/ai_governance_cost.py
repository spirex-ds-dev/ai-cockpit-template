#!/usr/bin/env python3
"""Build advisory governance-cost metrics from Work Item-scoped evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_performance_diagnosis import PerformanceReportError, load_events


def _duration(event: dict[str, Any]) -> int | None:
    value = event.get("durationMs")
    if isinstance(value, int) and value >= 0:
        return value
    fields = event.get("fields")
    nested = fields.get("durationMs") if isinstance(fields, dict) else None
    return nested if isinstance(nested, int) and nested >= 0 else None


def build_report(
    events: list[dict[str, Any]],
    *,
    work_item_id: str,
    ignored_cross_work_item_events: int = 0,
    source_path: str | None = None,
    source_digest: str | None = None,
) -> dict[str, Any]:
    """Return observed counts and durations without estimating unavailable values."""
    phase_durations: dict[str, int] = defaultdict(int)
    local_compute = 0
    gate_duration = 0
    gate_runs = 0
    verification_runs = 0
    retries = 0
    backtracks = 0
    human_decisions = 0
    for event in events:
        event_type = event.get("eventType")
        raw_fields = event.get("fields")
        fields: dict[str, Any] = raw_fields if isinstance(raw_fields, dict) else {}
        duration = _duration(event)
        if event_type == "lifecycle_phase_finished" and duration is not None:
            phase = fields.get("phase") or event.get("phase") or "unknown"
            if isinstance(phase, str):
                phase_durations[phase] += duration
                local_compute += duration
        check_id = event.get("checkId")
        if event_type == "check_started" and isinstance(check_id, str):
            gate_runs += 1
            if check_id == "quality" or check_id.startswith("quality"):
                verification_runs += 1
        if event_type in {"check_passed", "check_failed"} and duration is not None:
            gate_duration += duration
        if event_type in {"retry", "work_item_retry"} or fields.get("retry") is True:
            retries += 1
        if event_type in {"backtrack", "backtrack_recorded"} or check_id == "aiBacktrack":
            backtracks += 1
        if event_type in {"human_decision_requested", "human_decision_recorded"}:
            human_decisions += 1

    observed = {
        "localComputeMs": local_compute if events and local_compute else "unknown",
        "gateDurationMs": gate_duration if gate_duration else "unknown",
        "phaseDurationsMs": dict(sorted(phase_durations.items())),
        "gateRuns": gate_runs,
        "verificationRuns": verification_runs,
        "retries": retries,
        "backtracks": backtracks,
        "humanDecisions": human_decisions,
    }
    report: dict[str, Any] = {
        "schemaVersion": 1,
        "workItemId": work_item_id,
        "generatedAt": datetime.now(UTC).isoformat(),
        "source": {
            "kind": "local_observability",
            "path": source_path,
            "sha256": source_digest,
            "ignoredCrossWorkItemEvents": ignored_cross_work_item_events,
        },
        "observed": observed,
        "unknown": {
            "providerWaitMs": "unknown",
            "humanWaitMs": "unknown",
            "recoveryRetryMs": "unknown",
            "tokenUsage": {"input": "unknown", "output": "unknown", "total": "unknown"},
        },
        "advisory": True,
        "decisionImpact": "none",
    }
    digest_source = {key: value for key, value in report.items() if key != "generatedAt"}
    digest_payload = json.dumps(
        digest_source, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    report["reportDigest"] = "sha256:" + hashlib.sha256(digest_payload.encode()).hexdigest()
    return report


def render_markdown(report: dict[str, Any]) -> str:
    observed = report["observed"]
    unknown = report["unknown"]
    lines = [
        f"# Governance cost: {report['workItemId']}",
        "",
        "Advisory, evidence-only metrics. Unknown values are not estimated.",
        "",
        f"- Local compute: `{observed['localComputeMs']}` ms",
        f"- Gate duration: `{observed['gateDurationMs']}` ms",
        f"- Gate / verification runs: `{observed['gateRuns']}` / `{observed['verificationRuns']}`",
        f"- Retries / backtracks: `{observed['retries']}` / `{observed['backtracks']}`",
        f"- Human decisions: `{observed['humanDecisions']}`",
        f"- Provider wait / human wait: `{unknown['providerWaitMs']}` / `{unknown['humanWaitMs']}`",
        "",
        f"Report digest: `{report['reportDigest']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--events", type=Path, default=Path("target/ai_observability.jsonl"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        events, ignored = load_events(args.events, work_item_id=args.work_item)
        source_digest = "sha256:" + hashlib.sha256(args.events.read_bytes()).hexdigest()
        report = build_report(
            events,
            work_item_id=args.work_item,
            ignored_cross_work_item_events=ignored,
            source_path=args.events.as_posix(),
            source_digest=source_digest,
        )
    except (OSError, PerformanceReportError) as exc:
        parser.error(str(exc))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(f"governance cost report written: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
