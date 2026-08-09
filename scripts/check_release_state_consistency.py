#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

STATES = {"development", "candidate_prepared", "candidate_verified", "release_published"}
CANONICAL_SCHEMA_VERSION = 1
PROJECTION_FILES = {"published": "release.json", "candidate": "next-release.json"}
TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_STATUSES = {"not_started", "pending_provider_assets", "verified", "published"}


def load_object(path: Path, label: str, issues: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"{label} is not readable JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        issues.append(f"{label} must contain a JSON object")
        return {}
    return value


def sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def semver_key(tag: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag)
    if not match:
        raise ValueError(f"not a semantic-version tag: {tag!r}")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def is_next_patch(candidate: str, previous: str) -> bool:
    try:
        candidate_parts = semver_key(candidate)
        previous_parts = semver_key(previous)
    except ValueError:
        return False
    return candidate_parts[:2] == previous_parts[:2] and candidate_parts[2] == previous_parts[2] + 1


def check_ci_evidence(state: dict[str, Any], source_commit: Any, issues: list[str]) -> None:
    if state.get("state") not in {"candidate_verified", "release_published"}:
        return
    evidence = state.get("ciEvidence")
    if not isinstance(evidence, dict):
        issues.append("verified/published release state requires ciEvidence")
        return
    if (
        evidence.get("evidenceSource") not in {"github_api", "github_actions"}
        or not evidence.get("workflowRunId")
        or evidence.get("headSha") != source_commit
    ):
        issues.append("ciEvidence must be provider-bound and complete")


def check_repository(root: Path) -> list[str]:
    issues: list[str] = []
    state_path = root / "release-state.json"
    published_path = root / "release.json"
    candidate_path = root / "next-release.json"
    state = load_object(state_path, "release-state.json", issues)
    published = load_object(published_path, "release.json", issues)
    candidate = load_object(candidate_path, "next-release.json", issues)
    if state.get("schemaVersion") != CANONICAL_SCHEMA_VERSION:
        issues.append(
            "release-state.json schemaVersion must identify the canonical release-state schema"
        )
    if state.get("canonical") is not True:
        issues.append("release-state.json canonical marker must be true")
    if state.get("projections") != PROJECTION_FILES:
        issues.append(
            "release-state.json projections must map published/candidate to release.json/next-release.json"
        )
    state_name = state.get("state")
    if state_name not in STATES:
        issues.append(f"release-state.json state must be one of {sorted(STATES)}")
    state_tag = state.get("releaseTag")
    if not isinstance(state_tag, str) or not TAG_PATTERN.fullmatch(state_tag):
        issues.append("release-state.json releaseTag must be a semantic version tag")
    source_binding = state.get("sourceBinding")
    source_commit = state.get("sourceCommit")
    if state_name in {"development", "candidate_prepared"}:
        if source_binding != "deferred_to_release_finalization" or source_commit is not None:
            issues.append(f"{state_name} source binding must be deferred with null sourceCommit")
    elif (
        source_binding != "exact"
        or not isinstance(source_commit, str)
        or not SHA_PATTERN.fullmatch(source_commit)
    ):
        issues.append(
            f"{state_name} source binding must be exact with a 40-character lowercase SHA"
        )
    previous = state.get("previousRelease")
    if not isinstance(previous, str) or not TAG_PATTERN.fullmatch(previous):
        issues.append("release-state.json previousRelease must be a semantic version tag")
    reserved_tags = state.get("reservedTags")
    if not isinstance(reserved_tags, list) or any(
        not isinstance(tag, str) or not TAG_PATTERN.fullmatch(tag) for tag in reserved_tags
    ):
        issues.append("release-state.json reservedTags must be semantic-version strings")
        reserved_tags = []
    elif reserved_tags != sorted(set(reserved_tags), key=semver_key):
        issues.append("release-state.json reservedTags must be sorted unique")
    unavailable_tags = state.get("unavailableTags")
    unavailable_tag_names: list[str] = []
    if not isinstance(unavailable_tags, list):
        issues.append("release-state.json unavailableTags must be a list")
    else:
        for item in unavailable_tags:
            if not isinstance(item, dict):
                issues.append("release-state.json unavailableTags entries must be objects")
                continue
            tag_value = item.get("tag")
            unavailable_tag_names.append(tag_value if isinstance(tag_value, str) else "")
            if (
                not isinstance(tag_value, str)
                or not TAG_PATTERN.fullmatch(tag_value)
                or item.get("kind")
                not in {
                    "stable_release_invalid_public_distribution",
                    "stable_release_unverified",
                    "tag_only",
                }
                or not isinstance(item.get("reason"), str)
                or not item["reason"].strip()
                or not isinstance(item.get("evidence"), str)
                or not item["evidence"].strip()
            ):
                issues.append(
                    "release-state.json unavailableTags entries require tag, kind, reason, and evidence"
                )
        if set(unavailable_tag_names) != set(reserved_tags):
            issues.append("release-state.json unavailableTags must explain every reserved tag")
    evidence_status = state.get("evidenceStatus")
    if evidence_status not in EVIDENCE_STATUSES:
        issues.append(
            f"release-state.json evidenceStatus must be one of {sorted(EVIDENCE_STATUSES)}"
        )
    evidence_digest = state.get("evidenceBundleDigest")
    expected_status = {
        "development": "not_started",
        "candidate_prepared": "pending_provider_assets",
        "candidate_verified": "verified",
        "release_published": "published",
    }.get(state_name if isinstance(state_name, str) else "")
    digest_valid = isinstance(evidence_digest, str) and DIGEST_PATTERN.fullmatch(evidence_digest)
    if state_name in {"development", "candidate_prepared"}:
        if evidence_status != expected_status or evidence_digest is not None:
            issues.append(f"{state_name} must have {expected_status} evidence and null digest")
    elif state_name in {"candidate_verified", "release_published"} and (
        evidence_status != expected_status or not digest_valid
    ):
        issues.append(f"{state_name} must have {expected_status} evidence and a SHA-256 digest")
    check_ci_evidence(state, source_commit, issues)
    published_tag = published.get("releaseTag")
    candidate_tag = candidate.get("releaseTag")
    if state_name in {"candidate_prepared", "candidate_verified"} and state_tag != candidate_tag:
        issues.append(
            f"canonical candidate releaseTag {state_tag!r} disagrees with next-release.json {candidate_tag!r}"
        )
    if state_name == "release_published" and state_tag != published_tag:
        issues.append(
            f"canonical published releaseTag {state_tag!r} disagrees with release.json {published_tag!r}"
        )
    if previous != published_tag:
        issues.append(
            f"release-state.json previousRelease {previous!r} does not equal published release {published_tag!r}"
        )
    if published_tag == candidate_tag:
        issues.append("published and candidate tags must be distinct")
    if candidate_tag in reserved_tags:
        issues.append("candidate tag must not reuse a reserved tag")
    if (
        isinstance(candidate_tag, str)
        and isinstance(previous, str)
        and TAG_PATTERN.fullmatch(candidate_tag)
        and TAG_PATTERN.fullmatch(previous)
    ):
        sequence = [previous, *reserved_tags]
        highest_sequence_tag = max(sequence, key=semver_key)
        if not is_next_patch(candidate_tag, highest_sequence_tag):
            issues.append(
                "candidate tag must be the next patch after the highest reserved sequence tag"
            )
    if candidate.get("basedOnReleaseTag") != published_tag:
        issues.append("next-release.json basedOnReleaseTag must equal release.json releaseTag")
    if candidate.get("releaseState") != "candidate" or candidate.get("published") is not False:
        issues.append("next-release.json must remain an unpublished candidate")
    digests = state.get("metadataDigests")
    if not isinstance(digests, dict):
        issues.append("release-state.json metadataDigests must reference legacy metadata files")
    else:
        for key, path in (("published", published_path), ("candidate", candidate_path)):
            expected = digests.get(key)
            actual = sha256_file(path)
            if not isinstance(expected, str) or not DIGEST_PATTERN.fullmatch(expected):
                issues.append(
                    f"release-state.json metadata digest {key} must be a SHA-256 hex digest"
                )
            elif actual is None or expected != actual:
                issues.append(
                    f"release-state.json metadata digest {key} does not match {path.name}"
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    issues = check_repository(args.root)
    if issues:
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("release state consistency check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
