import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from scripts import determine_quality_scope, run_quality_gate, summarize_quality_gates

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_quality_gate.py"
SUMMARY = ROOT / "scripts" / "summarize_quality_gates.py"


def _run(tmp_path, command, timeout=None):
    output = tmp_path / "timing" / "gate.json"
    log = tmp_path / "logs" / "gate.log"
    args = [
        sys.executable,
        str(RUNNER),
        "--gate",
        "sample",
        "--category",
        "test",
        "--repository",
        str(ROOT),
        "--output",
        str(output),
        "--log",
        str(log),
    ]
    if timeout is not None:
        args += ["--timeout-seconds", str(timeout)]
    result = subprocess.run(args + ["--"] + command, text=True, capture_output=True, check=False)
    return result, output, log


def test_runner_emits_pass_evidence(tmp_path):
    result, output, log = _run(tmp_path, [sys.executable, "-c", "print('ok')"])
    assert result.returncode == 0
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["result"] == "passed"
    assert evidence["exitCode"] == 0
    assert evidence["outputDigest"].startswith("sha256:")
    assert "ok" in log.read_text(encoding="utf-8")


def test_runner_function_covers_relative_output_and_cache_metadata(tmp_path):
    output = tmp_path / "timing.json"
    log = tmp_path / "gate.log"
    args = Namespace(
        repository=str(ROOT),
        output=str(output),
        log=str(log),
        gate="direct",
        category="test",
        timeout_seconds=None,
        cache_applicable=True,
        cache_hit=True,
        command=["--", sys.executable, "-c", "print('direct')"],
    )
    assert run_quality_gate.run_gate(args) == 0
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["cache"] == {"applicable": True, "hit": True}
    assert evidence["logPath"] == str(log)


def test_runner_rejects_missing_command_and_preserves_timeout_directly(tmp_path):
    missing = Namespace(
        repository=str(ROOT),
        output=str(tmp_path / "missing.json"),
        log=str(tmp_path / "missing.log"),
        gate="missing",
        category="test",
        timeout_seconds=None,
        cache_applicable=False,
        cache_hit=False,
        command=[],
    )
    try:
        run_quality_gate.run_gate(missing)
    except ValueError as exc:
        assert "command is required" in str(exc)
    else:
        raise AssertionError("missing command must fail closed")
    timeout = Namespace(
        repository=str(ROOT),
        output=str(tmp_path / "timeout.json"),
        log=str(tmp_path / "timeout.log"),
        gate="timeout",
        category="test",
        timeout_seconds=1,
        cache_applicable=False,
        cache_hit=False,
        command=[sys.executable, "-c", "import time; time.sleep(2)"],
    )
    assert run_quality_gate.run_gate(timeout) == 124


def test_summarizer_loads_only_schema_one_and_main_writes_outputs(tmp_path, monkeypatch):
    timing = tmp_path / "timing"
    timing.mkdir()
    (timing / "ignored.json").write_text(json.dumps({"schemaVersion": 2}), encoding="utf-8")
    (timing / "one.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "gate": "one",
                "category": "test",
                "durationMs": 1,
                "startedAt": "2026-07-27T00:00:00Z",
                "finishedAt": "2026-07-27T00:00:01Z",
                "result": "passed",
                "commitSha": "abc",
                "cache": {"hit": False},
            }
        ),
        encoding="utf-8",
    )
    assert len(summarize_quality_gates.load_records(timing)) == 1
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_quality_gates.py",
            "--input",
            str(timing),
            "--json-output",
            str(tmp_path / "out.json"),
            "--markdown-output",
            str(tmp_path / "out.md"),
        ],
    )
    assert summarize_quality_gates.main() == 0
    assert (tmp_path / "out.json").is_file()


def test_summarizer_function_reports_failed_and_skipped_records():
    records = [
        {
            "gate": "failed",
            "category": "test",
            "durationMs": 50,
            "startedAt": "2026-07-27T00:00:00Z",
            "finishedAt": "2026-07-27T00:00:01Z",
            "result": "failed",
            "commitSha": "abc",
        },
        {
            "gate": "skipped",
            "category": "test",
            "durationMs": 1,
            "startedAt": "2026-07-27T00:00:00Z",
            "finishedAt": "2026-07-27T00:00:01Z",
            "result": "skipped",
            "commitSha": "abc",
            "cache": {"hit": True},
        },
    ]
    summary = summarize_quality_gates.summarize(records)
    assert summary["decision"] == "FAIL"
    assert summary["failedGates"] == ["failed"]
    assert summary["skippedGates"] == ["skipped"]
    assert "failed" in summarize_quality_gates.markdown(summary)


def test_scope_changed_paths_and_explicit_mode(tmp_path):
    assert determine_quality_scope.changed_paths("HEAD", "HEAD", ROOT) == []
    result = determine_quality_scope.determine([], explicit="release")
    assert result["requiredGroups"] == ["quality-fast", "quality-full", "quality-release"]


def test_runner_preserves_failure_and_timeout_evidence(tmp_path):
    failure, output, _ = _run(tmp_path, [sys.executable, "-c", "raise SystemExit(3)"])
    assert failure.returncode == 3
    assert json.loads(output.read_text(encoding="utf-8"))["result"] == "failed"
    timeout, output, _ = _run(
        tmp_path, [sys.executable, "-c", "import time; time.sleep(2)"], timeout=1
    )
    assert timeout.returncode == 124
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["result"] == "timeout"
    assert evidence["timedOut"] is True


def test_summarizer_reports_decision_and_slowest_gate(tmp_path):
    timing = tmp_path / "timing"
    timing.mkdir()
    for gate, duration in (("fast", 10), ("slow", 30)):
        (timing / f"{gate}.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "gate": gate,
                    "category": "test",
                    "startedAt": "2026-07-27T00:00:00Z",
                    "finishedAt": "2026-07-27T00:00:01Z",
                    "durationMs": duration,
                    "result": "passed",
                    "exitCode": 0,
                    "commitSha": "abc",
                    "cache": {"applicable": False, "hit": False},
                }
            ),
            encoding="utf-8",
        )
    result = subprocess.run(
        [
            sys.executable,
            str(SUMMARY),
            "--input",
            str(timing),
            "--json-output",
            str(tmp_path / "summary.json"),
            "--markdown-output",
            str(tmp_path / "summary.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["decision"] == "PASS"
    assert summary["slowestGate"] == "slow"
    assert "Parallel efficiency" in (tmp_path / "summary.md").read_text(encoding="utf-8")
