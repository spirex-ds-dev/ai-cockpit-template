from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest

from scripts import quality_shard_workspace


def init_git_repository(root: Path) -> None:
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "tests@example.invalid"], check=True
    )
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Quality Tests"], check=True)
    (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "--quiet", "-m", "initial"], check=True)


def test_lifecycle_serializes_each_shared_git_metadata_mutation(tmp_path: Path) -> None:
    calls: list[str] = []

    def mutation() -> None:
        calls.append("mutation")

    quality_shard_workspace.run_locked_mutation(tmp_path / "worktree.lock", mutation)

    assert calls == ["mutation"]


def test_workspace_lifecycle_creates_and_removes_a_real_detached_worktree(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    init_git_repository(root)
    workspace = root / "target" / "quality" / "shard-workspaces" / "core"
    lock_path = workspace.parent / ".worktree-metadata.lock"

    quality_shard_workspace.prepare_workspace(
        root=root,
        workspace=workspace,
        lock_path=lock_path,
    )

    assert (workspace / "tracked.txt").is_file()
    assert quality_shard_workspace._registered(root, workspace)

    quality_shard_workspace.cleanup_workspace(
        root=root,
        workspace=workspace,
        lock_path=lock_path,
    )

    assert not workspace.exists()
    assert not quality_shard_workspace._registered(root, workspace)


def test_prepare_recovers_a_registered_nonempty_worktree(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    init_git_repository(root)
    workspace = root / "target" / "quality" / "shard-workspaces" / "core"
    lock_path = workspace.parent / ".worktree-metadata.lock"

    quality_shard_workspace.prepare_workspace(
        root=root,
        workspace=workspace,
        lock_path=lock_path,
    )
    (workspace / "stale-generated-file").write_text("stale\n", encoding="utf-8")

    quality_shard_workspace.prepare_workspace(
        root=root,
        workspace=workspace,
        lock_path=lock_path,
    )

    assert not (workspace / "stale-generated-file").exists()
    quality_shard_workspace.cleanup_workspace(
        root=root,
        workspace=workspace,
        lock_path=lock_path,
    )


def test_successful_runner_and_cleanup_preserve_success() -> None:
    events: list[str] = []

    result = quality_shard_workspace.run_lifecycle(
        shard="core",
        prepare=lambda: events.append("prepare"),
        runner=lambda: events.append("runner") or 0,
        publish=lambda: events.append("publish"),
        cleanup=lambda: events.append("cleanup"),
    )

    assert result.exit_code == 0
    assert result.diagnostics == []
    assert events == ["prepare", "runner", "publish", "cleanup"]


def test_cleanup_failure_is_visible_and_fails_a_successful_runner() -> None:
    def fail_cleanup() -> None:
        raise quality_shard_workspace.LifecycleError("cleanup", "cannot remove worktree")

    result = quality_shard_workspace.run_lifecycle(
        shard="release",
        prepare=lambda: None,
        runner=lambda: 0,
        publish=lambda: None,
        cleanup=fail_cleanup,
    )

    assert result.exit_code != 0
    assert result.diagnostics == [
        "project-test shard release cleanup failed: cannot remove worktree"
    ]


def test_cleanup_failure_does_not_overwrite_preceding_runner_failure() -> None:
    def fail_cleanup() -> None:
        raise quality_shard_workspace.LifecycleError("cleanup", "cannot remove worktree")

    result = quality_shard_workspace.run_lifecycle(
        shard="governance",
        prepare=lambda: None,
        runner=lambda: 23,
        publish=lambda: None,
        cleanup=fail_cleanup,
    )

    assert result.exit_code == 23
    assert result.diagnostics == [
        "project-test shard governance cleanup failed: cannot remove worktree"
    ]


def test_prepare_failure_is_reported_and_cleanup_still_runs() -> None:
    result = quality_shard_workspace.run_lifecycle(
        shard="installer",
        prepare=lambda: (_ for _ in ()).throw(
            quality_shard_workspace.LifecycleError("prepare", "cannot create worktree")
        ),
        runner=lambda: 0,
        publish=lambda: None,
        cleanup=lambda: None,
    )

    assert result.exit_code == 1
    assert result.diagnostics == [
        "project-test shard installer prepare failed: cannot create worktree"
    ]


def test_run_locked_mutation_releases_lock_after_a_failure(tmp_path: Path) -> None:
    def fail() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        quality_shard_workspace.run_locked_mutation(tmp_path / "lock", fail)

    quality_shard_workspace.run_locked_mutation(tmp_path / "lock", lambda: None)


def test_inside_rejects_a_path_outside_the_declared_boundary(tmp_path: Path) -> None:
    with pytest.raises(quality_shard_workspace.LifecycleError, match="must be inside"):
        quality_shard_workspace._inside(tmp_path / "outside", tmp_path / "parent", label="path")


def test_run_reports_command_failures_with_their_phase(monkeypatch: pytest.MonkeyPatch) -> None:
    completed = subprocess.CompletedProcess(["tool"], 7, "output", "failure")
    monkeypatch.setattr(
        quality_shard_workspace.subprocess, "run", lambda *args, **kwargs: completed
    )

    with pytest.raises(quality_shard_workspace.LifecycleError, match="failure") as raised:
        quality_shard_workspace._run(["tool"], cwd=Path.cwd(), phase="copy")

    assert raised.value.phase == "copy"


def test_run_reports_a_process_start_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("missing tool")

    monkeypatch.setattr(quality_shard_workspace.subprocess, "run", fail)
    with pytest.raises(quality_shard_workspace.LifecycleError, match="could not start"):
        quality_shard_workspace._run(["missing-tool"], cwd=Path.cwd(), phase="runner")


def test_copy_current_evidence_applies_tracked_and_untracked_changes(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    init_git_repository(root)
    workspace = root / "target" / "quality" / "shard-workspaces" / "core"
    lock_path = workspace.parent / ".worktree-metadata.lock"
    quality_shard_workspace.prepare_workspace(root=root, workspace=workspace, lock_path=lock_path)

    (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
    (root / "new.txt").write_text("new\n", encoding="utf-8")
    quality_shard_workspace.copy_current_evidence(root=root, workspace=workspace)

    assert (workspace / "tracked.txt").read_text(encoding="utf-8") == "changed\n"
    assert (workspace / "new.txt").read_text(encoding="utf-8") == "new\n"
    quality_shard_workspace.cleanup_workspace(root=root, workspace=workspace, lock_path=lock_path)


def test_regenerate_and_copy_inputs_use_the_declared_workspace_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    calls: list[list[str]] = []
    monkeypatch.setattr(
        quality_shard_workspace,
        "_run",
        lambda command, **kwargs: (
            calls.append(command) or subprocess.CompletedProcess(command, 0, "", "")
        ),
    )
    quality_shard_workspace.regenerate_workspace(workspace=workspace, python="python")
    assert len(calls) == 3

    root = tmp_path / "root"
    root.mkdir()
    manifest = root / "manifest.json"
    plan = root / "plan.json"
    manifest.write_text("{}\n", encoding="utf-8")
    plan.write_text("{}\n", encoding="utf-8")
    quality_shard_workspace.copy_inputs(
        root=root,
        workspace=workspace,
        manifest=manifest,
        plan=plan,
    )
    assert (workspace / "target" / "quality" / "manifest.json").is_file()
    assert (workspace / "target" / "quality" / "plan.json").is_file()


def test_run_shard_and_publish_artifacts_preserve_the_shard_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    output = workspace / "target" / "quality" / "shards" / "core"
    output.mkdir(parents=True)
    (output / "receipt.json").write_text("{}\n", encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(
        quality_shard_workspace.subprocess,
        "run",
        lambda command, **kwargs: (
            calls.append(command) or subprocess.CompletedProcess(command, 0, "", "")
        ),
    )
    assert (
        quality_shard_workspace.run_shard(
            workspace=workspace,
            manifest=workspace / "manifest.json",
            plan=workspace / "plan.json",
            shard="core",
            python="python",
        )
        == 0
    )
    assert calls and calls[0][1:3] == ["scripts/quality_test_manifest.py", "run-shard"]

    root = tmp_path / "root"
    artifact_source = root / "workspace" / "target" / "quality" / "shards" / "core"
    artifact_source.mkdir(parents=True)
    (artifact_source / "receipt.json").write_text("{}\n", encoding="utf-8")
    quality_shard_workspace.publish_artifacts(root=root, workspace=root / "workspace", shard="core")
    assert (root / "target" / "quality" / "shards" / "core" / "receipt.json").is_file()

    with pytest.raises(quality_shard_workspace.LifecycleError, match="missing shard evidence"):
        quality_shard_workspace.publish_artifacts(
            root=root, workspace=root / "missing-workspace", shard="core"
        )


def test_run_shard_reports_a_process_start_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("missing runner")

    monkeypatch.setattr(quality_shard_workspace.subprocess, "run", fail)
    with pytest.raises(quality_shard_workspace.LifecycleError, match="could not start"):
        quality_shard_workspace.run_shard(
            workspace=tmp_path,
            manifest=tmp_path / "manifest.json",
            plan=tmp_path / "plan.json",
            shard="core",
            python="missing-python",
        )


def test_registered_worktree_recovery_removes_nonempty_residue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "worktree"
    workspace.mkdir()
    (workspace / "stale").write_text("stale\n", encoding="utf-8")
    calls = 0

    def fake_git(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise quality_shard_workspace.LifecycleError("cleanup", "Directory not empty")
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr(quality_shard_workspace, "_git", fake_git)
    monkeypatch.setattr(quality_shard_workspace, "_registered", lambda *args: True)
    quality_shard_workspace._remove_registered_worktree(
        root=tmp_path, workspace=workspace, phase="cleanup"
    )
    assert calls == 2
    assert not workspace.exists()


def test_run_workspace_wires_all_lifecycle_phases(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    (root / "target" / "quality").mkdir(parents=True)
    manifest = root / "target" / "quality" / "manifest.json"
    plan = root / "target" / "quality" / "plan.json"
    manifest.write_text("{}\n", encoding="utf-8")
    plan.write_text("{}\n", encoding="utf-8")
    events: list[str] = []
    monkeypatch.setattr(
        quality_shard_workspace, "prepare_workspace", lambda **kwargs: events.append("prepare")
    )
    monkeypatch.setattr(
        quality_shard_workspace, "copy_current_evidence", lambda **kwargs: events.append("copy")
    )
    monkeypatch.setattr(
        quality_shard_workspace,
        "regenerate_workspace",
        lambda **kwargs: events.append("regenerate"),
    )
    monkeypatch.setattr(
        quality_shard_workspace, "copy_inputs", lambda **kwargs: events.append("inputs")
    )
    monkeypatch.setattr(
        quality_shard_workspace, "run_shard", lambda **kwargs: events.append("runner") or 0
    )
    monkeypatch.setattr(
        quality_shard_workspace, "publish_artifacts", lambda **kwargs: events.append("publish")
    )
    monkeypatch.setattr(
        quality_shard_workspace, "cleanup_workspace", lambda **kwargs: events.append("cleanup")
    )
    result = quality_shard_workspace.run_workspace(
        argparse.Namespace(
            root=str(root),
            workspace_root=str(root / "target" / "quality" / "run-1"),
            manifest=str(manifest),
            plan=str(plan),
            shard="core",
            python="python",
        )
    )
    assert result.exit_code == 0
    assert events == ["prepare", "copy", "regenerate", "inputs", "runner", "publish", "cleanup"]


def test_cleanup_command_reports_a_lifecycle_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    (root / "target" / "quality").mkdir(parents=True)
    monkeypatch.setattr(
        quality_shard_workspace,
        "cleanup_workspace",
        lambda **kwargs: (_ for _ in ()).throw(
            quality_shard_workspace.LifecycleError("cleanup", "cannot remove")
        ),
    )
    args = argparse.Namespace(
        root=str(root),
        workspace_root=str(root / "target" / "quality" / "run-1"),
        shard="core",
    )
    assert quality_shard_workspace.cleanup_workspace_command(args) == 1


def test_main_dispatches_run_and_cleanup_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(quality_shard_workspace, "cleanup_workspace_command", lambda args: 0)
    assert (
        quality_shard_workspace.main(
            [
                "cleanup",
                "--root",
                str(tmp_path),
                "--workspace-root",
                str(tmp_path / "target" / "quality"),
                "--shard",
                "core",
            ]
        )
        == 0
    )

    monkeypatch.setattr(
        quality_shard_workspace,
        "run_workspace",
        lambda args: quality_shard_workspace.LifecycleResult(0, ["diagnostic"]),
    )
    assert (
        quality_shard_workspace.main(
            [
                "run",
                "--root",
                str(tmp_path),
                "--workspace-root",
                str(tmp_path / "target" / "quality"),
                "--manifest",
                str(tmp_path / "target" / "quality" / "manifest.json"),
                "--plan",
                str(tmp_path / "target" / "quality" / "plan.json"),
                "--shard",
                "core",
            ]
        )
        == 0
    )
