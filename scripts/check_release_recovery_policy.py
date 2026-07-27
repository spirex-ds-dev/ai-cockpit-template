#!/usr/bin/env python3
"""Validate recovery after an immutable release tag fails before publication."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from check_release_distribution import is_next_patch_release


ROOT = Path(__file__).resolve().parents[1]
TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def recovery_policy_issues(root: Path = ROOT) -> list[str]:
    """Return deterministic errors for a reserved-tag recovery candidate."""
    published = _load(root / "release.json")
    candidate = _load(root / "next-release.json")
    state = _load(root / "release-state.json")
    issues: list[str] = []
    published_tag = published.get("releaseTag")
    candidate_tag = candidate.get("releaseTag")
    reserved_tags = state.get("reservedTags", [])
    if not isinstance(reserved_tags, list) or any(
        not isinstance(tag, str) or not TAG_PATTERN.fullmatch(tag) for tag in reserved_tags
    ):
        return ["release-state.json reservedTags must be a list of semantic version tags"]
    if not reserved_tags:
        return issues
    highest_reserved = max(
        reserved_tags, key=lambda tag: tuple(int(part) for part in tag.removeprefix("v").split("."))
    )
    if not isinstance(candidate_tag, str) or not is_next_patch_release(
        candidate_tag, highest_reserved
    ):
        issues.append(
            f"next-release.json releaseTag {candidate_tag!r} must be the next patch after highest "
            f"immutable reserved tag {highest_reserved!r}"
        )
    if candidate.get("basedOnReleaseTag") != published_tag:
        issues.append("next-release.json basedOnReleaseTag must remain the published release tag")
    if candidate.get("releaseState") != "candidate" or candidate.get("published") is not False:
        issues.append("next-release.json must remain an unpublished candidate during recovery")
    return issues


def documentation_policy_issues(root: Path = ROOT) -> list[str]:
    """Ensure the governed recovery rule remains visible to maintainers."""
    text = (root / "docs" / "reference" / "distribution.md").read_text(encoding="utf-8")
    required = (
        "canonical `reservedTags`",
        "must not change `release.json` or `basedOnReleaseTag`",
        "next patch after the highest immutable reserved tag",
    )
    return [
        f"docs/reference/distribution.md is missing reserved-tag recovery boundary: {phrase}"
        for phrase in required
        if phrase not in text
    ]


def main() -> int:
    try:
        issues = [*recovery_policy_issues(), *documentation_policy_issues()]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"release recovery policy check failed: {exc}", file=sys.stderr)
        return 1
    if issues:
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("release recovery policy check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
