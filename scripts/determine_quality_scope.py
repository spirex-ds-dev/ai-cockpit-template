#!/usr/bin/env python3
"""Determine quality scope from changed paths, defaulting conservatively."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

RELEASE_PATHS = (
    "release.json",
    "next-release.json",
    "release-state.json",
    ".ai/cockpit/release-digests.json",
)
FULL_PREFIXES = (
    "scripts/",
    "tests/",
    ".github/workflows/",
    ".ai/",
    "examples/",
    "Makefile",
    "install.sh",
    "AGENTS.md",
    "GEMINI.md",
)
FAST_PREFIXES = ("docs/", "README")


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
    if explicit in {"fast", "full", "release"}:
        scope = explicit
        reasons = [f"explicit mode: {explicit}"]
    elif any(path in RELEASE_PATHS for path in paths):
        scope, reasons = "release", ["release preparation path changed"]
    elif any(path.startswith(FULL_PREFIXES) for path in paths):
        scope, reasons = "full", ["governance, code, test, install, or workflow path changed"]
    elif paths and all(path.startswith(FAST_PREFIXES) for path in paths):
        scope, reasons = "fast", ["documentation-only change"]
    else:
        scope, reasons = "full", ["unknown or mixed scope defaults to Full"]
    required = {
        "fast": ["quality-fast"],
        "full": ["quality-fast", "quality-full"],
        "release": ["quality-fast", "quality-full", "quality-release"],
    }[scope]
    return {
        "schemaVersion": 1,
        "scope": scope,
        "reasons": reasons,
        "changedPaths": paths,
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
