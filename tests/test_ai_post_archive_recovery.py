import hashlib
import json

import ai_post_archive_recovery as recovery
import pytest


def write_archive(root, task="example-task"):
    archive = root / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    files = {
        f"{task}.contract.json": {"workItemId": task},
        f"{task}.summary.json": {"workItemId": task},
        f"{task}.outcome.json": {"workItemId": task, "status": "completed"},
        f"{task}.archive-manifest.json": {"workItemId": task},
    }
    for name, value in files.items():
        (archive / name).write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return archive


def test_open_recovery_binds_failed_pr_audit_without_mutating_archive(tmp_path):
    archive = write_archive(tmp_path)
    original = {path.name: path.read_bytes() for path in archive.iterdir()}

    receipt = recovery.open_post_archive_recovery(
        root=tmp_path,
        task="example-task",
        base_commit="a" * 40,
        issue="https://github.com/example/repo/issues/1",
        authority="user-authorized same Work Item recovery",
        recovery_paths=["scripts/ai_finish.py", "tests/test_finish.py"],
        run_pr_audit=lambda _command: (1, "changed-critical coverage failed: below floor"),
        worktree_clean=lambda: True,
    )

    assert receipt["failure"]["gate"] == "changedCriticalCoverage"
    assert receipt["recoveryPaths"] == ["scripts/ai_finish.py", "tests/test_finish.py"]
    assert (
        receipt["archive"]["outcome"]["sha256"]
        == hashlib.sha256(original["example-task.outcome.json"]).hexdigest()
    )
    assert {path.name: path.read_bytes() for path in archive.iterdir()} == original
    assert recovery.validate_recovery_receipt(tmp_path, receipt, pr_base="a" * 40) == []


def test_open_recovery_refuses_when_pr_audit_is_not_failing(tmp_path):
    write_archive(tmp_path)

    with pytest.raises(ValueError, match="must fail"):
        recovery.open_post_archive_recovery(
            root=tmp_path,
            task="example-task",
            base_commit="a" * 40,
            issue="https://github.com/example/repo/issues/1",
            authority="user-authorized same Work Item recovery",
            recovery_paths=["scripts/ai_finish.py"],
            run_pr_audit=lambda _command: (0, "aggregate PR check passed"),
            worktree_clean=lambda: True,
        )
