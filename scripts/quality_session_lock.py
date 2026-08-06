#!/usr/bin/env python3
"""Serialize quality writers inside one worktree with an OS-owned lock."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import os
import subprocess  # nosec B404: this runner owns a Contract-bound local command
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

BUSY_EXIT_CODE = 75


class QualitySessionBusy(RuntimeError):
    """Raised when another live quality session owns this worktree."""


@contextlib.contextmanager
def acquire(lock_path: Path, *, worktree: Path) -> Iterator[None]:
    """Acquire a non-blocking worktree-local lock released by the kernel on exit."""
    del worktree  # The caller supplies it for audit-friendly API symmetry and messages.
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise QualitySessionBusy from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def run(command: Sequence[str], *, lock_path: Path, worktree: Path) -> int:
    """Run one owned quality command, or fail closed without waiting/reusing."""
    if not command or Path(command[0]).name not in {"make", "gmake"}:
        raise ValueError("quality session lock accepts only Make commands")
    try:
        with acquire(lock_path, worktree=worktree):
            environment = os.environ.copy()
            environment["QUALITY_SESSION_LOCK_HELD"] = "true"
            return subprocess.run(  # nosec B603: validated Make executable and Makefile-owned arguments
                command, cwd=worktree, env=environment, check=False
            ).returncode
    except QualitySessionBusy:
        print(
            "Quality session already active in this worktree; no coverage or quality evidence "
            "was produced by this invocation. Wait for the owning session to finish, then retry.\n"
            "Retry: make quality",
            file=sys.stderr,
        )
        return BUSY_EXIT_CODE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--worktree", type=Path, default=Path("."))
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a quality command is required after --")
    return args


def main() -> int:
    args = parse_args()
    return run(args.command, lock_path=args.lock.resolve(), worktree=args.worktree.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
