"""Open and validate a narrow same-Work-Item recovery after a failed PR audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - all process calls below use fixed list-form commands
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from ai_common import PROJECT_ROOT, clean_git_environment

RECEIPT_DIRECTORY = Path(".ai/work-items/recovery-receipts")
ARCHIVE_SUFFIXES = ("contract", "summary", "outcome", "archive-manifest")
ALLOWED_GATES = {
    "changedCriticalCoverage",
    "archiveEvidence",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_files(root: Path, task: str) -> dict[str, Path]:
    found: dict[str, list[Path]] = {suffix: [] for suffix in ARCHIVE_SUFFIXES}
    for year in root.joinpath(".ai/work-items/archive").glob("*"):
        if not year.is_dir():
            continue
        for suffix in ARCHIVE_SUFFIXES:
            candidate = year / f"{task}.{suffix}.json"
            if candidate.is_file():
                found[suffix].append(candidate)
    missing_or_ambiguous = [name for name, paths in found.items() if len(paths) != 1]
    if missing_or_ambiguous:
        raise ValueError(
            "expected exactly one immutable archive artifact for "
            f"{task}: {', '.join(missing_or_ambiguous)}"
        )
    return {name: paths[0] for name, paths in found.items()}


def classify_failure(output: str) -> str:
    lowered = output.lower()
    if "changed-critical coverage" in lowered or "below" in lowered and "coverage" in lowered:
        return "changedCriticalCoverage"
    if "archive" in lowered or "paired ownership" in lowered or "human benefit report" in lowered:
        return "archiveEvidence"
    raise ValueError(
        "PR audit failure is not an allowed coverage or archive-evidence recovery gate"
    )


def normalized_paths(paths: list[str]) -> list[str]:
    if not paths:
        raise ValueError("at least one recovery path is required")
    normalized: list[str] = []
    for raw in paths:
        value = raw.strip().replace("\\", "/")
        if not value or value.startswith("/") or ".." in Path(value).parts:
            raise ValueError(f"invalid recovery path: {raw!r}")
        if value.startswith((".ai/work-items/archive/", ".ai/work-items/active/")):
            raise ValueError("recovery paths must not rewrite archive or active Work Item evidence")
        if value not in normalized:
            normalized.append(value)
    return normalized


def open_post_archive_recovery(
    *,
    root: Path,
    task: str,
    base_commit: str,
    issue: str,
    authority: str,
    recovery_paths: list[str],
    run_pr_audit: Callable[[list[str]], tuple[int, str]],
    worktree_clean: Callable[[], bool],
) -> dict:
    if len(base_commit) != 40:
        raise ValueError("PR base commit must be a 40-character SHA")
    if not issue.startswith("https://github.com/"):
        raise ValueError("recovery Issue must be a GitHub Issue URL")
    if not authority.strip():
        raise ValueError("human authority is required")
    if not worktree_clean():
        raise ValueError("post-archive recovery must start from a clean committed worktree")
    artifacts = archive_files(root, task)
    outcome = json.loads(artifacts["outcome"].read_text(encoding="utf-8"))
    if outcome.get("workItemId") != task or outcome.get("status") != "completed":
        raise ValueError("same-Work-Item recovery requires a completed archived Outcome")
    code, output = run_pr_audit(["make", "check-ai-pr", f"AI_BASE_COMMIT={base_commit}"])
    if code == 0:
        raise ValueError("post-archive recovery may open only after check-ai-pr must fail")
    gate = classify_failure(output)
    receipt = {
        "receiptVersion": 1,
        "kind": "same_work_item_post_archive_recovery",
        "workItemId": task,
        "prBaseCommit": base_commit,
        "issue": issue,
        "humanAuthorization": {"type": "human", "reference": authority},
        "failure": {
            "gate": gate,
            "command": ["make", "check-ai-pr", f"AI_BASE_COMMIT={base_commit}"],
            "exitCode": code,
            "outputDigest": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        },
        "archive": {
            name: {
                "path": path.relative_to(root).as_posix(),
                "sha256": digest(path),
            }
            for name, path in artifacts.items()
        },
        "recoveryPaths": normalized_paths(recovery_paths),
        "openedAt": datetime.now(UTC).isoformat(),
    }
    directory = root / RECEIPT_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{task}.json"
    if target.exists():
        raise ValueError(f"recovery receipt already exists: {target.relative_to(root)}")
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def validate_recovery_receipt(root: Path, receipt: object, *, pr_base: str) -> list[str]:
    if not isinstance(receipt, dict):
        return ["recovery receipt must be an object"]
    if (
        receipt.get("receiptVersion") != 1
        or receipt.get("kind") != "same_work_item_post_archive_recovery"
    ):
        return ["recovery receipt has an unsupported schema"]
    task = receipt.get("workItemId")
    if not isinstance(task, str) or not task:
        return ["recovery receipt workItemId is required"]
    if receipt.get("prBaseCommit") != pr_base:
        return ["recovery receipt PR base does not match the checked PR base"]
    authorization = receipt.get("humanAuthorization")
    if (
        not isinstance(authorization, dict)
        or authorization.get("type") != "human"
        or not isinstance(authorization.get("reference"), str)
        or not authorization["reference"].strip()
    ):
        return ["recovery receipt requires human authorization"]
    failure = receipt.get("failure")
    if not isinstance(failure, dict) or failure.get("gate") not in ALLOWED_GATES:
        return ["recovery receipt failure gate is not allowed"]
    paths = receipt.get("recoveryPaths")
    try:
        if not isinstance(paths, list) or normalized_paths(paths) != paths:
            return ["recovery receipt paths are invalid or non-canonical"]
        artifacts = archive_files(root, task)
    except ValueError as exc:
        return [str(exc)]
    archive = receipt.get("archive")
    if not isinstance(archive, dict):
        return ["recovery receipt archive binding is required"]
    issues: list[str] = []
    for name, path in artifacts.items():
        expected = archive.get(name)
        if (
            not isinstance(expected, dict)
            or expected.get("path") != path.relative_to(root).as_posix()
            or expected.get("sha256") != digest(path)
        ):
            issues.append(f"recovery receipt archive binding changed: {name}")
    return issues


def _clean_worktree() -> bool:
    result = subprocess.run(  # nosec B603 B607 - fixed list-form Git status inspection
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=PROJECT_ROOT,
        env=clean_git_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and not result.stdout.strip()


def _run_pr_audit(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(  # nosec B603 - caller constructs only the fixed PR-audit argv
        command,
        cwd=PROJECT_ROOT,
        env=clean_git_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--authority", required=True)
    parser.add_argument("--recovery-path", action="append", default=[])
    args = parser.parse_args()
    try:
        receipt = open_post_archive_recovery(
            root=PROJECT_ROOT,
            task=args.task,
            base_commit=args.base,
            issue=args.issue,
            authority=args.authority,
            recovery_paths=args.recovery_path,
            run_pr_audit=_run_pr_audit,
            worktree_clean=_clean_worktree,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
