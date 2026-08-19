from __future__ import annotations

import signal
import subprocess

import ai_finish
import pytest


class FakeProcess:
    def __init__(self, *, timeout: bool = False):
        self.pid = 901
        self.returncode = None
        self.timeout = timeout
        self.communicate_calls = 0
        self.wait_calls = 0

    def communicate(self, timeout=None):
        self.communicate_calls += 1
        if self.timeout and self.communicate_calls == 1:
            raise subprocess.TimeoutExpired(["make", "quality"], timeout)
        self.returncode = 0
        return "captured\n", None

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.timeout and self.wait_calls == 1:
            raise subprocess.TimeoutExpired(["make", "quality"], timeout)
        self.returncode = 0
        return self.returncode


def test_timeout_terminates_and_escalates_only_the_owned_process_group(monkeypatch):
    process = FakeProcess(timeout=True)
    signals: list[tuple[int, signal.Signals]] = []

    monkeypatch.setattr(ai_finish.subprocess, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(ai_finish, "_owned_process_groups", lambda _pid: {901})
    monkeypatch.setattr(
        ai_finish.os,
        "killpg",
        lambda pid, signum: signals.append((pid, signum)),
    )
    monkeypatch.setenv(ai_finish.FINISH_COMMAND_TIMEOUT_ENV, "1")

    code, _duration, output = ai_finish.run(["make", "quality"])

    assert code == 124
    assert "timed out after 1 second(s)" in output
    assert signals == [(901, signal.SIGTERM), (901, signal.SIGKILL)]
    assert process.communicate_calls == 2
    assert process.wait_calls == 2


def test_sigterm_cancellation_returns_signal_failure_and_cleans_owned_group(monkeypatch):
    process = FakeProcess()
    signals: list[tuple[int, signal.Signals]] = []

    monkeypatch.setattr(ai_finish.subprocess, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(ai_finish, "_owned_process_groups", lambda _pid: {901})
    monkeypatch.setattr(
        ai_finish.os,
        "killpg",
        lambda pid, signum: signals.append((pid, signum)),
    )

    def communicate(timeout=None):
        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)
        handler(signal.SIGTERM, None)
        return "cancelled\n", None

    process.communicate = communicate

    code, _duration, output = ai_finish.run(["make", "quality"])

    assert code == 128 + signal.SIGTERM
    assert "cancelled by signal" in output
    assert signals == [(901, signal.SIGTERM)]


def test_invalid_timeout_fails_closed_without_spawning(monkeypatch):
    monkeypatch.setenv(ai_finish.FINISH_COMMAND_TIMEOUT_ENV, "not-a-number")
    monkeypatch.setattr(
        ai_finish.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("invalid timeout must not spawn a command"),
    )

    code, duration, output = ai_finish.run(["make", "quality"])

    assert code == 2
    assert duration == 0
    assert ai_finish.FINISH_COMMAND_TIMEOUT_ENV in output


def test_timeout_defaults_when_unset(monkeypatch):
    monkeypatch.delenv(ai_finish.FINISH_COMMAND_TIMEOUT_ENV, raising=False)

    assert (
        ai_finish.finish_command_timeout_seconds()
        == ai_finish.FINISH_COMMAND_TIMEOUT_DEFAULT_SECONDS
    )


def test_timeout_rejects_non_integer_or_out_of_range(monkeypatch):
    monkeypatch.setenv(ai_finish.FINISH_COMMAND_TIMEOUT_ENV, "0")

    with pytest.raises(ValueError, match="integer from 1 through"):
        ai_finish.finish_command_timeout_seconds()


def test_process_group_helper_never_targets_an_unrelated_group(monkeypatch):
    signals: list[tuple[int, signal.Signals]] = []
    process = FakeProcess()
    monkeypatch.setattr(
        ai_finish.os,
        "killpg",
        lambda pid, signum: signals.append((pid, signum)),
    )

    ai_finish._signal_owned_process_group(process, signal.SIGTERM)

    assert signals == [(901, signal.SIGTERM)]


def test_process_tree_cleanup_collects_descendant_process_groups(monkeypatch):
    class Snapshot:
        stdout = "901 1 901\n902 901 902\n903 902 903\n904 1 904\n"

    monkeypatch.setattr(ai_finish.subprocess, "run", lambda *_args, **_kwargs: Snapshot())

    assert ai_finish._owned_process_groups(901) == {901, 902, 903}
