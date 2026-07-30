#!/usr/bin/env python3
"""Run one quality gate and persist auditable timing and output evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import threading
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return f"sha256:{value.hexdigest()}"


def commit_sha(repository: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def display_path(path: Path, repository: Path) -> str:
    try:
        return str(path.relative_to(repository))
    except ValueError:
        return str(path)


def signal_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (AttributeError, OSError):
        process.terminate()


def inherited_jobserver_fds() -> tuple[int, ...]:
    if os.name != "posix":
        return ()
    match = re.search(r"--jobserver-(?:auth|fds)=(\d+),(\d+)", os.environ.get("MAKEFLAGS", ""))
    if match is None:
        return ()
    descriptors = tuple(int(value) for value in match.groups())
    try:
        for descriptor in descriptors:
            os.fstat(descriptor)
    except OSError:
        return ()
    return descriptors


def stop_process(process: subprocess.Popen[str]) -> None:
    signal_process(process)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def run_gate(args: argparse.Namespace) -> int:
    repository = Path(args.repository).resolve()
    output = (repository / args.output).resolve()
    log = (repository / args.log).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    started = now()
    result_name = "failed"
    exit_code = 1
    timed_out = False
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("a command is required after --")
    captured_parts: deque[str] = deque()
    captured_size = 0
    capture_limit = 4000
    cancelled_signal: int | None = None
    with log.open("w", encoding="utf-8") as log_stream:
        log_stream.write(f"$ {' '.join(command)}\n")
        log_stream.flush()
        process = subprocess.Popen(
            command,
            cwd=repository,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            start_new_session=True,
            pass_fds=inherited_jobserver_fds(),
        )
        if process.stdout is None:
            stop_process(process)
            raise RuntimeError("quality gate output stream is unavailable")
        process_stdout = process.stdout
        previous_handlers: dict[int, Any] = {}

        def cancel(signum: int, _frame: Any) -> None:
            nonlocal cancelled_signal
            cancelled_signal = signum
            signal_process(process)

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, cancel)

        def relay() -> None:
            nonlocal captured_size
            for line in process_stdout:
                log_stream.write(line)
                log_stream.flush()
                sys.stdout.write(line)
                sys.stdout.flush()
                captured_parts.append(line)
                captured_size += len(line)
                while captured_size > capture_limit and captured_parts:
                    captured_size -= len(captured_parts.popleft())

        relay_thread = threading.Thread(target=relay, name=f"quality-{args.gate}", daemon=True)
        relay_thread.start()
        try:
            exit_code = process.wait(timeout=args.timeout_seconds)
            if cancelled_signal is not None:
                exit_code = 128 + cancelled_signal
                result_name = "cancelled"
            else:
                result_name = "passed" if exit_code == 0 else "failed"
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = 124
            result_name = "timeout"
            stop_process(process)
        relay_thread.join(timeout=5)
        for restored_signum, handler in previous_handlers.items():
            signal.signal(restored_signum, handler)
    captured = "".join(captured_parts)[-capture_limit:]
    finished = now()
    evidence: dict[str, Any] = {
        "schemaVersion": 1,
        "gate": args.gate,
        "category": args.category,
        "command": " ".join(command),
        "startedAt": started,
        "finishedAt": finished,
        "durationMs": max(
            0,
            int(
                (
                    datetime.fromisoformat(finished[:-1]) - datetime.fromisoformat(started[:-1])
                ).total_seconds()
                * 1000
            ),
        ),
        "result": result_name,
        "exitCode": exit_code,
        "commitSha": commit_sha(repository),
        "sessionId": getattr(args, "session_id", "local"),
        "runId": getattr(args, "run_id", "local"),
        "cache": {"applicable": args.cache_applicable, "hit": args.cache_hit},
        "logPath": display_path(log, repository),
        "outputDigest": digest(log),
        "outputTail": captured[-4000:],
        "timedOut": timed_out,
    }
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result_name != "passed":
        print(
            f"Gate failed: {args.gate}\nRetry: {evidence['command']}\nLog: {evidence['logPath']}",
            file=sys.stderr,
        )
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log", default=None)
    parser.add_argument("--repository", default=".")
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--session-id", default="local")
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "local"))
    parser.add_argument("--cache-applicable", action="store_true")
    parser.add_argument("--cache-hit", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.log is None:
        args.log = f"target/quality/logs/{args.gate}.log"
    try:
        return run_gate(args)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"[ERROR] quality gate telemetry failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
