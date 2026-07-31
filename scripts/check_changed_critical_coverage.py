#!/usr/bin/env python3
"""Predict critical-file coverage regressions for the current PR diff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from check_critical_coverage import CRITICAL_MINIMUMS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = PROJECT_ROOT / ".ai" / "guards" / "changed_critical_coverage_policy.json"
DEFAULT_REPORT = PROJECT_ROOT / "target" / "changed-critical-coverage.json"


def load_policy(path: Path) -> dict:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load changed-critical coverage policy: {exc}") from exc
    if not isinstance(policy, dict) or policy.get("version") != 1:
        raise ValueError("changed-critical coverage policy version must be 1")
    if not isinstance(policy.get("criticalFiles"), dict):
        raise TypeError("changed-critical coverage policy must declare criticalFiles")
    return policy


def select_changed_critical(
    changed_files: list[str],
    policy: dict,
    critical_minimums: dict[str, float],
) -> tuple[list[str], list[str]]:
    changed = set(changed_files)
    configured = policy.get("criticalFiles", {})
    selected: list[str] = []
    tests: list[str] = []
    for path, authoritative_floor in critical_minimums.items():
        if path not in changed:
            continue
        entry = configured.get(path) if isinstance(configured, dict) else None
        if not isinstance(entry, dict):
            raise TypeError(f"missing changed-critical test mapping: {path}")
        configured_floor = entry.get("minimum")
        if not isinstance(configured_floor, (int, float)) or float(configured_floor) != float(
            authoritative_floor
        ):
            raise ValueError(
                f"{path}: configured minimum {configured_floor!r} does not match "
                f"authoritative floor {authoritative_floor:g}"
            )
        declared_tests = entry.get("tests")
        if (
            not isinstance(declared_tests, list)
            or not declared_tests
            or not all(isinstance(item, str) and item for item in declared_tests)
        ):
            raise ValueError(f"missing changed-critical test mapping: {path}")
        selected.append(path)
        for test_path in declared_tests:
            if test_path not in tests:
                tests.append(test_path)
    return selected, tests


def focused_coverage_failures(
    report: dict,
    selected: list[str],
    critical_minimums: dict[str, float],
) -> list[str]:
    files = report.get("files", {})
    failures: list[str] = []
    for path in selected:
        data = files.get(path) if isinstance(files, dict) else None
        summary = data.get("summary", {}) if isinstance(data, dict) else {}
        covered = summary.get("percent_covered") if isinstance(summary, dict) else None
        minimum = critical_minimums[path]
        if not isinstance(covered, (int, float)):
            failures.append(f"{path}: missing from focused coverage report")
        elif covered < minimum:
            failures.append(f"{path}: {covered:.2f}% is below {minimum:g}%")
    return failures


def git_changed_files(base: str) -> list[str]:
    commands = [
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    changed: list[str] = []
    for command in commands:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError(
                f"cannot resolve changed files from {base}: "
                f"{(result.stderr or result.stdout).strip()}"
            )
        for line in result.stdout.splitlines():
            path = line.strip()
            if path and path not in changed:
                changed.append(path)
    return changed


def run_predictor(
    *,
    base: str,
    policy_path: Path,
    report_path: Path,
    project_root: Path,
    run_command: Callable[[list[str]], int],
    critical_minimums: dict[str, float],
) -> int:
    policy = load_policy(policy_path)
    selected, tests = select_changed_critical(
        git_changed_files(base),
        policy,
        critical_minimums,
    )
    if not selected:
        print("changed-critical coverage: not applicable; no critical script changed")
        return 0
    missing_tests = [path for path in tests if not (project_root / path).is_file()]
    if missing_tests:
        raise ValueError(
            "changed-critical test mapping references missing file(s): " + ", ".join(missing_tests)
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--cov=scripts",
        f"--cov-report=json:{report_path}",
        "--cov-report=term-missing:skip-covered",
        *tests,
    ]
    result = run_command(command)
    if result != 0:
        return result
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load focused coverage report: {exc}") from exc
    failures = focused_coverage_failures(report, selected, critical_minimums)
    if failures:
        for failure in failures:
            print(f"[ERROR] {failure}", file=sys.stderr)
        return 1
    rendered = ", ".join(f"{path}>={critical_minimums[path]:g}%" for path in selected)
    print(f"changed-critical coverage passed: {rendered}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    def run(command: list[str]) -> int:
        return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode

    try:
        return run_predictor(
            base=args.base,
            policy_path=args.policy,
            report_path=args.report,
            project_root=PROJECT_ROOT,
            run_command=run,
            critical_minimums=CRITICAL_MINIMUMS,
        )
    except (TypeError, ValueError) as exc:
        print(f"changed-critical coverage failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
