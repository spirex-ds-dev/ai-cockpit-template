#!/usr/bin/env python3
"""Append a source-bound baseline transition to a paused Work Item Contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_start_receipt import (
    PROJECT_ROOT,
    RESUME_SCHEMA_VERSION,
    predecessor_closure_snapshot,
    receipt_path,
    validate_receipt,
    validate_resume_history,
    work_branch_identifies_work_item,
)


class ResumeError(ValueError):
    """Raised when a Work Item baseline transition cannot be trusted."""


def _load_json(path: Path, description: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ResumeError(f"{description} cannot be read: {exc}") from exc
    if not isinstance(value, dict):
        raise ResumeError(f"{description} must be a JSON object")
    return value


def _git(project_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise ResumeError(detail)
    return result.stdout.strip()


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _predecessor_transition_fields(contract: dict[str, Any], target: str) -> dict[str, Any]:
    predecessor = contract.get("predecessorWorkItem")
    if not isinstance(predecessor, dict):
        raise ResumeError("predecessorWorkItem must be an evidence object")
    snapshot = predecessor_closure_snapshot(predecessor)
    failed = [field for field, value in snapshot.items() if value is not True]
    if failed:
        if "statusClosed" in failed:
            raise ResumeError("predecessor status must be closed")
        raise ResumeError(f"predecessor closure is incomplete: {', '.join(failed)}")
    work_item_id = predecessor.get("workItemId")
    if not isinstance(work_item_id, str) or not work_item_id:
        raise ResumeError("predecessor Work Item ID is missing")
    pr = predecessor.get("pr")
    merge_commit = pr.get("mergeCommit") if isinstance(pr, dict) else None
    if merge_commit != target:
        raise ResumeError("predecessor merge commit must equal resume target")
    closure = predecessor.get("closure")
    manifest = closure.get("evidence") if isinstance(closure, dict) else None
    if not isinstance(manifest, str) or not manifest:
        raise ResumeError("predecessor archive manifest path is missing")
    return {
        "predecessorWorkItemId": work_item_id,
        "predecessorMergeCommit": merge_commit,
        "predecessorManifestPath": manifest,
        "predecessorClosure": snapshot,
    }


def resume_contract(
    contract_path: Path,
    *,
    base_remote: str,
    base_branch: str,
    timestamp: str | None = None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Validate live repository facts, append one transition, and atomically write."""
    contract_path = contract_path.resolve()
    project_root = project_root.resolve()
    try:
        contract_path.relative_to(project_root)
    except ValueError as exc:
        raise ResumeError("Contract must be inside the repository") from exc
    original_bytes = contract_path.read_bytes()
    contract = _load_json(contract_path, "Contract")
    work_item_id = contract.get("workItemId")
    if not isinstance(work_item_id, str) or not work_item_id:
        raise ResumeError("Contract workItemId is missing")
    receipt_file = receipt_path(work_item_id, project_root=project_root)
    receipt = _load_json(receipt_file, "Start Receipt")
    current_issues = validate_receipt(
        contract,
        receipt,
        project_root=project_root,
        require_latest_predecessor=False,
    )
    if current_issues:
        raise ResumeError("current Work Item evidence is invalid: " + "; ".join(current_issues))

    work_branch = _git(project_root, "branch", "--show-current")
    if not work_branch:
        raise ResumeError("resume requires a checked-out dedicated Work Item branch")
    if work_branch == base_branch:
        raise ResumeError("resume requires a dedicated non-base Work Item branch")
    receipt_branch = receipt.get("baseBranch")
    history = contract.get("resumeHistory")
    if isinstance(history, list) and history:
        first_transition = history[0]
        first_work_branch = (
            first_transition.get("workBranch") if isinstance(first_transition, dict) else None
        )
        if first_work_branch != work_branch:
            raise ResumeError("current branch does not match the first resume transition")
    if isinstance(receipt_branch, str) and receipt_branch:
        if receipt_branch == base_branch:
            if not work_branch_identifies_work_item(work_branch, work_item_id):
                raise ResumeError("compatibility work branch does not identify this Work Item")
        elif receipt_branch != work_branch:
            raise ResumeError("current branch does not match immutable Start Receipt")
    target_ref = f"refs/remotes/{base_remote}/{base_branch}"
    target = _git(project_root, "rev-parse", "--verify", target_ref)
    head = _git(project_root, "rev-parse", "HEAD")
    from_base = str(contract.get("baseCommit", ""))
    if not from_base:
        raise ResumeError("Contract baseCommit is missing")
    if from_base == target:
        raise ResumeError("Work Item is already based on the remote default branch")
    try:
        _git(project_root, "merge-base", "--is-ancestor", from_base, target)
    except ResumeError as exc:
        raise ResumeError(
            "current Contract baseCommit is not an ancestor of resume target"
        ) from exc
    try:
        _git(project_root, "merge-base", "--is-ancestor", target, head)
    except ResumeError as exc:
        raise ResumeError("Work Item branch is not rebased onto the resume target") from exc

    predecessor_fields = _predecessor_transition_fields(contract, target)
    transition = {
        "resumeVersion": RESUME_SCHEMA_VERSION,
        "fromBaseCommit": from_base,
        "toBaseCommit": target,
        "baseRemote": base_remote,
        "baseBranch": base_branch,
        "workBranch": work_branch,
        "recordedAt": timestamp or datetime.now(UTC).isoformat(),
        "priorContractDigest": hashlib.sha256(original_bytes).hexdigest(),
        **predecessor_fields,
    }
    candidate = dict(contract)
    history = contract.get("resumeHistory", [])
    if not isinstance(history, list):
        raise ResumeError("existing resumeHistory must be an array")
    candidate["resumeHistory"] = [*history, transition]
    candidate["baseCommit"] = target
    candidate_issues = validate_resume_history(candidate, receipt, project_root=project_root)
    if candidate_issues:
        raise ResumeError("resume transition is invalid: " + "; ".join(candidate_issues))

    _atomic_write_json(contract_path, candidate)
    return transition


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume a paused governed Work Item.")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--base-remote", required=True)
    parser.add_argument("--base-branch", required=True)
    args = parser.parse_args()
    try:
        transition = resume_contract(
            PROJECT_ROOT / args.contract,
            base_remote=args.base_remote,
            base_branch=args.base_branch,
            project_root=PROJECT_ROOT,
        )
    except (OSError, ResumeError) as exc:
        print(f"[ERROR] Work Item resume failed: {exc}")
        return 1
    print(
        f"Work Item resume recorded: {transition['fromBaseCommit']} -> {transition['toBaseCommit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
