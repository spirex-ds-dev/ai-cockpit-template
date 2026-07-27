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


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    durations = [int(record.get("durationMs", 0)) for record in records]
    starts = [
        datetime.fromisoformat(record["startedAt"].replace("Z", "+00:00")) for record in records
    ]
    finishes = [
        datetime.fromisoformat(record["finishedAt"].replace("Z", "+00:00")) for record in records
    ]
    wall = int((max(finishes) - min(starts)).total_seconds() * 1000) if records else 0
    total = sum(durations)
    failed = [record for record in records if record.get("result") not in {"passed", "skipped"}]
    return {
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


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "## Quality Gate Summary",
        "",
        f"Scope: {summary['scope']}",
        f"Decision: {summary['decision']}",
        f"Wall time: {summary['totalWallTimeMs']} ms",
        f"Total gate time: {summary['totalGateTimeMs']} ms",
        f"Parallel efficiency: {summary['parallelEfficiency']}x",
        f"Slowest gate: {summary['slowestGate'] or 'n/a'}",
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
    args = parser.parse_args()
    input_dir = Path(args.input)
    records = load_records(input_dir)
    if not records:
        parser.error(f"no quality gate timing evidence found in {input_dir}")
    summary = summarize(records)
    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(payload, encoding="utf-8")
    Path(args.markdown_output).write_text(markdown(summary), encoding="utf-8")
    print(f"quality gate summary written: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
