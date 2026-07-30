from __future__ import annotations

import signal

import pytest
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
