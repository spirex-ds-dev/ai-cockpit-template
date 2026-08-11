#!/usr/bin/env python3
"""Synchronize verified public release assets into the next source candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
INSTALLER_DEFAULT_REF = re.compile(r"(AI_COCKPIT_TEMPLATE_REF:-)v\d+\.\d+\.\d+")
INSTALLER_USAGE_REF = re.compile(r"(AI_COCKPIT_TEMPLATE_REF=)v\d+\.\d+\.\d+")


class ProjectionSyncError(ValueError):
    """Raised when provider assets cannot safely become source projection facts."""


def load_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProjectionSyncError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ProjectionSyncError(f"{label} must contain an object")
    return value


def next_patch(tag: str) -> str:
    match = TAG.fullmatch(tag)
    if match is None:
        raise ProjectionSyncError("release tag must be a semantic version")
    major, minor, patch = (int(part) for part in match.groups())
    return f"v{major}.{minor}.{patch + 1}"


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def synchronized_installer_bytes(path: Path, candidate_tag: str) -> bytes:
    """Advance both public installer default references with the candidate."""
    try:
        installer = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProjectionSyncError("install.sh is required for projection synchronization") from exc
    installer, default_count = INSTALLER_DEFAULT_REF.subn(
        rf"\g<1>{candidate_tag}", installer, count=1
    )
    installer, usage_count = INSTALLER_USAGE_REF.subn(rf"\g<1>{candidate_tag}", installer, count=1)
    if default_count != 1 or usage_count != 1:
        raise ProjectionSyncError(
            "install.sh must contain exactly one default ref and one documented ref"
        )
    return installer.encode("utf-8")


def synchronize_projection(
    root: Path,
    *,
    release_tag: str,
    source_commit: str,
    release_json_bytes: bytes,
    release_digests_bytes: bytes,
    unavailable_entry: dict[str, str] | None = None,
) -> None:
    """Atomically promote provider-verified facts and advance the candidate patch."""
    if not TAG.fullmatch(release_tag):
        raise ProjectionSyncError("release tag must be a semantic version")
    if not COMMIT.fullmatch(source_commit):
        raise ProjectionSyncError("source_commit must be a concrete commit SHA")
    release = load_object(release_json_bytes, "release.json asset")
    digests = load_object(release_digests_bytes, "release-digests.json asset")
    if release.get("releaseTag") != release_tag:
        raise ProjectionSyncError("release.json asset releaseTag does not match requested tag")
    if digests.get("releaseTag") != release_tag:
        raise ProjectionSyncError(
            "release-digests.json asset releaseTag does not match requested tag"
        )
    for field in ("sourceCommit", "tagTarget", "metadataCommit"):
        if digests.get(field) != source_commit:
            raise ProjectionSyncError(
                f"release-digests.json asset {field} does not match sourceCommit"
            )

    next_release_path = root / "next-release.json"
    state_path = root / "release-state.json"
    version_path = root / ".ai" / "cockpit" / "version.json"
    candidate = load_object(next_release_path.read_bytes(), "next-release.json")
    state = load_object(state_path.read_bytes(), "release-state.json")
    version = load_object(version_path.read_bytes(), "version.json")
    candidate_tag = next_patch(release_tag)
    installer_bytes = synchronized_installer_bytes(root / "install.sh", candidate_tag)
    candidate["releaseTag"] = candidate_tag
    candidate["releaseState"] = "candidate"
    candidate["published"] = False
    candidate["basedOnReleaseTag"] = release_tag
    state["state"] = "candidate_prepared"
    state["releaseTag"] = candidate_tag
    state["sourceBinding"] = "deferred_to_release_finalization"
    state["sourceCommit"] = None
    state["previousRelease"] = release_tag
    reserved = state.get("reservedTags")
    if not isinstance(reserved, list) or any(not isinstance(item, str) for item in reserved):
        raise ProjectionSyncError("release-state reservedTags is invalid")
    state["reservedTags"] = sorted({*reserved, release_tag})
    if unavailable_entry is not None:
        allowed_kinds = {
            "stable_release_invalid_public_distribution",
            "stable_release_unverified",
            "tag_only",
        }
        if unavailable_entry.get("kind") not in allowed_kinds or not all(
            isinstance(unavailable_entry.get(key), str) and unavailable_entry[key]
            for key in ("reason", "evidence")
        ):
            raise ProjectionSyncError("unavailable release entry is invalid")
        unavailable = state.get("unavailableTags")
        if not isinstance(unavailable, list):
            raise ProjectionSyncError("release-state unavailableTags is invalid")
        state["unavailableTags"] = [
            item
            for item in unavailable
            if not isinstance(item, dict) or item.get("tag") != release_tag
        ] + [{"tag": release_tag, **unavailable_entry}]
    metadata_digests = state.get("metadataDigests")
    if not isinstance(metadata_digests, dict):
        raise ProjectionSyncError("release-state metadataDigests is invalid")
    metadata_digests["published"] = hashlib.sha256(release_json_bytes).hexdigest()
    metadata_digests["candidate"] = hashlib.sha256(
        (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode()
    ).hexdigest()
    version["releaseVersion"] = candidate_tag.removeprefix("v")

    # All validation completes before this first write, preventing partial projection promotion.
    (root / "release.json").write_bytes(release_json_bytes)
    (root / ".ai" / "cockpit" / "release-digests.json").write_bytes(release_digests_bytes)
    (root / "install.sh").write_bytes(installer_bytes)
    write_json(next_release_path, candidate)
    write_json(state_path, state)
    write_json(version_path, version)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--release-json", type=Path, required=True)
    parser.add_argument("--release-digests", type=Path, required=True)
    parser.add_argument("--release-json-sha256", required=True)
    parser.add_argument("--release-digests-sha256", required=True)
    parser.add_argument(
        "--unavailable-kind",
        choices=[
            "stable_release_invalid_public_distribution",
            "stable_release_unverified",
            "tag_only",
        ],
    )
    parser.add_argument("--unavailable-reason")
    parser.add_argument("--unavailable-evidence")
    args = parser.parse_args(argv)
    try:
        release_bytes = args.release_json.read_bytes()
        digest_bytes = args.release_digests.read_bytes()
        if hashlib.sha256(release_bytes).hexdigest() != args.release_json_sha256:
            raise ProjectionSyncError("release.json asset digest mismatch")
        if hashlib.sha256(digest_bytes).hexdigest() != args.release_digests_sha256:
            raise ProjectionSyncError("release-digests.json asset digest mismatch")
        unavailable_values = (
            args.unavailable_kind,
            args.unavailable_reason,
            args.unavailable_evidence,
        )
        if any(unavailable_values) and not all(unavailable_values):
            raise ProjectionSyncError(
                "unavailable release status requires kind, reason, and evidence"
            )
        synchronize_projection(
            args.root,
            release_tag=args.release_tag,
            source_commit=args.source_commit,
            release_json_bytes=release_bytes,
            release_digests_bytes=digest_bytes,
            unavailable_entry=(
                {
                    "kind": args.unavailable_kind,
                    "reason": args.unavailable_reason,
                    "evidence": args.unavailable_evidence,
                }
                if all(unavailable_values)
                else None
            ),
        )
    except (OSError, ProjectionSyncError) as exc:
        print(f"ERROR: published release projection sync failed: {exc}", file=sys.stderr)
        return 2
    print(f"published release projection synchronized: {args.release_tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
