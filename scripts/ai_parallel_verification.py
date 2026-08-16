#!/usr/bin/env python3
"""Run bounded verification jobs concurrently when their declared scopes do not conflict."""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - argv-only execution is validated below
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


class ParallelPlanError(ValueError):
    """Raised when a parallel verification plan is unsafe or malformed."""


def validate_plan(plan: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    jobs = plan.get("jobs")
    workers = plan.get("maxWorkers")
    if not isinstance(jobs, list) or not jobs:
        raise ParallelPlanError("jobs must be a non-empty array")
    if not isinstance(workers, int) or isinstance(workers, bool) or not 1 <= workers <= 8:
        raise ParallelPlanError("maxWorkers must be an integer from 1 through 8")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            raise ParallelPlanError(f"job {index} must be an object")
        job_id = job.get("id")
        command = job.get("command")
        scope = job.get("scope")
        if not isinstance(job_id, str) or not job_id.strip() or job_id in seen:
            raise ParallelPlanError(f"job {index} has a duplicate or empty id")
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(item, str) or not item for item in command)
        ):
            raise ParallelPlanError(f"job {job_id} command must be a non-empty argv array")
        if not isinstance(scope, list) or any(
            not isinstance(item, str) or not item for item in scope
        ):
            raise ParallelPlanError(f"job {job_id} scope must be a string array")
        seen.add(job_id)
        normalized.append({"id": job_id, "command": command, "scope": sorted(set(scope))})
    return normalized, workers


def _conflicts(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_scope = set(left["scope"])
    right_scope = set(right["scope"])
    return not left_scope or not right_scope or bool(left_scope & right_scope)


def plan_batches(plan: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """Place jobs into deterministic conflict-free batches using conservative scope rules."""
    jobs, _ = validate_plan(plan)
    batches: list[list[dict[str, Any]]] = []
    for job in jobs:
        for batch in batches:
            if all(not _conflicts(job, existing) for existing in batch):
                batch.append(job)
                break
        else:
            batches.append([job])
    return batches


def _run_job(job: dict[str, Any], *, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(  # nosec B603 - validated argv, no shell, bounded timeout
            job["command"],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        status = "passed" if completed.returncode == 0 else "failed"
        return {
            "id": job["id"],
            "command": job["command"],
            "scope": job["scope"],
            "status": status,
            "returnCode": completed.returncode,
            "durationMs": int((time.monotonic() - started) * 1000),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "id": job["id"],
            "command": job["command"],
            "scope": job["scope"],
            "status": "timed_out",
            "returnCode": None,
            "durationMs": int((time.monotonic() - started) * 1000),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "timeout",
        }


def execute_plan(plan: dict[str, Any], *, cwd: Path, timeout_seconds: int = 300) -> dict[str, Any]:
    jobs, workers = validate_plan(plan)
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 3600:
        raise ParallelPlanError("timeoutSeconds must be from 1 through 3600")
    batches = plan_batches(plan)
    results: list[dict[str, Any]] = []
    for batch in batches:
        with ThreadPoolExecutor(max_workers=min(workers, len(batch))) as executor:
            futures = [
                executor.submit(_run_job, job, cwd=cwd, timeout_seconds=timeout_seconds)
                for job in batch
            ]
            results.extend(future.result() for future in as_completed(futures))
    order = {job["id"]: index for index, job in enumerate(jobs)}
    results.sort(key=lambda item: order[item["id"]])
    return {
        "schemaVersion": 1,
        "maxWorkers": workers,
        "batchCount": len(batches),
        "batches": [[job["id"] for job in batch] for batch in batches],
        "results": results,
        "passed": all(item["status"] == "passed" for item in results),
        "advisory": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cwd", type=Path, default=Path("."))
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        if not isinstance(plan, dict):
            raise ParallelPlanError("plan must be an object")
        report = execute_plan(plan, cwd=args.cwd.resolve(), timeout_seconds=args.timeout_seconds)
    except (OSError, json.JSONDecodeError, ParallelPlanError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"parallel verification report written: {args.output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
