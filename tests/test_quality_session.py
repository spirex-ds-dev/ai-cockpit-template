from __future__ import annotations

import signal
import subprocess
import sys
from pathlib import Path

import pytest
import quality_session_lock
import run_quality_session


class FakeProcess:
    def __init__(self, pid: int, exit_code: int):
        self.pid = pid
        self.exit_code = exit_code
        self.wait_calls = 0

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls += 1
        return self.exit_code


def test_failed_phase_terminates_its_owned_process_group_and_stops_sequence(monkeypatch):
    started: list[list[str]] = []
    terminated: list[tuple[int, signal.Signals]] = []

    def fake_popen(command, **kwargs):
        started.append(command)
        assert kwargs["start_new_session"] is True
        return FakeProcess(901, 7)

    monkeypatch.setattr(run_quality_session.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(run_quality_session, "_owned_process_groups", lambda _pid: {901, 902})
    monkeypatch.setattr(
        run_quality_session.os, "killpg", lambda pid, sig: terminated.append((pid, sig))
    )

    result = run_quality_session.run_phases(["fast", "heavy"], ["make"])

    assert result == 7
    assert started == [["make", "fast"]]
    assert sorted(terminated) == [(901, signal.SIGTERM), (902, signal.SIGTERM)]


def test_successful_phases_run_in_order_without_cleanup(monkeypatch):
    started: list[list[str]] = []
    processes = [FakeProcess(902, 0), FakeProcess(903, 0)]

    def fake_popen(command, **kwargs):
        started.append(command)
        assert kwargs["start_new_session"] is True
        return processes.pop(0)

    monkeypatch.setattr(run_quality_session.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(run_quality_session, "_owned_process_groups", lambda _pid: {902})
    monkeypatch.setattr(
        run_quality_session.os, "killpg", lambda *_: pytest.fail("unexpected cleanup")
    )

    assert run_quality_session.run_phases(["fast", "heavy"], ["make"]) == 0
    assert started == [["make", "fast"], ["make", "heavy"]]


def test_interrupted_phase_terminates_its_owned_process_group(monkeypatch):
    terminated: list[tuple[int, signal.Signals]] = []

    class InterruptedProcess(FakeProcess):
        def wait(self, timeout: float | None = None) -> int:
            raise KeyboardInterrupt

    monkeypatch.setattr(
        run_quality_session.subprocess,
        "Popen",
        lambda *_args, **_kwargs: InterruptedProcess(904, 0),
    )
    monkeypatch.setattr(run_quality_session, "_owned_process_groups", lambda _pid: {904, 905})
    monkeypatch.setattr(
        run_quality_session.os, "killpg", lambda pid, sig: terminated.append((pid, sig))
    )

    with pytest.raises(KeyboardInterrupt):
        run_quality_session.run_phases(["fast"], ["make"])

    assert sorted(terminated) == [(904, signal.SIGTERM), (905, signal.SIGTERM)]


def test_owned_process_groups_include_independent_descendant_sessions(monkeypatch):
    class Snapshot:
        stdout = "100 1 100\n101 100 101\n102 101 102\n103 1 103\n"

    monkeypatch.setattr(run_quality_session.subprocess, "run", lambda *_args, **_kwargs: Snapshot())

    assert run_quality_session._owned_process_groups(100) == {100, 101, 102}


def test_second_same_worktree_session_fails_fast_with_canonical_retry(tmp_path):
    lock_path = tmp_path / "target" / "quality" / "session.lock"
    with quality_session_lock.acquire(lock_path, worktree=tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(Path(quality_session_lock.__file__)),
                "--lock",
                str(lock_path),
                "--worktree",
                str(tmp_path),
                "--",
                "make",
                "-f",
                "/dev/null",
                "-n",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    assert result.returncode == quality_session_lock.BUSY_EXIT_CODE
    assert "Quality session already active in this worktree" in result.stderr
    assert "Retry: make quality" in result.stderr


def test_distinct_worktrees_hold_independent_quality_locks(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    with (
        quality_session_lock.acquire(first / "target/quality/session.lock", worktree=first),
        quality_session_lock.acquire(second / "target/quality/session.lock", worktree=second),
    ):
        assert True


def test_lock_runner_marks_child_as_already_owned(tmp_path):
    lock_path = tmp_path / "target" / "quality" / "session.lock"
    makefile = tmp_path / "QualitySession.mk"
    makefile.write_text(
        'check-env:\n\t@test "$$QUALITY_SESSION_LOCK_HELD" = true\n', encoding="utf-8"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(Path(quality_session_lock.__file__)),
            "--lock",
            str(lock_path),
            "--worktree",
            str(tmp_path),
            "--",
            "make",
            "-f",
            str(makefile),
            "check-env",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0


def test_lock_runner_rejects_non_make_commands(tmp_path):
    with pytest.raises(ValueError, match="only Make commands"):
        quality_session_lock.run(
            [sys.executable, "-c", "raise SystemExit(0)"],
            lock_path=tmp_path / "target/quality/session.lock",
            worktree=tmp_path,
        )


def test_run_returns_child_status_and_busy_path_without_spawning(tmp_path, monkeypatch, capsys):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return type("Result", (), {"returncode": 7})()

    monkeypatch.setattr(quality_session_lock.subprocess, "run", fake_run)
    assert (
        quality_session_lock.run(
            ["make", "quality-fast"],
            lock_path=tmp_path / "target/quality/session.lock",
            worktree=tmp_path,
        )
        == 7
    )
    assert calls[0][1]["env"]["QUALITY_SESSION_LOCK_HELD"] == "true"

    monkeypatch.setattr(
        quality_session_lock,
        "acquire",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(quality_session_lock.QualitySessionBusy()),
    )
    assert (
        quality_session_lock.run(
            ["make", "quality"],
            lock_path=tmp_path / "target/quality/session.lock",
            worktree=tmp_path,
        )
        == quality_session_lock.BUSY_EXIT_CODE
    )
    assert "Retry: make quality" in capsys.readouterr().err


def test_cli_parsing_and_main_delegate_to_resolved_paths(tmp_path, monkeypatch):
    lock = tmp_path / "lock"
    monkeypatch.setattr(
        "sys.argv",
        [
            "quality_session_lock.py",
            "--lock",
            str(lock),
            "--worktree",
            str(tmp_path),
            "--",
            "make",
            "quality",
        ],
    )
    parsed = quality_session_lock.parse_args()
    assert parsed.command == ["make", "quality"]
    observed = {}
    monkeypatch.setattr(
        quality_session_lock,
        "run",
        lambda command, **kwargs: observed.update(command=command, **kwargs) or 0,
    )
    assert quality_session_lock.main() == 0
    assert observed["lock_path"] == lock.resolve()
    assert observed["worktree"] == tmp_path.resolve()
