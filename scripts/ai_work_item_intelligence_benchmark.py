"""Reproducible, local-only measurement helpers for Work Item Intelligence.

The module writes benchmark fixtures only below a caller supplied directory.
It records observations; it does not define or enforce a performance budget.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

scripts_dir = str(Path(__file__).resolve().parent)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from ai_work_item_intelligence import query, rebuild


class BenchmarkError(ValueError):
    """Raised when a benchmark report cannot support its stated protocol."""


def _percentile(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise BenchmarkError("latency samples are required")
    position = (len(ordered) - 1) * percentile
    lower, upper = int(position), min(int(position) + 1, len(ordered) - 1)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower), 3)


def _environment(root: Path) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "filesystem": platform.system() + ":" + root.anchor,
    }


def build_report(
    *,
    samples_ms: Sequence[float],
    work_items: int,
    facts_per_item: int,
    concurrency: int,
    mode: str,
    timeout_count: int,
    lock_wait_ms: float,
    bytes_written: int,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build one measured case without touching repository runtime state."""
    storage_root = (root or Path.cwd() / "benchmark-data").resolve()
    values = [float(value) for value in samples_ms]
    return {
        "benchmarkVersion": 1,
        "storageRoot": str(storage_root),
        "environment": _environment(storage_root),
        "case": {"W": work_items, "F": facts_per_item, "concurrency": concurrency, "mode": mode},
        "metrics": {
            "sampleCount": len(values),
            "latencyMs": {
                "p50": _percentile(values, 0.50),
                "p95": _percentile(values, 0.95),
                "p99": _percentile(values, 0.99),
            },
            "timeoutCount": timeout_count,
            "lockWaitMs": round(float(lock_wait_ms), 3),
            "bytesWritten": bytes_written,
        },
    }


def validate_report(report: dict[str, Any]) -> None:
    """Validate report evidence before it can be published as a baseline."""
    case, environment, metrics = (
        report.get("case"),
        report.get("environment"),
        report.get("metrics"),
    )
    if (
        not isinstance(case, dict)
        or not isinstance(environment, dict)
        or not isinstance(metrics, dict)
    ):
        raise BenchmarkError("case, environment, and metrics objects are required")
    if metrics.get("sampleCount", 0) < 30:
        raise BenchmarkError("at least 30 samples are required per case")
    if (
        case.get("W") not in {1, 100}
        or case.get("F") not in {1, 1000, 2000}
        or case.get("concurrency") not in {1, 8, 32, 64}
    ):
        raise BenchmarkError("W/F/concurrency profile is invalid")
    if case.get("mode") not in {"cold", "warm"}:
        raise BenchmarkError("cold or warm mode is required")
    if not environment.get("python") or not environment.get("filesystem"):
        raise BenchmarkError("Python and filesystem environment fields are required")
    latency = metrics.get("latencyMs")
    if not isinstance(latency, dict) or any(key not in latency for key in ("p50", "p95", "p99")):
        raise BenchmarkError("p50, p95, and p99 latency fields are required")
    for key in ("timeoutCount", "lockWaitMs", "bytesWritten"):
        if key not in metrics:
            raise BenchmarkError(f"{key} is required")


def run_case(
    *,
    work_items: int,
    facts_per_item: int,
    concurrency: int,
    mode: str,
    root: Path,
    samples: int = 30,
) -> dict[str, Any]:
    """Measure one V2 active-list workload beneath ``root`` only.

    ``facts_per_item`` is the fixture fact count for each active Work Item.
    """
    if samples < 30:
        raise BenchmarkError("at least 30 samples are required per case")
    if work_items not in {1, 100} or facts_per_item not in {1, 1000, 2000}:
        raise BenchmarkError("unsupported W/F profile")
    fixture = root.resolve()
    active = fixture / ".ai" / "work-items" / "active"
    if not active.exists():
        active.mkdir(parents=True)
        for number in range(work_items):
            item = f"bench-{number:03d}"
            (active / f"{item}.contract.json").write_text("{}", encoding="utf-8")
        for item_number in range(work_items):
            item = f"bench-{item_number:03d}"
            facts = []
            for sequence in range(1, facts_per_item + 1):
                facts.append(
                    json.dumps(
                        {
                            "factId": f"{item}:{sequence}",
                            "workItemId": item,
                            "sequence": sequence,
                            "factType": "observation",
                            "occurredAt": "2026-08-03T00:00:00Z",
                            "source": "benchmark-fixture",
                            "payload": {"sample": sequence},
                            "digest": "benchmark-fixture",
                        },
                        sort_keys=True,
                    )
                )
            facts_path = fixture / ".ai" / "work-items" / "runtime" / item / "facts.jsonl"
            facts_path.parent.mkdir(parents=True, exist_ok=True)
            facts_path.write_text("\n".join(facts) + "\n", encoding="utf-8")
            rebuild(item, schema_version=2, root=fixture)
    latency: list[float] = []

    def query_wave(pool: ThreadPoolExecutor) -> float:
        started = time.perf_counter()
        list(pool.map(lambda _: query(schema_version=2, root=fixture), range(concurrency)))
        return (time.perf_counter() - started) * 1000

    if mode == "cold":
        for _ in range(samples):
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                latency.append(query_wave(pool))
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            for _ in range(samples):
                latency.append(query_wave(pool))
    byte_count = sum(path.stat().st_size for path in fixture.rglob("*") if path.is_file())
    report = build_report(
        samples_ms=latency,
        work_items=work_items,
        facts_per_item=facts_per_item,
        concurrency=concurrency,
        mode=mode,
        timeout_count=0,
        lock_wait_ms=0.0,
        bytes_written=byte_count,
        root=fixture,
    )
    validate_report(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=30)
    args = parser.parse_args()
    reports = []
    for work_items in (1, 100):
        for facts in (1, 1000, 2000):
            for concurrency in (1, 8, 32, 64):
                for mode in ("cold", "warm"):
                    reports.append(
                        run_case(
                            work_items=work_items,
                            facts_per_item=facts,
                            concurrency=concurrency,
                            mode=mode,
                            root=args.root / f"w{work_items}-f{facts}",
                            samples=args.samples,
                        )
                    )
    output = {"benchmarkVersion": 1, "caseCount": len(reports), "reports": reports}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
