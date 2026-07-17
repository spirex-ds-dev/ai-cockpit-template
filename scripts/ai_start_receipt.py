"""Create and validate immutable Work Item Start Receipts."""

from __future__ import annotations

import hashlib
import json
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECEIPTS_DIR = PROJECT_ROOT / ".ai" / "work-items" / "starts"
RECEIPT_SCHEMA_VERSION = 1
RECEIPT_PREFIX = ".ai/work-items/starts/"


def receipt_path(work_item_id: str, *, project_root: Path = PROJECT_ROOT) -> Path:
    return project_root / ".ai" / "work-items" / "starts" / f"{work_item_id}.json"


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def scope_digest(scope: list[str]) -> str:
    return _digest(scope)


def skeleton_digest(contract: dict[str, Any]) -> str:
    """Digest fields established by ai-start and stable for later contract edits."""
    stable = {
        key: contract.get(key)
        for key in ("contractVersion", "workItemId", "mode", "title", "baseCommit")
    }
    return _digest(stable)


def current_branch(*, project_root: Path = PROJECT_ROOT) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_receipt(
    contract: dict[str, Any],
    *,
    timestamp: str | None = None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    work_item_id = contract.get("workItemId")
    scope = contract.get("scope")
    base_commit = contract.get("baseCommit")
    if not isinstance(work_item_id, str) or not work_item_id:
        raise ValueError("Contract workItemId is required for a Start Receipt")
    if not isinstance(scope, list) or not all(isinstance(item, str) for item in scope):
        raise ValueError("Contract scope must be a string list for a Start Receipt")
    if not isinstance(base_commit, str) or not base_commit:
        raise ValueError("Contract baseCommit is required for a Start Receipt")
    return {
        "receiptVersion": RECEIPT_SCHEMA_VERSION,
        "workItemId": work_item_id,
        "receiptPath": f"{RECEIPT_PREFIX}{work_item_id}.json",
        "baseCommit": base_commit,
        "baseBranch": current_branch(project_root=project_root),
        "startTimestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "initialScopeDigest": scope_digest(scope),
        "contractSkeletonDigest": skeleton_digest(contract),
    }


def receipt_binding(receipt: dict[str, Any]) -> dict[str, str]:
    return {
        "path": str(receipt["receiptPath"]),
        "baseCommit": str(receipt["baseCommit"]),
        "initialScopeDigest": str(receipt["initialScopeDigest"]),
        "contractSkeletonDigest": str(receipt["contractSkeletonDigest"]),
    }


def validate_receipt(
    contract: dict[str, Any],
    receipt: dict[str, Any] | None,
    *,
    project_root: Path = PROJECT_ROOT,
    require_tracked: bool = False,
) -> list[str]:
    """Return fail-closed issues for a receipt and its Contract binding."""
    issues: list[str] = []
    if receipt is None:
        return ["Start Receipt is missing"]
    required = (
        "receiptVersion",
        "workItemId",
        "receiptPath",
        "baseCommit",
        "startTimestamp",
        "initialScopeDigest",
        "contractSkeletonDigest",
    )
    for key in required:
        if key not in receipt:
            issues.append(f"Start Receipt missing field: {key}")
    if issues:
        return issues
    if receipt.get("receiptVersion") != RECEIPT_SCHEMA_VERSION:
        issues.append("Start Receipt receiptVersion is unsupported")
    work_item_id = contract.get("workItemId")
    if receipt.get("workItemId") != work_item_id:
        issues.append("Start Receipt workItemId does not match Contract")
    expected_path = f"{RECEIPT_PREFIX}{work_item_id}.json"
    if receipt.get("receiptPath") != expected_path:
        issues.append("Start Receipt receiptPath is not the canonical repository-relative path")
    if receipt.get("baseCommit") != contract.get("baseCommit"):
        issues.append("Start Receipt baseCommit does not match Contract")
    try:
        datetime.fromisoformat(str(receipt["startTimestamp"]))
    except ValueError:
        issues.append("Start Receipt startTimestamp is not ISO-8601")
    if (
        not isinstance(receipt.get("initialScopeDigest"), str)
        or len(receipt["initialScopeDigest"]) != 64
    ):
        issues.append("Start Receipt initialScopeDigest must be a SHA-256 digest")
    if (
        not isinstance(receipt.get("contractSkeletonDigest"), str)
        or len(receipt["contractSkeletonDigest"]) != 64
    ):
        issues.append("Start Receipt contractSkeletonDigest must be a SHA-256 digest")
    binding = contract.get("startReceipt")
    if not isinstance(binding, dict):
        issues.append("Contract startReceipt binding is missing")
    elif binding != receipt_binding(receipt):
        issues.append("Contract startReceipt binding does not match Receipt")
    if require_tracked:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(receipt["receiptPath"])],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            issues.append("Start Receipt is not Git-tracked")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Work Item Start Receipt.")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--receipt")
    args = parser.parse_args()
    contract_path = PROJECT_ROOT / args.contract
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Start Receipt check failed: {exc}")
        return 1
    path = PROJECT_ROOT / args.receipt if args.receipt else receipt_path(contract["workItemId"])
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        receipt = None
    issues = validate_receipt(contract, receipt, require_tracked=True)
    if issues:
        for issue in issues:
            print(f"[ERROR] {issue}")
        return 1
    print(f"Start Receipt check passed: {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
