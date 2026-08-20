from __future__ import annotations

import json
import sys

import pytest
from ai_knowledge_projection_benchmark import (
    main,
    route_changed_path,
    run_benchmark,
    synthetic_dependency_index,
)


def test_unrelated_refresh_routes_without_visiting_synthetic_records() -> None:
    result = run_benchmark([1000, 10000])

    assert [item["recordCount"] for item in result["results"]] == [1000, 10000]
    assert all(item["affectedCount"] == 0 for item in result["results"])
    assert all(item["recordsVisited"] == 0 for item in result["results"])
    assert all(item["dependencyLookups"] == 1 for item in result["results"])


def test_changed_refresh_reports_reverse_map_matches() -> None:
    payload = synthetic_dependency_index(2)

    result = route_changed_path(payload, "src/synthetic/synthetic-00001.py")

    assert result["affectedCount"] == 1
    assert result["recordsVisited"] == 0
    assert result["dependencyLookups"] == 1


def test_main_writes_requested_benchmark_output(tmp_path, monkeypatch, capsys) -> None:
    output = tmp_path / "benchmark.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_knowledge_projection_benchmark.py", "--records", "2", "--output", str(output)],
    )

    assert main() == 0
    assert json.loads(output.read_text(encoding="utf-8"))["results"][0]["recordCount"] == 2
    assert json.loads(capsys.readouterr().out)["schemaVersion"] == 1


def test_main_rejects_non_positive_record_counts(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_knowledge_projection_benchmark.py", "--records", "0"],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
