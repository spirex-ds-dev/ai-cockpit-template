#!/usr/bin/env python3
"""Determine quality scope from changed paths, defaulting conservatively."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import determine_governance_profile as governance_routing

POLICY_PATH = Path(__file__).resolve().parents[1] / ".ai/quality/governance-routing.yaml"


def changed_paths(base: str, head: str, repository: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "unable to determine changed paths")
    return [line for line in result.stdout.splitlines() if line]


def determine(paths: list[str], explicit: str | None = None) -> dict:
    explicit_profiles = {"fast": "lite", "full": "strict", "release": "release"}
    requested = explicit_profiles.get(explicit) if explicit is not None else None
    routed = governance_routing.determine(
        paths, governance_routing.load_policy(POLICY_PATH), requested=requested
    )
    profile = routed["selectedProfile"]
    scope = {"lite": "fast", "standard": "full", "strict": "full", "release": "release"}[profile]
    required = {
        "fast": ["quality-fast"],
        "full": ["quality-fast", "quality-full"],
        "release": ["quality-fast", "quality-full", "quality-release"],
    }[scope]
    return {
        "schemaVersion": 1,
        "scope": scope,
        "reasons": routed["reasons"],
        "changedPaths": routed["changedPaths"],
        "requiredGroups": required,
        "releasePreparation": scope == "release",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--event", default="local")
    parser.add_argument("--mode", choices=("fast", "full", "release"))
    parser.add_argument("--repository", default=".")
    parser.add_argument("--output", default="target/quality/scope.json")
    args = parser.parse_args()
    result = determine(changed_paths(args.base, args.head, Path(args.repository)), args.mode)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
