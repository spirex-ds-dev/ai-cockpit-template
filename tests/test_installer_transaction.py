from __future__ import annotations

import json
from pathlib import Path

import pytest

import ai_installer_transaction as transaction
from ai_installer_transaction import (
    InstallerLock,
    SourceMode,
    WritePlan,
    TransactionAction,
    classify_source,
)


def make_source(root: Path, *, git: bool = False) -> Path:
    (root / ".ai" / "cockpit").mkdir(parents=True)
    (root / ".ai" / "cockpit" / "version.json").write_text(
        json.dumps({"distributionVersion": 2, "contractSchema": 2}), encoding="utf-8"
    )
    if git:
        (root / ".git").mkdir()
    return root


def test_classify_unknown_source_without_identity(tmp_path):
    result = classify_source(tmp_path / "source")
    assert result.mode is SourceMode.UNKNOWN_SOURCE


def test_classify_complete_archive_as_verified_release(tmp_path):
    source = make_source(tmp_path / "source")
    (source / "release.json").write_text(
        json.dumps(
            {
                "releaseTag": "v1.0.0",
                "releaseEvidenceAuthority": "release-assets-v1",
                "installerDigest": "abc",
            }
        ),
        encoding="utf-8",
    )
    assert classify_source(source).mode is SourceMode.RELEASE_VERIFIED


def test_classify_invalid_archive_as_unknown(tmp_path):
    source = make_source(tmp_path / "source")
    (source / "release.json").write_text("{}", encoding="utf-8")
    assert classify_source(source).mode is SourceMode.UNKNOWN_SOURCE


def test_classify_clean_custom_and_private_checkouts(tmp_path, monkeypatch):
    source = make_source(tmp_path / "source")

    def fake_git(_source, *args):
        stdout = "true" if args == ("rev-parse", "--is-inside-work-tree") else ""
        return transaction.subprocess.CompletedProcess(["git"], 0, stdout, "")

    monkeypatch.setattr(transaction, "_git", fake_git)
    assert classify_source(source).mode is SourceMode.LOCAL_CLEAN_COMMIT
    monkeypatch.setenv("AI_COCKPIT_TEMPLATE_CUSTOM_SOURCE", "1")
    assert classify_source(source).mode is SourceMode.CUSTOM_SOURCE
    monkeypatch.delenv("AI_COCKPIT_TEMPLATE_CUSTOM_SOURCE")
    monkeypatch.setenv("AI_COCKPIT_TEMPLATE_PRIVATE_MIRROR", "1")
    assert classify_source(source).mode is SourceMode.PRIVATE_MIRROR


def test_classify_dirty_checkout(tmp_path, monkeypatch):
    source = make_source(tmp_path / "source")

    def fake_git(_source, *args):
        stdout = "true" if args == ("rev-parse", "--is-inside-work-tree") else " M file.py"
        return transaction.subprocess.CompletedProcess(["git"], 0, stdout, "")

    monkeypatch.setattr(transaction, "_git", fake_git)
    assert classify_source(source).mode is SourceMode.LOCAL_DIRTY_WORKTREE


def test_classify_git_status_failure_is_unknown(tmp_path, monkeypatch):
    source = make_source(tmp_path / "source")

    def fake_git(_source, *args):
        if args == ("rev-parse", "--is-inside-work-tree"):
            return transaction.subprocess.CompletedProcess(["git"], 0, "true", "")
        return transaction.subprocess.CompletedProcess(["git"], 1, "", "error")

    monkeypatch.setattr(transaction, "_git", fake_git)
    assert classify_source(source).mode is SourceMode.UNKNOWN_SOURCE


def test_write_plan_deduplicates_actions(tmp_path):
    target = tmp_path / "target"
    path = target / "file"
    plan = WritePlan([])
    action = TransactionAction("write", path, "first")
    plan.add(action)
    plan.add(TransactionAction("overwrite", path, "second"))
    assert plan.actions == [action]


def test_write_plan_rejects_absolute_path_outside_target(tmp_path):
    plan = WritePlan([TransactionAction("write", tmp_path / "outside", "bad")])
    with pytest.raises(ValueError, match="escapes"):
        plan.validate(tmp_path / "target")


def test_write_plan_rejects_traversal_and_outside_target(tmp_path):
    plan = WritePlan([TransactionAction("write", tmp_path / "target" / "ok", "ok")])
    plan.add(TransactionAction("write", tmp_path / "target" / ".." / "escape", "bad"))
    with pytest.raises(ValueError, match="traversal|escapes"):
        plan.validate(tmp_path / "target")


def test_installer_lock_is_exclusive_and_releases(tmp_path):
    path = tmp_path / ".ai" / "cockpit" / ".install.lock"
    first = InstallerLock(path)
    second = InstallerLock(path)
    first.acquire()
    with pytest.raises(RuntimeError, match="locked"):
        second.acquire()
    first.release()
    second.acquire()
    second.release()
    assert not path.exists()
