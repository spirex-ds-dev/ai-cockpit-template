#!/usr/bin/env python3
"""Validate a narrowly bounded provider merge-state inconsistency.

This command is deliberately separate from ``ai-close-work-item``.  It never
deletes a branch, changes a pull request, or treats an ordinary open pull
request as merged.  It only validates independently captured evidence and
produces a truthful recovery receipt for a later, explicitly authorized human
recovery decision.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class RecoveryEvidenceError(ValueError):
    """Evidence is insufficient for the exceptional recovery boundary."""


def _sha(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value.lower())
    ):
        raise RecoveryEvidenceError(f"{label} must be a 40-character Git SHA")
    return value


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RecoveryEvidenceError(f"{label} must be an object")
    return value


@dataclass(frozen=True)
class RecoveryResult:
    task: str
    pull_request_url: str
    pull_request_number: int
    provider_state: str
    work_branch: str
    work_head: str
    base_remote: str
    base_branch: str
    base_head: str
    merge_commit: str
    required_jobs: tuple[str, ...]


def validate_recovery_evidence(
    evidence: dict[str, object], *, human_confirmed: bool
) -> RecoveryResult:
    """Require all independent facts for a provider-partial-merge anomaly."""
    if not human_confirmed:
        raise RecoveryEvidenceError(
            "explicit human confirmation is required for recovery assessment"
        )
    task = evidence.get("task")
    if not isinstance(task, str) or not task:
        raise RecoveryEvidenceError("task must be a non-empty string")
    pr = _object(evidence.get("pullRequest"), "pullRequest")
    state = pr.get("state")
    if state != "OPEN":
        raise RecoveryEvidenceError("provider state OPEN is required for exceptional recovery")
    if pr.get("mergedAt") is not None or pr.get("mergeCommit") is not None:
        raise RecoveryEvidenceError("provider OPEN state cannot include normal merge facts")
    number = pr.get("number")
    url = pr.get("url")
    branch = pr.get("headRefName")
    if not isinstance(number, int) or number <= 0:
        raise RecoveryEvidenceError("pull request number must be a positive integer")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RecoveryEvidenceError("pull request URL must be an https URL")
    if not isinstance(branch, str) or not branch:
        raise RecoveryEvidenceError("pull request head branch must be non-empty")
    work_head = _sha(pr.get("headRefOid"), "pull request Head SHA")

    base = _object(evidence.get("base"), "base")
    remote = base.get("remote")
    base_branch = base.get("branch")
    if not isinstance(remote, str) or not remote:
        raise RecoveryEvidenceError("base remote must be non-empty")
    if not isinstance(base_branch, str) or not base_branch:
        raise RecoveryEvidenceError("base branch must be non-empty")
    base_head = _sha(base.get("observedHead"), "observed base Head SHA")

    merge = _object(evidence.get("mergeCommit"), "mergeCommit")
    merge_commit = _sha(merge.get("oid"), "merge commit SHA")
    parents = merge.get("parents")
    if not isinstance(parents, list) or len(parents) != 2:
        raise RecoveryEvidenceError("merge commit must have exactly two parents")
    parent_base = _sha(parents[0], "merge first parent")
    parent_head = _sha(parents[1], "merge second parent")
    if parent_base != base_head or parent_head != work_head:
        raise RecoveryEvidenceError(
            "merge parent order must be [observed base Head SHA, pull request Head SHA]"
        )
    if merge.get("reachableOnBase") is not True:
        raise RecoveryEvidenceError("merge commit is not reachable on the observed base")
    verification = _object(merge.get("githubVerification"), "merge GitHub verification")
    if verification.get("verified") is not True or verification.get("reason") != "valid":
        raise RecoveryEvidenceError(
            "merge commit requires GitHub-verified valid signature evidence"
        )

    hosted = _object(evidence.get("hostedEvidence"), "hostedEvidence")
    if _sha(hosted.get("headSha"), "hosted evidence Head SHA") != work_head:
        raise RecoveryEvidenceError("hosted evidence Head SHA does not match pull request Head SHA")
    required = hosted.get("requiredJobs")
    jobs = hosted.get("jobs")
    if (
        not isinstance(required, list)
        or not required
        or not all(isinstance(name, str) and name for name in required)
    ):
        raise RecoveryEvidenceError("hosted requiredJobs must be a non-empty string list")
    if len(set(required)) != len(required):
        raise RecoveryEvidenceError("hosted requiredJobs must not contain duplicates")
    if not isinstance(jobs, list):
        raise RecoveryEvidenceError("hosted jobs must be a list")
    conclusions: dict[str, str] = {}
    for job in jobs:
        if not isinstance(job, dict):
            raise RecoveryEvidenceError("hosted job must be an object")
        name = job.get("name")
        conclusion = job.get("conclusion")
        if not isinstance(name, str) or not isinstance(conclusion, str):
            raise RecoveryEvidenceError("hosted job requires name and conclusion")
        conclusions[name] = conclusion
    for name in required:
        if name not in conclusions:
            raise RecoveryEvidenceError(f"hosted evidence is missing required job: {name}")
        if conclusions[name] != "success":
            raise RecoveryEvidenceError(f"hosted required job did not succeed: {name}")
    return RecoveryResult(
        task=task,
        pull_request_url=url,
        pull_request_number=number,
        provider_state=state,
        work_branch=branch,
        work_head=work_head,
        base_remote=remote,
        base_branch=base_branch,
        base_head=base_head,
        merge_commit=merge_commit,
        required_jobs=tuple(required),
    )


def render_recovery_receipt(result: RecoveryResult) -> str:
    """Render a receipt that cannot be mistaken for normal merged-PR closure."""
    jobs = ", ".join(f"`{name}`" for name in result.required_jobs)
    return "\n".join(
        [
            f"# Provider Merge-State Recovery Assessment: {result.task}",
            "",
            "## Observed inconsistency",
            f"- Pull Request: {result.pull_request_url} (#{result.pull_request_number})",
            f"- Provider PR state observed: `{result.provider_state}`",
            "- Normal mergedAt: `unavailable`",
            "- Normal mergeCommit: `unavailable`",
            f"- Work branch / Head: `{result.work_branch}` / `{result.work_head}`",
            f"- GitHub-verified merge commit: `{result.merge_commit}`",
            f"- Base evidence: `{result.base_remote}/{result.base_branch}` parent `{result.base_head}`",
            f"- Required hosted jobs bound to Head: {jobs}",
            "",
            "## Boundary",
            "This is not normal PR-merged closure evidence.",
            "This assessment performs no provider mutation or branch cleanup. A later recovery action",
            "requires its own explicit human decision and must retain this receipt as evidence.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--human-confirmed", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        if not isinstance(evidence, dict):
            raise RecoveryEvidenceError("evidence root must be an object")
        result = validate_recovery_evidence(evidence, human_confirmed=args.human_confirmed)
        receipt = render_recovery_receipt(result)
    except (OSError, json.JSONDecodeError, RecoveryEvidenceError) as exc:
        print(f"Provider merge-state recovery: blocked\nReason: {exc}")
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(receipt, encoding="utf-8")
        print(f"Provider merge-state recovery receipt: {args.output}")
    else:
        print(receipt, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
