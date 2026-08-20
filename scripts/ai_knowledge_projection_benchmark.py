#!/usr/bin/env python3
"""Measure dependency-index routing without rebuilding synthetic Records."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


def synthetic_dependency_index(record_count: int) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    by_path: dict[str, list[str]] = {}
    for number in range(record_count):
        work_item_id = f"synthetic-{number:05d}"
        path = f"src/synthetic/{work_item_id}.py"
        records[work_item_id] = {
            "recordPath": f".ai/knowledge/work-items/{work_item_id}.json",
            "dependencies": [path],
        }
        by_path[path] = [work_item_id]
    return {"schemaVersion": 1, "records": records, "byPath": by_path}


def route_changed_path(payload: dict[str, Any], changed_path: str) -> dict[str, Any]:
    """Route one changed path using one reverse-map lookup."""
    started = time.perf_counter()
    affected = payload["byPath"].get(changed_path, [])
    return {
        "affectedCount": len(affected),
        "recordsVisited": 0,
        "dependencyLookups": 1,
        "elapsedMilliseconds": round((time.perf_counter() - started) * 1000, 4),
    }


def run_benchmark(record_counts: list[int]) -> dict[str, Any]:
    results = []
    for record_count in record_counts:
        payload = synthetic_dependency_index(record_count)
        measurement = route_changed_path(payload, "src/synthetic/not-routed.py")
        results.append({"recordCount": record_count, **measurement})
    return {
        "schemaVersion": 1,
        "changedPath": "src/synthetic/not-routed.py",
        "results": results,
        "invariant": "unrelated refresh performs one reverse-map lookup and visits zero Records",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="+", type=int, default=[1000, 10000])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("target/knowledge-projection-benchmark.json"),
    )
    args = parser.parse_args()
    if any(value <= 0 for value in args.records):
        parser.error("--records values must be positive")
    result = run_benchmark(args.records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
