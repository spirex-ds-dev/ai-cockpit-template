import json
import os
import signal
import subprocess
import sys
import time
from argparse import Namespace
from pathlib import Path

import pytest

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
    assert evidence["outputTail"].endswith("ok\n")
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
        session_id="abc123-hosted-42-1",
        run_id="42",
        command=["--", sys.executable, "-c", "print('direct')"],
    )
    assert run_quality_gate.run_gate(args) == 0
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["cache"] == {"applicable": True, "hit": True}
    assert evidence["logPath"] == str(log)
    assert evidence["sessionId"] == "abc123-hosted-42-1"
    assert evidence["runId"] == "42"


def test_runner_emits_source_and_environment_identity(tmp_path):
    args = Namespace(
        repository=str(ROOT),
        output=str(tmp_path / "timing.json"),
        log=str(tmp_path / "gate.log"),
        gate="identity",
        category="test",
        timeout_seconds=None,
        cache_applicable=False,
        cache_hit=False,
        session_id="identity-session",
        run_id="identity-run",
        command=["--", sys.executable, "-c", "print('identity')"],
    )

    assert run_quality_gate.run_gate(args) == 0
    evidence = json.loads((tmp_path / "timing.json").read_text(encoding="utf-8"))
    assert evidence["treeDigest"].startswith("sha256:")
    assert evidence["environment"]["os"]
    assert evidence["environment"]["python"] == sys.version.split()[0]
    assert evidence["environment"]["cpuCount"] >= 1


def test_runner_preserves_valid_make_jobserver_descriptors(monkeypatch):
    read_fd, write_fd = os.pipe()
    try:
        monkeypatch.setenv("MAKEFLAGS", f" --jobserver-auth={read_fd},{write_fd} -j")
        assert run_quality_gate.inherited_jobserver_fds() == (read_fd, write_fd)
    finally:
        os.close(read_fd)
        os.close(write_fd)
    assert run_quality_gate.inherited_jobserver_fds() == ()


def test_runner_streams_output_before_the_gate_finishes(tmp_path, monkeypatch):
    class RecordingStream:
        def __init__(self):
            self.events = []

        def write(self, value):
            self.events.append((time.monotonic(), value))
            return len(value)

        def flush(self):
            return None

    stream = RecordingStream()
    monkeypatch.setattr(sys, "stdout", stream)
    args = Namespace(
        repository=str(ROOT),
        output=str(tmp_path / "timing.json"),
        log=str(tmp_path / "gate.log"),
        gate="streaming",
        category="test",
        timeout_seconds=None,
        cache_applicable=False,
        cache_hit=False,
        session_id="local-stream",
        run_id="local",
        command=[
            "--",
            sys.executable,
            "-c",
            "import time; print('first', flush=True); time.sleep(0.5); print('last', flush=True)",
        ],
    )
    started = time.monotonic()
    assert run_quality_gate.run_gate(args) == 0
    finished = time.monotonic()
    first_at = next(at for at, value in stream.events if "first" in value)
    assert first_at - started < 0.3
    assert finished - first_at >= 0.3


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
        session_id="local-missing",
        run_id="local",
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
        session_id="local-timeout",
        run_id="local",
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
            "outputTail": "failure tail",
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
    assert summary["failureTails"] == {"failed": "failure tail"}
    assert summary["skippedGates"] == ["skipped"]
    assert "failed" in summarize_quality_gates.markdown(summary)


def test_scope_changed_paths_and_explicit_mode(tmp_path):
    assert determine_quality_scope.changed_paths("HEAD", "HEAD", ROOT) == []
    with pytest.raises(ValueError, match="unsupported quality scope mode"):
        determine_quality_scope.determine([], explicit="release")


def test_runner_preserves_failure_and_timeout_evidence(tmp_path):
    failure, output, _ = _run(tmp_path, [sys.executable, "-c", "raise SystemExit(3)"])
    assert failure.returncode == 3
    assert json.loads(output.read_text(encoding="utf-8"))["result"] == "failed"
    assert "🔴 quality-full blocked" in failure.stderr
    assert "Failed gate: sample" in failure.stderr
    assert "Recovery:" in failure.stderr
    timeout, output, _ = _run(
        tmp_path, [sys.executable, "-c", "import time; time.sleep(2)"], timeout=1
    )
    assert timeout.returncode == 124
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["result"] == "timeout"
    assert evidence["timedOut"] is True


def test_runner_preserves_cancellation_evidence(tmp_path):
    output = tmp_path / "timing" / "gate.json"
    log = tmp_path / "logs" / "gate.log"
    ready_marker = "runner-handler-ready"
    child_code = (
        "import time; "
        f"print(bytes.fromhex('{ready_marker.encode().hex()}').decode(), flush=True); "
        "time.sleep(30)"
    )
    assert ready_marker not in child_code
    process = subprocess.Popen(
        [
            sys.executable,
            str(RUNNER),
            "--gate",
            "cancel",
            "--category",
            "test",
            "--repository",
            str(ROOT),
            "--output",
            str(output),
            "--log",
            str(log),
            "--",
            sys.executable,
            "-c",
            child_code,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + 5
    while (
        not log.exists() or ready_marker not in log.read_text(encoding="utf-8")
    ) and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ready_marker in log.read_text(encoding="utf-8")
    os.kill(process.pid, signal.SIGTERM)
    assert process.wait(timeout=15) == 128 + signal.SIGTERM
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["result"] == "cancelled"
    assert evidence["timedOut"] is False


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


def test_summarizer_emits_profile_budget_and_cache_diagnostics():
    records = [
        {
            "schemaVersion": 1,
            "gate": "project-test",
            "category": "tests",
            "startedAt": "2026-08-01T00:00:00+00:00",
            "finishedAt": "2026-08-01T00:00:03+00:00",
            "durationMs": 3000,
            "result": "passed",
            "commitSha": "abc",
            "cache": {"applicable": True, "hit": False},
        },
        {
            "schemaVersion": 1,
            "gate": "project-test",
            "category": "tests",
            "startedAt": "2026-08-01T00:00:03+00:00",
            "finishedAt": "2026-08-01T00:00:04+00:00",
            "durationMs": 1000,
            "result": "passed",
            "commitSha": "abc",
            "cache": {"applicable": True, "hit": True},
        },
    ]

    summary = summarize_quality_gates.summarize(
        records,
        profile="strict",
        escalations=["release_preflight"],
        escalation_reasons=["release workflow file changed"],
        budget_ms=3500,
    )

    report = summary["performanceReport"]
    assert report["profile"] == "strict"
    assert report["verificationEscalations"] == ["release_preflight"]
    assert report["escalationReasons"] == ["release workflow file changed"]
    assert report["preflightDurationMs"] == 0
    assert report["gateDurationMs"] == 4000
    assert report["testDurationMs"] == 4000
    assert report["cache"] == {"applicable": 2, "hits": 1, "misses": 1}
    assert report["repeatedChecks"] == ["project-test"]
    assert report["slowestStep"] == {"name": "project-test", "durationMs": 3000}
    assert report["budget"] == {"limitMs": 3500, "status": "over_budget", "overageMs": 500}
    rendered = summarize_quality_gates.markdown(summary)
    assert "Budget status: over_budget" in rendered
    assert "Cache hits/misses: 1/1" in rendered


def test_summarizer_marks_an_absent_budget_as_not_configured():
    report = summarize_quality_gates.performance_report(
        [], profile="light", escalations=[], escalation_reasons=[], budget_ms=None
    )
    assert report["budget"] == {"limitMs": None, "status": "not_configured", "overageMs": 0}
