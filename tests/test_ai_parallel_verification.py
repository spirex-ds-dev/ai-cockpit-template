from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts.ai_parallel_verification import ParallelPlanError, execute_plan, main, plan_batches


def command(code: str) -> list[str]:
    return [sys.executable, "-c", code]


def test_independent_jobs_run_and_retain_results(tmp_path: Path) -> None:
    plan = {
        "schemaVersion": 1,
        "maxWorkers": 2,
        "jobs": [
            {"id": "a", "command": command("print('a')"), "scope": ["a.py"]},
            {"id": "b", "command": command("print('b')"), "scope": ["b.py"]},
        ],
    }
    report = execute_plan(plan, cwd=tmp_path, timeout_seconds=10)
    assert report["batchCount"] == 1
    assert report["batches"] == [["a", "b"]]
    assert [item["status"] for item in report["results"]] == ["passed", "passed"]
    assert report["results"][0]["returnCode"] == 0


def test_conflicting_scopes_are_serialized() -> None:
    plan = {
        "schemaVersion": 1,
        "maxWorkers": 4,
        "jobs": [
            {"id": "first", "command": command("pass"), "scope": ["shared"]},
            {"id": "second", "command": command("pass"), "scope": ["shared"]},
            {"id": "empty", "command": command("pass"), "scope": []},
        ],
    }
    assert [[job["id"] for job in batch] for batch in plan_batches(plan)] == [
        ["first"],
        ["second"],
        ["empty"],
    ]


def test_failure_is_recorded_and_invalid_plan_fails_closed(tmp_path: Path) -> None:
    failing = {
        "schemaVersion": 1,
        "maxWorkers": 1,
        "jobs": [{"id": "bad", "command": command("raise SystemExit(3)"), "scope": ["bad.py"]}],
    }
    report = execute_plan(failing, cwd=tmp_path, timeout_seconds=10)
    assert report["passed"] is False
    assert report["results"][0]["status"] == "failed"
    with pytest.raises(ParallelPlanError, match="maxWorkers"):
        execute_plan({"maxWorkers": 0, "jobs": failing["jobs"]}, cwd=tmp_path)
    with pytest.raises(ParallelPlanError, match="argv"):
        execute_plan(
            {"maxWorkers": 1, "jobs": [{"id": "bad", "command": "echo", "scope": ["x"]}]},
            cwd=tmp_path,
        )


def test_cli_writes_report_and_returns_failure_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.json"
    output = tmp_path / "nested" / "report.json"
    plan.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "maxWorkers": 1,
                "jobs": [{"id": "ok", "command": command("print('ok')"), "scope": ["x"]}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "ai_parallel_verification.py",
            "--plan",
            str(plan),
            "--output",
            str(output),
            "--cwd",
            str(tmp_path),
            "--timeout-seconds",
            "10",
        ],
    )
    assert main() == 0
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True
