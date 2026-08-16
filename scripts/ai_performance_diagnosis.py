#!/usr/bin/env python3
"""Derive evidence-only Work Item governance cost and bottleneck reports."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class PerformanceReportError(ValueError):
    """Raised when performance evidence cannot be interpreted safely."""


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None


def load_events(path: Path, *, work_item_id: str) -> tuple[list[dict[str, Any]], int]:
    """Load valid events for one Work Item; malformed evidence fails closed."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PerformanceReportError(f"cannot read observability log: {exc}") from exc
    events: list[dict[str, Any]] = []
    ignored = 0
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PerformanceReportError(f"malformed observability JSON at line {number}") from exc
        if not isinstance(value, dict):
            raise PerformanceReportError(f"observability event at line {number} is not an object")
        event_item = value.get("workItemId")
        if event_item != work_item_id:
            ignored += 1
            continue
        events.append(value)
    return events, ignored


def _event_duration(event: dict[str, Any]) -> int | None:
    direct = _int(event.get("durationMs"))
    if direct is not None:
        return direct
    fields = event.get("fields")
    return _int(fields.get("durationMs")) if isinstance(fields, dict) else None


def build_report(
    events: list[dict[str, Any]],
    *,
    work_item_id: str,
    ignored_cross_work_item_events: int = 0,
    source_path: str | None = None,
    source_digest: str | None = None,
) -> dict[str, Any]:
    """Build deterministic metrics without estimating unavailable categories."""
    phases: dict[str, int] = defaultdict(int)
    gates: dict[str, int] = defaultdict(int)
    gate_runs = 0
    verification_runs = 0
    retries = 0
    backtracks = 0
    human_decisions = 0
    total_elapsed: int | None = None

    for event in events:
        event_type = event.get("eventType")
        duration = _event_duration(event)
        raw_fields = event.get("fields")
        fields: dict[str, Any] = raw_fields if isinstance(raw_fields, dict) else {}
        if event_type == "work_item_finished" and duration is not None:
            total_elapsed = duration if total_elapsed is None else max(total_elapsed, duration)
        if event_type == "lifecycle_phase_finished":
            phase = fields.get("phase") or event.get("phase") or "unknown"
            if isinstance(phase, str) and duration is not None:
                phases[phase] += duration
        if event_type in {"check_started", "check_passed", "check_failed"}:
            check = event.get("checkId")
            if isinstance(check, str):
                gate_runs += event_type == "check_started"
                if duration is not None and event_type != "check_started":
                    gates[check] += duration
                if check == "quality" or check.startswith("quality"):
                    verification_runs += event_type == "check_started"
        if event_type in {"retry", "work_item_retry"} or fields.get("retry") is True:
            retries += 1
        if (
            event_type in {"backtrack", "backtrack_recorded"}
            or event.get("checkId") == "aiBacktrack"
        ):
            backtracks += 1
        if event_type in {"human_decision_requested", "human_decision_recorded"}:
            human_decisions += 1

    candidates: list[dict[str, Any]] = [
        {"name": f"phase:{name}", "durationMs": duration, "source": "lifecycle_phase_finished"}
        for name, duration in phases.items()
    ] + [
        {"name": f"gate:{name}", "durationMs": duration, "source": "check_result"}
        for name, duration in gates.items()
    ]
    candidates.sort(key=lambda item: (-int(item["durationMs"]), str(item["name"])))
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
        "time": {
            "totalElapsedMs": total_elapsed if total_elapsed is not None else "unknown",
            "phaseDurationsMs": dict(sorted(phases.items())),
            "providerWaitMs": "unknown",
            "humanWaitMs": "unknown",
            "recoveryRetryMs": "unknown",
        },
        "execution": {
            "gateRuns": gate_runs,
            "verificationRuns": verification_runs,
            "retries": retries,
            "backtracks": backtracks,
            "humanDecisions": human_decisions,
        },
        "tokenUsage": {"input": "unknown", "output": "unknown", "total": "unknown"},
        "topBottlenecks": candidates[:3],
        "advisory": True,
        "decisionImpact": "none",
    }
    report["reportDigest"] = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    return report


def render_markdown(report: dict[str, Any]) -> str:
    time_data = report["time"]
    execution = report["execution"]
    lines = [
        f"# Governance Cost: {report['workItemId']}",
        "",
        "Evidence-only report; unavailable provider and human timings remain `unknown`.",
        "",
        f"- Total elapsed: `{time_data['totalElapsedMs']}` ms",
        f"- Gate runs: `{execution['gateRuns']}`",
        f"- Verification runs: `{execution['verificationRuns']}`",
        f"- Retries / backtracks: `{execution['retries']}` / `{execution['backtracks']}`",
        f"- Human decisions: `{execution['humanDecisions']}`",
        "",
        "## Top bottlenecks",
        "",
    ]
    if report["topBottlenecks"]:
        lines.extend(
            f"{index}. `{item['name']}` — `{item['durationMs']}` ms"
            for index, item in enumerate(report["topBottlenecks"], 1)
        )
    else:
        lines.append("No measured bottlenecks.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--events", type=Path, default=Path("target/ai_observability.jsonl"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        events, ignored = load_events(args.events, work_item_id=args.work_item)
        digest = "sha256:" + hashlib.sha256(args.events.read_bytes()).hexdigest()
        report = build_report(
            events,
            work_item_id=args.work_item,
            ignored_cross_work_item_events=ignored,
            source_path=args.events.as_posix(),
            source_digest=digest,
        )
    except (OSError, PerformanceReportError) as exc:
        parser.error(str(exc))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(f"performance diagnosis written: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
