#!/usr/bin/env python3
"""Run quality phases in isolated process groups and clean them on failure."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess  # nosec B404: process control is this script's documented responsibility
import sys
from collections.abc import Sequence
from typing import Any


def _owned_process_groups(root_pid: int) -> set[int]:
    """Return the process groups rooted below one phase's Make process."""
    try:
        snapshot = subprocess.run(  # nosec B603: fixed local `ps` inspection command
            ["/bin/ps", "-eo", "pid=,ppid=,pgid="],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return {root_pid}

    children: dict[int, list[tuple[int, int]]] = {}
    for line in snapshot.stdout.splitlines():
        try:
            pid, parent_pid, process_group = (int(value) for value in line.split())
        except ValueError:
            continue
        children.setdefault(parent_pid, []).append((pid, process_group))

    groups = {root_pid}
    pending = [root_pid]
    while pending:
        parent_pid = pending.pop()
        for child_pid, process_group in children.get(parent_pid, []):
            groups.add(process_group)
            pending.append(child_pid)
    return groups


def _terminate_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate and reap every process group owned by one quality phase."""
    groups = _owned_process_groups(process.pid)
    for process_group in groups:
        try:
            os.killpg(process_group, signal.SIGTERM)
        except (AttributeError, ProcessLookupError, OSError):
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        for process_group in groups:
            try:
                os.killpg(process_group, signal.SIGKILL)
            except (AttributeError, ProcessLookupError, OSError):
                pass
        process.wait()


def run_phases(phases: Sequence[str], make_command: Sequence[str]) -> int:
    """Run each phase in order, returning its failure after owned cleanup."""
    for phase in phases:
        process = subprocess.Popen(  # nosec B603: Contract-bound Make command and phase names
            [*make_command, phase], start_new_session=True
        )
        previous_handlers: dict[int, Any] = {}

        def interrupt(_signum: int, _frame: object) -> None:
            raise KeyboardInterrupt

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, interrupt)
        try:
            result = process.wait()
        except BaseException:
            _terminate_group(process)
            raise
        finally:
            for restore_signum, handler in previous_handlers.items():
                signal.signal(restore_signum, handler)
        if result:
            _terminate_group(process)
            return result
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", action="append", required=True)
    parser.add_argument("make_command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.make_command and args.make_command[0] == "--":
        args.make_command = args.make_command[1:]
    if not args.make_command:
        parser.error("a Make command is required after --")
    return args


def main() -> int:
    args = parse_args()
    return run_phases(args.phase, args.make_command)


if __name__ == "__main__":
    sys.exit(main())
