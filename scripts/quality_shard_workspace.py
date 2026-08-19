#!/usr/bin/env python3
"""Coordinate isolated quality-shard worktrees without serializing shard tests."""

from __future__ import annotations

import argparse
import fcntl
import shutil
import subprocess  # nosec B404 - all commands are constructed as fixed list-form argv
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


class LifecycleError(RuntimeError):
    """An actionable failure in a named temporary-worktree lifecycle phase."""

    def __init__(self, phase: str, message: str) -> None:
        super().__init__(message)
        self.phase = phase
        self.message = message


@dataclass(frozen=True)
class LifecycleResult:
    exit_code: int
    diagnostics: list[str]


def run_locked_mutation(lock_path: Path, mutation: Callable[[], None]) -> None:
    """Run one Git-common-directory mutation under a cross-process file lock."""

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            mutation()
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def run_lifecycle(
    *,
    shard: str,
    prepare: Callable[[], None],
    runner: Callable[[], int],
    publish: Callable[[], None],
    cleanup: Callable[[], None],
) -> LifecycleResult:
    """Run one shard and preserve its primary failure when cleanup also fails."""

    exit_code = 0
    diagnostics: list[str] = []
    try:
        prepare()
        exit_code = runner()
        if exit_code == 0:
            publish()
    except LifecycleError as error:
        exit_code = 1
        diagnostics.append(f"project-test shard {shard} {error.phase} failed: {error.message}")
    finally:
        try:
            cleanup()
        except LifecycleError as error:
            diagnostics.append(f"project-test shard {shard} {error.phase} failed: {error.message}")
            if exit_code == 0:
                exit_code = 1

    return LifecycleResult(exit_code=exit_code, diagnostics=diagnostics)


def _inside(path: Path, parent: Path, *, label: str) -> Path:
    resolved_path = path.resolve()
    resolved_parent = parent.resolve()
    if not resolved_path.is_relative_to(resolved_parent):
        raise LifecycleError("validation", f"{label} must be inside {resolved_parent}")
    return resolved_path


def _run(
    command: list[str], *, cwd: Path, phase: str, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(  # nosec B603 - argv is fixed list-form Git/test execution
            command,
            cwd=cwd,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise LifecycleError(phase, f"could not start {' '.join(command)}: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or f"exit {completed.returncode}"
        raise LifecycleError(phase, detail)
    return completed


def _git(root: Path, arguments: list[str], *, phase: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", "-C", str(root), *arguments], cwd=root, phase=phase)


def _registered(root: Path, workspace: Path) -> bool:
    listing = _git(root, ["worktree", "list", "--porcelain"], phase="worktree-list").stdout
    return f"worktree {workspace}" in listing.splitlines()


def _remove_directory(path: Path, *, phase: str) -> None:
    if not path.exists() and not path.is_symlink():
        return
    try:
        shutil.rmtree(path)
    except OSError as error:
        raise LifecycleError(phase, f"cannot remove {path}: {error}") from error


def prepare_workspace(*, root: Path, workspace: Path, lock_path: Path) -> None:
    """Create a detached shard worktree, serializing only Git metadata changes."""

    def mutation() -> None:
        if _registered(root, workspace):
            _remove_registered_worktree(root=root, workspace=workspace, phase="worktree-remove")
        _remove_directory(workspace, phase="worktree-reset")
        _git(root, ["worktree", "add", "--detach", str(workspace), "HEAD"], phase="worktree-add")

    run_locked_mutation(lock_path, mutation)


def cleanup_workspace(*, root: Path, workspace: Path, lock_path: Path) -> None:
    """Remove a temporary shard worktree under the same Git metadata lock."""

    def mutation() -> None:
        if _registered(root, workspace):
            _remove_registered_worktree(root=root, workspace=workspace, phase="cleanup")
        _remove_directory(workspace, phase="cleanup")

    run_locked_mutation(lock_path, mutation)


def _remove_registered_worktree(*, root: Path, workspace: Path, phase: str) -> None:
    try:
        _git(root, ["worktree", "remove", "--force", str(workspace)], phase=phase)
        return
    except LifecycleError as error:
        if "Directory not empty" not in error.message:
            raise
        _remove_directory(workspace, phase=f"{phase}-residual")
        if _registered(root, workspace):
            _git(root, ["worktree", "remove", "--force", str(workspace)], phase=phase)


def copy_current_evidence(*, root: Path, workspace: Path) -> None:
    diff = _git(root, ["diff", "--binary"], phase="evidence-copy").stdout
    if diff:
        _run(
            ["git", "-C", str(workspace), "apply", "--whitespace=nowarn", "-"],
            cwd=root,
            phase="evidence-copy",
            input_text=diff,
        )
    entries = _git(
        root, ["ls-files", "--others", "--exclude-standard"], phase="evidence-copy"
    ).stdout
    for relative_text in entries.splitlines():
        relative = Path(relative_text)
        if relative.parts and relative.parts[0] in {"target", ".venv"}:
            continue
        source = _inside(root / relative, root, label="untracked evidence")
        destination = _inside(
            workspace / relative, workspace, label="untracked evidence destination"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source, destination)
        except OSError as error:
            raise LifecycleError("evidence-copy", f"cannot copy {relative}: {error}") from error


def regenerate_workspace(*, workspace: Path, python: str) -> None:
    for script in (
        "ai_capability_truth.py",
        "ai_japanese_capability.py",
        "check_pre_release_documentation_alignment.py",
    ):
        _run(
            [python, f"scripts/{script}", "--write"], cwd=workspace, phase="workspace-regeneration"
        )


def copy_inputs(*, root: Path, workspace: Path, manifest: Path, plan: Path) -> None:
    destination = workspace / "target" / "quality"
    destination.mkdir(parents=True, exist_ok=True)
    for source in (manifest, plan):
        try:
            shutil.copy2(source, destination / source.name)
        except OSError as error:
            raise LifecycleError("evidence-copy", f"cannot copy {source}: {error}") from error


def run_shard(*, workspace: Path, manifest: Path, plan: Path, shard: str, python: str) -> int:
    command = [
        python,
        "scripts/quality_test_manifest.py",
        "run-shard",
        "--root",
        str(workspace),
        "--manifest",
        str(workspace / "target" / "quality" / manifest.name),
        "--plan",
        str(workspace / "target" / "quality" / plan.name),
        "--shard",
        shard,
        "--output",
        str(workspace / "target" / "quality" / "shards" / shard),
    ]
    try:
        return subprocess.run(  # nosec B603 - coordinator passes validated list-form argv
            command, cwd=workspace, check=False
        ).returncode
    except OSError as error:
        raise LifecycleError("runner", f"could not start {' '.join(command)}: {error}") from error


def publish_artifacts(*, root: Path, workspace: Path, shard: str) -> None:
    destination = _inside(
        root / "target" / "quality" / "shards" / shard,
        root / "target" / "quality" / "shards",
        label="artifact destination",
    )
    source = workspace / "target" / "quality" / "shards" / shard
    if not source.is_dir():
        raise LifecycleError("publish", f"missing shard evidence at {source}")
    _remove_directory(destination, phase="publish")
    try:
        shutil.copytree(source, destination)
    except OSError as error:
        raise LifecycleError("publish", f"cannot publish shard evidence: {error}") from error


def run_workspace(args: argparse.Namespace) -> LifecycleResult:
    root = Path(args.root).resolve()
    quality_root = root / "target" / "quality"
    workspace_root = _inside(Path(args.workspace_root), quality_root, label="workspace root")
    workspace = _inside(workspace_root / args.shard, workspace_root, label="workspace")
    manifest = _inside(Path(args.manifest), quality_root, label="manifest")
    plan = _inside(Path(args.plan), quality_root, label="plan")
    lock_path = workspace_root / ".worktree-metadata.lock"

    def prepare() -> None:
        prepare_workspace(root=root, workspace=workspace, lock_path=lock_path)
        copy_current_evidence(root=root, workspace=workspace)
        regenerate_workspace(workspace=workspace, python=args.python)
        copy_inputs(root=root, workspace=workspace, manifest=manifest, plan=plan)

    return run_lifecycle(
        shard=args.shard,
        prepare=prepare,
        runner=lambda: run_shard(
            workspace=workspace,
            manifest=manifest,
            plan=plan,
            shard=args.shard,
            python=args.python,
        ),
        publish=lambda: publish_artifacts(root=root, workspace=workspace, shard=args.shard),
        cleanup=lambda: cleanup_workspace(root=root, workspace=workspace, lock_path=lock_path),
    )


def cleanup_workspace_command(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    quality_root = root / "target" / "quality"
    workspace_root = _inside(Path(args.workspace_root), quality_root, label="workspace root")
    workspace = _inside(workspace_root / args.shard, workspace_root, label="workspace")
    try:
        cleanup_workspace(
            root=root,
            workspace=workspace,
            lock_path=workspace_root / ".worktree-metadata.lock",
        )
    except LifecycleError as error:
        print(
            f"project-test shard {args.shard} {error.phase} failed: {error.message}",
            file=sys.stderr,
        )
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run one isolated project-test shard")
    run.add_argument("--root", required=True)
    run.add_argument("--workspace-root", required=True)
    run.add_argument("--manifest", required=True)
    run.add_argument("--plan", required=True)
    run.add_argument("--shard", required=True)
    run.add_argument("--python", default=sys.executable)
    cleanup = subparsers.add_parser("cleanup", help="recover one isolated project-test shard")
    cleanup.add_argument("--root", required=True)
    cleanup.add_argument("--workspace-root", required=True)
    cleanup.add_argument("--shard", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "cleanup":
        return cleanup_workspace_command(args)
    result = run_workspace(args)
    for diagnostic in result.diagnostics:
        print(diagnostic, file=sys.stderr)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
