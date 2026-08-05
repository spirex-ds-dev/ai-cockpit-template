#!/usr/bin/env python3
"""Classify Dependabot source facts without mutating a provider."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_EVIDENCE = [
    "current_main_work_item_contract",
    "current_main_start_receipt",
    "current_main_change_summary",
    "current_main_task_outcome",
    "current_main_archive_manifest",
    "source_pull_request_url_head_and_diff_digest_binding",
]


class IntakeError(ValueError):
    """A candidate has no trusted structured classification facts."""


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IntakeError(f"{label} must be non-empty text")
    return value.strip()


def source_binding(candidate: dict[str, Any]) -> dict[str, str]:
    pull_request = candidate.get("pullRequest")
    if not isinstance(pull_request, dict):
        raise IntakeError("pullRequest must be an object")
    url = _text(pull_request.get("url"), "pullRequest.url")
    head = _text(pull_request.get("head"), "pullRequest.head").lower()
    digest = _text(candidate.get("diffDigest"), "diffDigest").lower()
    if not url.startswith("https://"):
        raise IntakeError("pullRequest.url must be an https URL")
    if not SHA1.fullmatch(head):
        raise IntakeError("pullRequest.head must be a 40-character Git SHA")
    if not SHA256.fullmatch(digest):
        raise IntakeError("diffDigest must be a SHA-256 digest")
    return {"pullRequestUrl": url, "head": head, "diffDigest": digest}


def classification(paths: object) -> str:
    if not isinstance(paths, list) or not paths or any(not isinstance(path, str) for path in paths):
        raise IntakeError("changedPaths must be a non-empty path list")
    if any(
        path.startswith("requirements") or path in {"pyproject.toml", "uv.lock"} for path in paths
    ):
        return "locked_dependency"
    if any(path.startswith(".github/workflows/") for path in paths):
        return "pinned_github_action"
    return "other_dependabot_change"


def successor_is_bound(successor: object, binding: dict[str, str]) -> bool:
    if not isinstance(successor, dict):
        return False
    archive_fields = ("contract", "startReceipt", "summary", "outcome", "archiveManifest")
    return (
        successor.get("base") == "current-main"
        and all(successor.get(field) == "archived" for field in archive_fields)
        and isinstance(successor.get("workItemId"), str)
        and bool(successor["workItemId"])
        and isinstance(successor.get("branch"), str)
        and successor["branch"].startswith("codex/")
        and successor.get("source") == binding
    )


def assess(candidate: dict[str, Any], successor: object | None = None) -> dict[str, object]:
    """Return an evidence-only intake decision; never authorizes a merge."""
    if candidate.get("provider") != "github" or candidate.get("author") != "dependabot[bot]":
        return {"state": "not_applicable", "automaticMergeAuthorized": False}
    binding = source_binding(candidate)
    category = classification(candidate.get("changedPaths"))
    result: dict[str, object] = {
        "classification": category,
        "sourceBinding": binding,
        "automaticMergeAuthorized": False,
    }
    if category in {"locked_dependency", "pinned_github_action"} and successor_is_bound(
        successor, binding
    ):
        return {**result, "state": "eligible_for_current_main_successor"}
    if category in {"locked_dependency", "pinned_github_action"}:
        return {
            **result,
            "state": "blocked",
            "reason": "governed_successor_archive_required",
            "requiredEvidence": REQUIRED_EVIDENCE,
        }
    return {
        **result,
        "state": "blocked",
        "reason": "unsupported_dependabot_change_requires_explicit_maintainer_disposition",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--successor-evidence", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        if not isinstance(candidate, dict):
            raise IntakeError("candidate must be an object")
        successor = (
            json.loads(args.successor_evidence.read_text(encoding="utf-8"))
            if args.successor_evidence
            else None
        )
        result = assess(candidate, successor)
    except (OSError, json.JSONDecodeError, IntakeError) as exc:
        result = {"state": "blocked", "reason": str(exc), "automaticMergeAuthorized": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"not_applicable", "eligible_for_current_main_successor"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
