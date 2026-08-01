#!/usr/bin/env python3
"""Collect a truthful, read-only GitHub provider-governance receipt.

The command obtains its facts only through ``gh api``.  It never changes
repository configuration and represents unavailable provider data explicitly.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STATES = {
    "provider_verified",
    "repository_recorded_only",
    "local_provider_simulation",
    "not_run",
    "not_claimed",
}
CAPABILITIES = (
    "pr_creation",
    "required_checks",
    "branch_protection",
    "codeowners",
    "review_approval",
    "merge",
    "merge_sha",
    "remote_branch_cleanup",
    "tag",
    "release",
    "release_asset",
    "provider_identity",
    "provider_audit_evidence",
)
SHA_CAPABILITIES = {
    "pr_creation",
    "required_checks",
    "merge",
    "merge_sha",
    "remote_branch_cleanup",
    "tag",
    "release",
    "release_asset",
}


class ProviderUnavailable(RuntimeError):
    """The provider did not expose a requested resource."""


class GitHubClient:
    """Small read-only GitHub API adapter used by the live command."""

    def get(self, path: str) -> Any:
        completed = subprocess.run(  # nosec: fixed read-only gh argv
            ["gh", "api", path],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            message = (
                completed.stderr.strip() or completed.stdout.strip() or "GitHub API unavailable"
            )
            raise ProviderUnavailable(message)
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ProviderUnavailable(f"GitHub API returned invalid JSON: {exc}") from exc


def observed_at() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def entry(
    capability: str,
    state: str,
    observed: str,
    *,
    resource_id: str | None = None,
    sha: str | None = None,
    asset_digest: str | None = None,
    reason: str | None = None,
) -> dict[str, str]:
    if state not in STATES:
        raise ValueError(f"unsupported evidence state: {state}")
    result = {"capability": capability, "state": state, "observedAt": observed}
    if resource_id:
        result["resourceId"] = resource_id
    if sha:
        result["sha"] = sha
    if asset_digest:
        result["assetDigest"] = asset_digest
    if reason:
        result["reason"] = reason
    return result


def unavailable(
    capability: str, observed: str, exc: Exception, *, state: str = "not_run"
) -> dict[str, str]:
    return entry(capability, state, observed, reason=str(exc))


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProviderUnavailable(f"{label} was not an object")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProviderUnavailable(f"{label} was missing")
    return value


def resolve_tag_sha(client: Any, repository: str, tag: str) -> str:
    ref = require_object(client.get(f"repos/{repository}/git/ref/tags/{tag}"), "tag ref")
    target = require_object(ref.get("object"), "tag ref object")
    sha = require_text(target.get("sha"), "tag ref SHA")
    if target.get("type") == "tag":
        annotated = require_object(
            client.get(f"repos/{repository}/git/tags/{sha}"), "annotated tag"
        )
        return require_text(
            require_object(annotated.get("object"), "annotated tag object").get("sha"),
            "tag target SHA",
        )
    return sha


def collect_receipt(client: Any, *, repository: str, pr_number: int, tag: str) -> dict[str, Any]:
    """Collect one complete route; absence is evidence, never a successful claim."""
    observed = observed_at()
    facts: list[dict[str, str]] = []
    pr: dict[str, Any] | None = None
    head_sha = ""
    branch = ""
    try:
        pr = require_object(client.get(f"repos/{repository}/pulls/{pr_number}"), "pull request")
        head = require_object(pr.get("head"), "pull request head")
        head_sha = require_text(head.get("sha"), "pull request head SHA")
        branch = require_text(head.get("ref"), "pull request head branch")
        facts.append(
            entry(
                "pr_creation",
                "provider_verified",
                observed,
                resource_id=f"pull_request:{pr['id']}",
                sha=head_sha,
            )
        )
        if pr.get("merged") is True:
            merge_sha = require_text(pr.get("merge_commit_sha"), "merge commit SHA")
            facts.append(
                entry(
                    "merge",
                    "provider_verified",
                    observed,
                    resource_id=f"pull_request:{pr['id']}",
                    sha=merge_sha,
                )
            )
            facts.append(
                entry(
                    "merge_sha",
                    "provider_verified",
                    observed,
                    resource_id=f"merge_commit:{merge_sha}",
                    sha=merge_sha,
                )
            )
        else:
            facts.extend(
                [
                    entry("merge", "not_claimed", observed, reason="provider PR is not merged"),
                    entry(
                        "merge_sha",
                        "not_claimed",
                        observed,
                        reason="provider PR has no merged commit SHA",
                    ),
                ]
            )
    except ProviderUnavailable as exc:
        facts.extend(
            [
                unavailable("pr_creation", observed, exc),
                unavailable("merge", observed, exc),
                unavailable("merge_sha", observed, exc),
            ]
        )

    try:
        protection = require_object(
            client.get(f"repos/{repository}/branches/main/protection"), "branch protection"
        )
        facts.append(
            entry(
                "branch_protection",
                "provider_verified",
                observed,
                resource_id="branch_protection:main",
                sha=head_sha or None,
            )
        )
        required = protection.get("required_status_checks")
        if isinstance(required, dict) and required.get("contexts"):
            facts.append(
                entry(
                    "required_checks",
                    "provider_verified",
                    observed,
                    resource_id="required_status_checks:main",
                    sha=head_sha or None,
                )
            )
        else:
            facts.append(
                entry(
                    "required_checks",
                    "not_claimed",
                    observed,
                    reason="provider branch protection has no required status-check contexts",
                )
            )
    except ProviderUnavailable as exc:
        facts.append(unavailable("branch_protection", observed, exc))
        facts.append(unavailable("required_checks", observed, exc, state="not_claimed"))

    try:
        codeowners = require_object(
            client.get(f"repos/{repository}/contents/CODEOWNERS"), "CODEOWNERS"
        )
        facts.append(
            entry(
                "codeowners",
                "provider_verified",
                observed,
                resource_id=f"contents:CODEOWNERS:{require_text(codeowners.get('sha'), 'CODEOWNERS SHA')}",
                sha=head_sha or None,
            )
        )
    except ProviderUnavailable as exc:
        facts.append(unavailable("codeowners", observed, exc))

    try:
        reviews = client.get(f"repos/{repository}/pulls/{pr_number}/reviews")
        if not isinstance(reviews, list):
            raise ProviderUnavailable("review list was not an array")
        approved = next(
            (
                review
                for review in reviews
                if isinstance(review, dict) and review.get("state") == "APPROVED"
            ),
            None,
        )
        if approved is None:
            facts.append(
                entry(
                    "review_approval",
                    "not_claimed",
                    observed,
                    reason="provider returned no APPROVED review",
                )
            )
        else:
            review_id = require_text(str(approved.get("id")), "review ID")
            facts.append(
                entry(
                    "review_approval",
                    "provider_verified",
                    observed,
                    resource_id=f"review:{review_id}",
                    sha=head_sha or None,
                )
            )
    except ProviderUnavailable as exc:
        facts.append(unavailable("review_approval", observed, exc, state="not_claimed"))

    try:
        runs = require_object(
            client.get(f"repos/{repository}/commits/{head_sha}/check-runs"), "check runs"
        )
        complete = [
            run
            for run in runs.get("check_runs", [])
            if isinstance(run, dict) and run.get("conclusion") == "success"
        ]
        if complete:
            facts.append(
                entry(
                    "provider_audit_evidence",
                    "provider_verified",
                    observed,
                    resource_id=f"check_run:{complete[0]['id']}",
                    sha=head_sha,
                )
            )
        else:
            facts.append(
                entry(
                    "provider_audit_evidence",
                    "not_claimed",
                    observed,
                    reason="provider returned no successful check run",
                )
            )
    except ProviderUnavailable as exc:
        facts.append(unavailable("provider_audit_evidence", observed, exc))

    try:
        client.get(f"repos/{repository}/git/ref/heads/{branch}")
        facts.append(
            entry(
                "remote_branch_cleanup",
                "not_claimed",
                observed,
                reason="provider still exposes the pull request head branch",
            )
        )
    except ProviderUnavailable as exc:
        facts.append(
            entry(
                "remote_branch_cleanup",
                "provider_verified",
                observed,
                resource_id=f"git_ref_absent:heads/{branch}",
                sha=head_sha or None,
                reason=str(exc),
            )
        )

    tag_sha = ""
    try:
        tag_sha = resolve_tag_sha(client, repository, tag)
        facts.append(
            entry(
                "tag", "provider_verified", observed, resource_id=f"git_ref:tags/{tag}", sha=tag_sha
            )
        )
    except ProviderUnavailable as exc:
        facts.append(unavailable("tag", observed, exc))
    try:
        release = require_object(client.get(f"repos/{repository}/releases/tags/{tag}"), "release")
        release_id = require_text(str(release.get("id")), "release ID")
        facts.append(
            entry(
                "release",
                "provider_verified",
                observed,
                resource_id=f"release:{release_id}",
                sha=tag_sha or None,
            )
        )
        assets = release.get("assets")
        asset = (
            next((item for item in assets if isinstance(item, dict) and item.get("digest")), None)
            if isinstance(assets, list)
            else None
        )
        if asset is None:
            facts.append(
                entry(
                    "release_asset",
                    "not_claimed",
                    observed,
                    reason="provider release has no asset digest",
                )
            )
        else:
            asset_id = require_text(str(asset.get("id")), "release asset ID")
            facts.append(
                entry(
                    "release_asset",
                    "provider_verified",
                    observed,
                    resource_id=f"release_asset:{asset_id}",
                    sha=tag_sha or None,
                    asset_digest=require_text(asset.get("digest"), "release asset digest"),
                )
            )
    except ProviderUnavailable as exc:
        facts.extend(
            [
                unavailable("release", observed, exc),
                unavailable("release_asset", observed, exc, state="not_claimed"),
            ]
        )

    try:
        user = require_object(client.get("user"), "provider identity")
        facts.append(
            entry(
                "provider_identity",
                "provider_verified",
                observed,
                resource_id=f"github_user:{require_text(str(user.get('id')), 'provider user ID')}",
            )
        )
    except ProviderUnavailable as exc:
        facts.append(unavailable("provider_identity", observed, exc))
    receipt = {
        "schemaVersion": 1,
        "provider": "github",
        "repository": repository,
        "pullRequest": pr_number,
        "tag": tag,
        "observedAt": observed,
        "facts": facts,
    }
    validate_receipt(receipt)
    return receipt


def validate_receipt(receipt: dict[str, Any]) -> None:
    facts = receipt.get("facts")
    if not isinstance(facts, list) or {
        item.get("capability") for item in facts if isinstance(item, dict)
    } != set(CAPABILITIES):
        raise ValueError("receipt must contain exactly one fact for every required capability")
    for item in facts:
        if (
            not isinstance(item, dict)
            or item.get("state") not in STATES
            or not item.get("observedAt")
        ):
            raise ValueError("receipt facts require a known state and observation time")
        if item["state"] == "provider_verified":
            if not item.get("resourceId"):
                raise ValueError(
                    f"provider_verified {item['capability']} requires provider resource ID"
                )
            if item["capability"] in SHA_CAPABILITIES and not item.get("sha"):
                raise ValueError(f"provider_verified {item['capability']} requires applicable SHA")
            if item["capability"] == "release_asset" and not item.get("assetDigest"):
                raise ValueError("provider_verified release_asset requires provider asset digest")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = collect_receipt(
            GitHubClient(), repository=args.repository, pr_number=args.pull_request, tag=args.tag
        )
    except (ProviderUnavailable, ValueError) as exc:
        print(f"provider-backed validation: blocked: {exc}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"provider-backed receipt: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
