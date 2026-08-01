#!/usr/bin/env python3
"""Aggregate per-gate timing evidence into JSON and Markdown summaries."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_records(directory: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("schemaVersion") == 1:
            records.append(data)
    return records


def performance_report(
    records: list[dict[str, Any]],
    *,
    profile: str,
    escalations: list[str],
    escalation_reasons: list[str],
    budget_ms: int | None,
) -> dict[str, Any]:
    """Derive local cost facts from existing quality receipts only."""
    cache_records = [record.get("cache", {}) for record in records]
    applicable = [cache for cache in cache_records if cache.get("applicable") is True]
    durations_by_category: dict[str, int] = {}
    gate_counts: dict[str, int] = {}
    for record in records:
        category = str(record.get("category", "unknown"))
        durations_by_category[category] = durations_by_category.get(category, 0) + int(
            record.get("durationMs", 0)
        )
        gate = str(record.get("gate", "unknown"))
        gate_counts[gate] = gate_counts.get(gate, 0) + 1
    slowest = max(records, key=lambda item: int(item.get("durationMs", 0)), default={})
    total = sum(int(record.get("durationMs", 0)) for record in records)
    overage = max(0, total - budget_ms) if budget_ms is not None else 0
    budget_status = (
        "not_configured" if budget_ms is None else "over_budget" if overage else "within_budget"
    )
    return {
        "measurementSource": "local_quality_receipts",
        "profile": profile,
        "verificationEscalations": escalations,
        "escalationReasons": escalation_reasons,
        "totalDurationMs": total,
        "phaseDurationsMs": durations_by_category,
        "preflightDurationMs": durations_by_category.get("preflight", 0),
        "gateDurationMs": total,
        "testDurationMs": durations_by_category.get("tests", 0),
        "archiveDurationMs": durations_by_category.get("archive", 0),
        "cache": {
            "applicable": len(applicable),
            "hits": sum(cache.get("hit") is True for cache in applicable),
            "misses": sum(cache.get("hit") is not True for cache in applicable),
        },
        "repeatedChecks": sorted(gate for gate, count in gate_counts.items() if count > 1),
        "slowestStep": {
            "name": slowest.get("gate"),
            "durationMs": int(slowest.get("durationMs", 0)),
        },
        "budget": {
            "limitMs": budget_ms,
            "status": budget_status,
            "overageMs": overage,
        },
    }


def summarize(
    records: list[dict[str, Any]],
    *,
    profile: str = "unknown",
    escalations: list[str] | None = None,
    escalation_reasons: list[str] | None = None,
    budget_ms: int | None = None,
) -> dict[str, Any]:
    durations = [int(record.get("durationMs", 0)) for record in records]
    starts = [datetime.fromisoformat(record["startedAt"]) for record in records]
    finishes = [datetime.fromisoformat(record["finishedAt"]) for record in records]
    wall = int((max(finishes) - min(starts)).total_seconds() * 1000) if records else 0
    total = sum(durations)
    failed = [record for record in records if record.get("result") not in {"passed", "skipped"}]
    summary = {
        "schemaVersion": 1,
        "scope": "unknown",
        "commitSha": records[0].get("commitSha", "unknown") if records else "unknown",
        "gateCount": len(records),
        "totalWallTimeMs": wall,
        "totalGateTimeMs": total,
        "parallelEfficiency": round(total / wall, 3) if wall else 0.0,
        "slowestGate": max(records, key=lambda item: int(item.get("durationMs", 0))).get("gate")
        if records
        else None,
        "failedGates": [record.get("gate") for record in failed],
        "failureTails": {record.get("gate"): record.get("outputTail", "") for record in failed},
        "skippedGates": [
            record.get("gate") for record in records if record.get("result") == "skipped"
        ],
        "decision": "PASS" if not failed else "FAIL",
        "gates": records,
    }
    summary["performanceReport"] = performance_report(
        records,
        profile=profile,
        escalations=escalations or [],
        escalation_reasons=escalation_reasons or [],
        budget_ms=budget_ms,
    )
    return summary


def markdown(summary: dict[str, Any]) -> str:
    report = summary["performanceReport"]
    lines = [
        "## Quality Gate Summary",
        "",
        f"Scope: {summary['scope']}",
        f"Decision: {summary['decision']}",
        f"Wall time: {summary['totalWallTimeMs']} ms",
        f"Total gate time: {summary['totalGateTimeMs']} ms",
        f"Parallel efficiency: {summary['parallelEfficiency']}x",
        f"Slowest gate: {summary['slowestGate'] or 'n/a'}",
        f"Performance profile: {report['profile']}",
        f"Budget status: {report['budget']['status']}",
        f"Cache hits/misses: {report['cache']['hits']}/{report['cache']['misses']}",
        f"Repeated checks: {', '.join(report['repeatedChecks']) or 'none'}",
        "",
        "| Gate | Category | Duration (ms) | Result | Cache |",
        "|---|---|---:|---|---|",
    ]
    for gate in summary["gates"]:
        cache = gate.get("cache", {})
        lines.append(
            f"| {gate.get('gate')} | {gate.get('category')} | {gate.get('durationMs')} | {gate.get('result')} | {cache.get('hit', False)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="target/quality/timing")
    parser.add_argument("--json-output", default="target/quality/summary.json")
    parser.add_argument("--markdown-output", default="target/quality/summary.md")
    parser.add_argument("--profile", default="unknown")
    parser.add_argument("--escalation", action="append", default=[])
    parser.add_argument("--escalation-reason", action="append", default=[])
    parser.add_argument("--budget-ms", type=int)
    args = parser.parse_args()
    input_dir = Path(args.input)
    records = load_records(input_dir)
    if not records:
        parser.error(f"no quality gate timing evidence found in {input_dir}")
    summary = summarize(
        records,
        profile=args.profile,
        escalations=args.escalation,
        escalation_reasons=args.escalation_reason,
        budget_ms=args.budget_ms,
    )
    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(payload, encoding="utf-8")
    Path(args.markdown_output).write_text(markdown(summary), encoding="utf-8")
    print(f"quality gate summary written: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
