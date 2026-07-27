#!/usr/bin/env python3
"""Run one quality gate and persist auditable timing and output evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
    try:
        completed = subprocess.run(
            command,
            cwd=repository,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=args.timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
        result_name = "passed" if exit_code == 0 else "failed"
        captured = completed.stdout or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        result_name = "timeout"
        captured = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
    with log.open("w", encoding="utf-8") as stream:
        stream.write(f"$ {' '.join(command)}\n")
        stream.write(captured)
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
        "cache": {"applicable": args.cache_applicable, "hit": args.cache_hit},
        "logPath": display_path(log, repository),
        "outputDigest": digest(log),
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
