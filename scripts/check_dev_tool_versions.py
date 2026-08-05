#!/usr/bin/env python3
"""Require local development tools to match their direct repository pins."""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404: invokes the current interpreter with the fixed Ruff module only
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "requirements-dev.in"
RECOVERY_COMMANDS = (
    "python3 -m venv .venv",
    ".venv/bin/python -m pip install --require-hashes -r requirements-dev.lock",
    "make project-format-check",
)


def recovery_guidance() -> str:
    return "\n".join(
        (
            "Recovery (from the repository root):",
            *(f"  {command}" for command in RECOVERY_COMMANDS),
        )
    )


def direct_pin(manifest: Path, tool: str) -> str:
    pattern = re.compile(rf"^{re.escape(tool)}==([^\s#]+)\s*(?:#.*)?$")
    matches = [
        match.group(1)
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if (match := pattern.fullmatch(line.strip()))
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{manifest}: expected exactly one direct pin for {tool}; found {len(matches)}"
        )
    return matches[0]


def installed_version(tool: str) -> str:
    result = subprocess.run(  # nosec B603: current interpreter and the only allowed module are fixed
        [sys.executable, "-m", tool, "--version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"cannot execute {tool} with {sys.executable}: {detail}")
    match = re.fullmatch(rf"{re.escape(tool)}\s+([^\s]+)", result.stdout.strip())
    if match is None:
        raise ValueError(f"cannot parse {tool} version output: {result.stdout.strip()!r}")
    return match.group(1)


def check_tool_version(manifest: Path, tool: str) -> int:
    try:
        expected = direct_pin(manifest, tool)
        observed = installed_version(tool)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"{tool} version check failed: {exc}\n{recovery_guidance()}", file=sys.stderr)
        return 2
    if observed != expected:
        print(
            f"{tool} version mismatch: expected {expected}, observed {observed}. "
            "Run project checks from the repository's locked development environment.\n"
            + recovery_guidance(),
            file=sys.stderr,
        )
        return 1
    print(f"{tool} version check passed: {observed}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--tool", choices=("ruff",), default="ruff")
    args = parser.parse_args()
    return check_tool_version(args.manifest, args.tool)


if __name__ == "__main__":
    raise SystemExit(main())
