from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ai_work_item_intelligence_benchmark import (
    BenchmarkError,
    build_report,
    run_case,
    validate_report,
)


def test_report_requires_complete_profile_and_thirty_samples() -> None:
    report = build_report(
        samples_ms=[1.0] * 29,
        work_items=1,
        facts_per_item=1,
        concurrency=1,
        mode="warm",
        timeout_count=0,
        lock_wait_ms=0.0,
        bytes_written=12,
    )

    with pytest.raises(BenchmarkError, match="at least 30"):
        validate_report(report)


def test_report_contains_required_distribution_and_environment_fields() -> None:
    report = build_report(
        samples_ms=[float(number) for number in range(1, 31)],
        work_items=1,
        facts_per_item=1,
        concurrency=1,
        mode="cold",
        timeout_count=0,
        lock_wait_ms=0.0,
        bytes_written=12,
    )

    assert report["environment"]["python"]
    assert report["environment"]["filesystem"]
    assert report["case"]["W"] == 1
    assert report["case"]["F"] == 1
    assert report["case"]["concurrency"] == 1
    assert report["case"]["mode"] == "cold"
    assert report["metrics"]["latencyMs"] == {"p50": 15.5, "p95": 28.55, "p99": 29.71}
    assert report["metrics"]["timeoutCount"] == 0
    assert report["metrics"]["lockWaitMs"] == 0.0
    assert report["metrics"]["bytesWritten"] == 12
    validate_report(report)


def test_report_rejects_an_undeclared_fact_profile() -> None:
    report = build_report(
        samples_ms=[1.0] * 30,
        work_items=1,
        facts_per_item=2,
        concurrency=1,
        mode="warm",
        timeout_count=0,
        lock_wait_ms=0.0,
        bytes_written=12,
    )

    with pytest.raises(BenchmarkError, match="W/F/concurrency"):
        validate_report(report)


def test_benchmark_uses_only_the_given_temporary_root(tmp_path: Path) -> None:
    repository_runtime = tmp_path / ".ai" / "work-items" / "runtime"
    report = build_report(
        samples_ms=[1.0] * 30,
        work_items=1,
        facts_per_item=1,
        concurrency=1,
        mode="warm",
        timeout_count=0,
        lock_wait_ms=0.0,
        bytes_written=12,
        root=tmp_path / "benchmark-data",
    )

    assert report["storageRoot"] == str(tmp_path / "benchmark-data")
    assert not repository_runtime.exists()


def test_run_case_queries_v2_from_an_isolated_fixture(tmp_path: Path) -> None:
    report = run_case(
        work_items=1,
        facts_per_item=1,
        concurrency=1,
        mode="warm",
        root=tmp_path / "fixture",
    )

    assert report["metrics"]["sampleCount"] == 30
    assert (tmp_path / "fixture" / ".ai" / "work-items" / "runtime").exists()
    assert not (tmp_path / ".ai" / "work-items" / "runtime").exists()
    fact = json.loads(
        (tmp_path / "fixture/.ai/work-items/runtime/bench-000/facts.jsonl").read_text(
            encoding="utf-8"
        )
    )
    assert fact["digest"].startswith("sha256:")
