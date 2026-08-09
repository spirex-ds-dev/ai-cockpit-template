"""Provision a worktree-local, hash-locked development environment when needed."""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404: invokes only the requested interpreter and fixed tool modules
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def direct_pin(manifest: Path, tool: str = "ruff") -> str:
    """Return the sole direct version pin for *tool* from the development manifest."""
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


def installed_version(interpreter: Path, tool: str = "ruff", *, root: Path) -> str:
    """Return a tool version from the specified virtual-environment interpreter."""
    result = subprocess.run(  # nosec B603: interpreter path and module name are fixed by this repository
        [str(interpreter), "-m", tool, "--version"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"cannot execute {tool} with {interpreter}: {detail}")
    match = re.fullmatch(rf"{re.escape(tool)}\s+([^\s]+)", result.stdout.strip())
    if match is None:
        raise ValueError(f"cannot parse {tool} version output: {result.stdout.strip()!r}")
    return match.group(1)


def needs_provision(interpreter: Path, manifest: Path, *, root: Path) -> bool:
    """Whether the local environment is absent, unusable, or off its direct pin."""
    if not interpreter.is_file():
        return True
    try:
        return installed_version(interpreter, root=root) != direct_pin(manifest)
    except (OSError, RuntimeError, ValueError):
        return True


def run(command: list[str], *, cwd: Path) -> None:
    """Run a bootstrap command and surface its failure without a fallback."""
    result = subprocess.run(  # nosec B603: commands are constructed internally from fixed inputs
        command,
        cwd=cwd,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"provisioning command failed ({result.returncode}): {' '.join(command)}"
        )


def provision(root: Path, bootstrap_python: str) -> None:
    """Create the virtual environment and install only the hash-locked development set."""
    interpreter = root / ".venv" / "bin" / "python"
    run([bootstrap_python, "-m", "venv", ".venv"], cwd=root)
    if not interpreter.is_file():
        raise RuntimeError(f"virtual-environment creation did not produce {interpreter}")
    run(
        [
            str(interpreter),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "-r",
            "requirements-dev.lock",
        ],
        cwd=root,
    )


def ensure(root: Path, bootstrap_python: str) -> None:
    """Converge the local development environment or fail closed."""
    manifest = root / "requirements-dev.in"
    interpreter = root / ".venv" / "bin" / "python"
    expected = direct_pin(manifest)
    if not needs_provision(interpreter, manifest, root=root):
        print(f"locked development environment ready: Ruff {expected}")
        return
    print(f"provisioning locked development environment for Ruff {expected}")
    provision(root, bootstrap_python)
    observed = installed_version(interpreter, root=root)
    if observed != expected:
        raise RuntimeError(
            f"provisioned Ruff version mismatch: expected {expected}, observed {observed}"
        )
    print(f"locked development environment provisioned: Ruff {observed}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--bootstrap-python", default=sys.executable)
    args = parser.parse_args()
    try:
        ensure(args.root.resolve(), args.bootstrap_python)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"locked development environment unavailable: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
