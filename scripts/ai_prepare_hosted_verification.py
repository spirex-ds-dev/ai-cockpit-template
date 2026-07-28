#!/usr/bin/env python3
"""Validate a committed pre-finish snapshot for required hosted verification."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess  # nosec B404 - every executable and argument list is fixed below
import sys
from typing import Any


class HostedVerificationError(ValueError):
    """A hosted-verification snapshot does not satisfy the narrow lifecycle boundary."""


def load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HostedVerificationError(f"cannot read JSON evidence: {path}") from exc
    if not isinstance(payload, dict):
        raise HostedVerificationError(f"JSON evidence must be an object: {path}")
    return payload


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and key != "AI_BASE_COMMIT"
    }


def git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(  # nosec B603 B607
        ["git", *args],
        cwd=root,
        env=git_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise HostedVerificationError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def active_summary_path(contract_path: Path) -> Path:
    if not contract_path.name.endswith(".contract.json"):
        raise HostedVerificationError("Contract path must end with .contract.json")
    return contract_path.with_name(contract_path.name.replace(".contract.json", ".summary.json"))


def validate_hosted_requirement(contract: dict[str, Any], summary: dict[str, Any]) -> None:
    acceptance = contract.get("acceptance")
    if not isinstance(acceptance, list) or not any(
        isinstance(item, str) and "hosted" in item.casefold() for item in acceptance
    ):
        raise HostedVerificationError("Contract does not explicitly require hosted verification")
    risk = contract.get("riskAssessment")
    risk_types = risk.get("riskTypes", []) if isinstance(risk, dict) else []
    if not isinstance(risk_types, list) or not {
        "performance_evidence",
        "hosted_verification",
    }.intersection(risk_types):
        raise HostedVerificationError("Contract risk does not declare hosted evidence")

    evidence = summary.get("hostedPerformanceEvidence")
    if not isinstance(evidence, dict):
        raise HostedVerificationError("Summary hosted performance evidence is missing")
    if evidence.get("status") == "complete":
        raise HostedVerificationError("hosted evidence is already complete")
    if evidence.get("status") not in {"not_run", "partial"}:
        raise HostedVerificationError("Summary hosted performance evidence status is invalid")
    scenarios = evidence.get("scenarios")
    pending = isinstance(scenarios, list) and any(
        isinstance(item, dict)
        and item.get("status") == "not_run"
        and isinstance(item.get("reason"), str)
        and bool(item["reason"].strip())
        for item in scenarios
    )
    if not pending:
        raise HostedVerificationError("Summary must contain a pending hosted scenario")


def validate_no_release_intent(contract: dict[str, Any]) -> None:
    operation = contract.get("requestedOperation")
    if not isinstance(operation, dict):
        raise HostedVerificationError("requestedOperation is required")
    target = str(operation.get("target", "")).casefold()
    action = str(operation.get("action", "")).casefold()
    if "release" in target or action in {"publish", "release", "deploy"}:
        raise HostedVerificationError("release or publication intent cannot use this snapshot")


def default_quality_runner(root: Path) -> dict[str, str]:
    inherited_make_state = {
        "AI_BASE_COMMIT",
        "CONTRACT",
        "GNUMAKEFLAGS",
        "MAKEFLAGS",
        "MAKEOVERRIDES",
        "MFLAGS",
        "SUMMARY",
        "TASK",
    }
    result = subprocess.run(  # nosec B603 B607
        ["make", "quality"],
        cwd=root,
        env={
            **{key: value for key, value in os.environ.items() if key not in inherited_make_state},
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        check=False,
    )
    if result.returncode != 0:
        return {"sessionId": "unknown", "decision": "FAIL", "summaryDigest": ""}
    pointer = root / "target" / "quality" / "current-session.txt"
    if not pointer.is_file():
        raise HostedVerificationError("local quality session pointer is missing")
    session_id = pointer.read_text(encoding="utf-8").strip()
    summary_path = root / "target" / "quality" / "sessions" / session_id / "summary.json"
    quality = load_object(summary_path)
    return {
        "sessionId": session_id,
        "decision": str(quality.get("decision", "")),
        "summaryDigest": f"sha256:{digest(summary_path)}",
    }


def prepare_snapshot(
    *,
    root: Path,
    contract_path: Path,
    output: Path,
    quality_runner: Callable[[Path], dict[str, str]] = default_quality_runner,
) -> dict[str, Any]:
    root = root.resolve()
    contract_path = contract_path.resolve()
    output = output.resolve()
    try:
        contract_path.relative_to(root / ".ai" / "work-items" / "active")
    except ValueError as exc:
        raise HostedVerificationError("Contract must be an active Work Item") from exc
    contract = load_object(contract_path)
    summary_path = active_summary_path(contract_path)
    summary = load_object(summary_path)
    work_item_id = contract.get("workItemId")
    if (
        contract.get("contractVersion") != 2
        or not isinstance(work_item_id, str)
        or not work_item_id
        or summary.get("workItemId") != work_item_id
    ):
        raise HostedVerificationError("Contract and Summary identity is invalid")

    archived = list(
        (root / ".ai" / "work-items" / "archive").glob(f"**/{work_item_id}.contract.json")
    )
    if archived:
        raise HostedVerificationError("Work Item is already archived")
    validate_hosted_requirement(contract, summary)
    validate_no_release_intent(contract)

    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if not branch:
        raise HostedVerificationError("detached HEAD cannot prepare a hosted snapshot")
    if branch in {"main", "master"}:
        raise HostedVerificationError("hosted snapshot requires a dedicated non-base branch")
    dirty = git(root, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise HostedVerificationError("worktree must be clean before hosted verification")

    head = git(root, "rev-parse", "HEAD")
    tree = git(root, "rev-parse", "HEAD^{tree}")
    base = contract.get("baseCommit")
    if not isinstance(base, str) or len(base) != 40:
        raise HostedVerificationError("Contract baseCommit is invalid")
    if head == base:
        raise HostedVerificationError("hosted snapshot must contain a committed implementation")
    ancestor = subprocess.run(  # nosec B603 B607
        ["git", "merge-base", "--is-ancestor", base, head],
        cwd=root,
        env=git_environment(),
        check=False,
    )
    if ancestor.returncode != 0:
        raise HostedVerificationError("Contract baseCommit is not an ancestor of HEAD")

    refs_before = git(root, "show-ref")
    quality = quality_runner(root)
    if quality.get("decision") != "PASS":
        raise HostedVerificationError("local quality did not pass")
    if not quality.get("sessionId") or not str(quality.get("summaryDigest", "")).startswith(
        "sha256:"
    ):
        raise HostedVerificationError("local quality evidence is incomplete")
    if git(root, "show-ref") != refs_before:
        raise HostedVerificationError("local quality mutated Git refs")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise HostedVerificationError("local quality left the worktree dirty")

    receipt: dict[str, Any] = {
        "schemaVersion": 1,
        "state": "hosted_verification_snapshot",
        "workItemId": work_item_id,
        "branch": branch,
        "baseCommit": base,
        "commitSha": head,
        "treeSha": tree,
        "contractPath": contract_path.relative_to(root).as_posix(),
        "contractDigest": digest(contract_path),
        "summaryPath": summary_path.relative_to(root).as_posix(),
        "summaryDigest": digest(summary_path),
        "quality": quality,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "onlyEligibleNextAction": "push_this_branch_for_hosted_verification_only",
        "authorizationClaim": "not_provided_by_receipt",
        "forbiddenActions": [
            "pull_request",
            "merge",
            "release",
            "archive_mutation",
            "work_item_closure",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("target/hosted-verification-snapshot.json"),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    contract = args.contract if args.contract.is_absolute() else root / args.contract
    output = args.output if args.output.is_absolute() else root / args.output
    try:
        receipt = prepare_snapshot(root=root, contract_path=contract, output=output)
    except HostedVerificationError as exc:
        print(f"[ERROR] hosted verification snapshot rejected: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
