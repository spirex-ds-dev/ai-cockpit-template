import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.ai_capability_truth as capability_truth
import scripts.check_release_preflight as preflight
import scripts.finalize_release_freeze as finalizer
from scripts import release_archive
from scripts.ai_capability_freshness import current_environment, make_record
from scripts.check_release_preflight import (
    ReleasePreflightError,
    _load_object,
    resolve_release_identity_ref,
    validate_release_identity,
    validate_release_preflight,
)


def _fixture(**overrides):
    values = {
        "release": {"releaseArchive": {"sha256": "abc"}},
        "release_digests": {"sourceCommit": "HEAD"},
        "source_commit": "HEAD",
        "freeze": {
            "state": "frozen",
            "sourceTree": "tree",
            "archiveSha256": "abc",
            "lifecycle": {
                "state": "closed_and_synchronized",
                "command": "make ai-close-work-item",
                "baseCommit": "tree",
                "worktreeClean": True,
            },
        },
        "actual_archive_sha": "abc",
        "source_tree": "tree",
        "active_work_items": [],
        "archive_count": 10,
        "archive_max": 10,
    }
    values.update(overrides)
    return values


def test_release_preflight_rejects_missing_malformed_or_mismatched_installer_digest():
    installer_sha = hashlib.sha256(b"installer\n").hexdigest()

    assert preflight.validate_installer_digest({}, installer_sha) == [
        "release.json installerDigest is missing or invalid"
    ]
    assert preflight.validate_installer_digest({"installerDigest": "bad"}, installer_sha) == [
        "release.json installerDigest is missing or invalid"
    ]
    assert preflight.validate_installer_digest({"installerDigest": "0" * 64}, installer_sha) == [
        "release.json installerDigest does not match source install.sh"
    ]
    assert (
        preflight.validate_installer_digest({"installerDigest": installer_sha}, installer_sha) == []
    )


def test_release_preflight_rejects_source_version_that_disagrees_with_requested_tag():
    assert preflight.validate_source_release_version({"releaseVersion": "0.5.32"}, "v0.5.50") == [
        "source version.json releaseVersion '0.5.32' does not match requested release tag v0.5.50"
    ]
    assert preflight.validate_source_release_version({"releaseVersion": "0.5.50"}, "v0.5.50") == []


def test_release_preflight_source_readers_bind_and_reject_exact_source_bytes(monkeypatch, tmp_path):
    def source_bytes(*_args, **_kwargs):
        return SimpleNamespace(stdout=b"source installer\n")

    monkeypatch.setattr(preflight.subprocess, "run", source_bytes)
    assert (
        preflight.source_file_sha256(tmp_path, "a" * 40, "install.sh")
        == hashlib.sha256(b"source installer\n").hexdigest()
    )

    def source_json(*_args, **_kwargs):
        return SimpleNamespace(stdout='{"releaseVersion":"0.5.50"}')

    monkeypatch.setattr(preflight.subprocess, "run", source_json)
    assert preflight.source_json_object(tmp_path, "a" * 40, ".ai/cockpit/version.json") == {
        "releaseVersion": "0.5.50"
    }

    def unreadable_source(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["git", "show"])

    monkeypatch.setattr(preflight.subprocess, "run", unreadable_source)
    with pytest.raises(ReleasePreflightError, match="release source file cannot be read"):
        preflight.source_file_sha256(tmp_path, "a" * 40, "install.sh")
    with pytest.raises(ReleasePreflightError, match="release source JSON cannot be read"):
        preflight.source_json_object(tmp_path, "a" * 40, ".ai/cockpit/version.json")

    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="[]"),
    )
    with pytest.raises(ReleasePreflightError, match="release source JSON must be an object"):
        preflight.source_json_object(tmp_path, "a" * 40, ".ai/cockpit/version.json")


def test_release_preflight_reports_projection_and_identity_tuple_drift():
    projection_issues = preflight.validate_release_projection(
        state={
            "state": "candidate_prepared",
            "releaseTag": "v0.5.50",
            "previousRelease": "v0.5.48",
        },
        release={"releaseTag": "v0.5.49"},
        candidate={"releaseTag": "v0.5.51", "basedOnReleaseTag": "v0.5.48"},
    )
    assert projection_issues == [
        "canonical candidate releaseTag does not match next-release.json",
        "canonical previousRelease does not match release.json releaseTag",
        "next-release.json basedOnReleaseTag does not match release.json releaseTag",
    ]

    identity_issues = validate_release_identity(
        release={"releaseTag": "v0.5.50"},
        freeze={"releaseTag": "v0.5.49"},
        release_digests={"releaseTag": "v0.5.49"},
        source_commit="invalid",
        tag_target="b" * 40,
        metadata_commit="",
    )
    assert "sourceCommit must be a concrete 40-character lowercase SHA" in identity_issues
    assert "metadataCommit must be a concrete 40-character lowercase SHA" in identity_issues
    assert "sourceCommit and tagTarget must identify the same commit" in identity_issues
    assert "freeze sourceCommit does not match the release identity tuple" in identity_issues
    assert (
        "release-digests tagTarget must be a concrete 40-character lowercase SHA" in identity_issues
    )
    assert "releaseTag must match between release.json and release-freeze.json" in identity_issues


def test_release_preflight_blocks_active_work_item_and_stale_digest():
    issues = validate_release_preflight(
        **_fixture(active_work_items=["task"], actual_archive_sha="new")
    )
    assert any("active Work Items" in issue for issue in issues)
    assert any("releaseArchive.sha256" in issue for issue in issues)
    assert any("release freeze archiveSha256" in issue for issue in issues)


def test_release_preflight_blocks_archive_budget_overflow_and_unfrozen_state():
    issues = validate_release_preflight(**_fixture(freeze={"state": "candidate"}, archive_count=11))
    assert any("archiveGrowth=11" in issue for issue in issues)
    assert any("state must be frozen" in issue for issue in issues)


def test_release_preflight_warns_on_archive_growth_when_policy_is_warning_only():
    assert (
        validate_release_preflight(
            **_fixture(archive_count=538, archive_max=200, archive_enforcement="warning")
        )
        == []
    )


def test_release_preflight_blocks_freeze_created_before_close():
    freeze = _fixture()["freeze"]
    del freeze["lifecycle"]
    issues = validate_release_preflight(**_fixture(freeze=freeze))
    assert any("finalized after Work Item archive" in issue for issue in issues)


def test_release_preflight_accepts_archive_bound_premerge_freeze():
    freeze = _fixture()["freeze"]
    freeze["lifecycle"] = {
        "state": "premerge_finalized",
        "command": "make finalize-release-freeze-premerge TASK=task",
        "baseCommit": "tree",
        "worktreeClean": True,
    }
    assert validate_release_preflight(**_fixture(freeze=freeze)) == []


def test_release_preflight_blocks_stale_digest_source_commit():
    issues = validate_release_preflight(**_fixture(release_digests={"sourceCommit": "old"}))
    assert any("release-digests sourceCommit" in issue for issue in issues)


def test_release_preflight_rejects_metadata_commit_drift():
    source = "a" * 40
    metadata = "b" * 40
    issues = validate_release_identity(
        release={"releaseTag": "v0.5.40"},
        freeze={
            "sourceCommit": source,
            "tagTarget": source,
            "metadataCommit": "c" * 40,
            "releaseTag": "v0.5.40",
        },
        release_digests={
            "sourceCommit": source,
            "tagTarget": source,
            "metadataCommit": metadata,
            "releaseTag": "v0.5.40",
        },
        source_commit=source,
        tag_target=source,
        metadata_commit=metadata,
    )
    assert any("metadataCommit" in issue for issue in issues)


def test_canonical_archive_helper_covers_current_source():
    source = preflight.resolve_source_commit(Path.cwd(), "HEAD")
    assert len(preflight.canonical_archive_sha(Path.cwd(), source)) == 64


def _commit_worktree_file(repo: Path, relative_path: str, content: str) -> str:
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "add", relative_path)
    _git(repo, "commit", "-m", "initial")
    return _git(repo, "rev-parse", "HEAD")


def test_worktree_archive_uses_current_tracked_file_bytes(tmp_path: Path):
    source = _commit_worktree_file(tmp_path, "tracked.txt", "before\n")
    (tmp_path / "tracked.txt").write_text("after\n", encoding="utf-8")

    archive = release_archive.canonical_tar_from_worktree(tmp_path, source)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as contents:
        member = contents.extractfile("ai-cockpit/tracked.txt")
        assert member is not None
        assert member.read() == b"after\n"

    compressed = release_archive.canonical_archive_bytes_from_worktree(tmp_path, source)
    assert gzip.decompress(compressed) == archive
    assert len(release_archive.canonical_source_tree_from_worktree(tmp_path, source)) == 64
    assert len(release_archive.canonical_archive_sha_from_worktree(tmp_path, source)) == 64
    assert release_archive.canonical_source_tree(tmp_path, source) != (
        release_archive.canonical_source_tree_from_worktree(tmp_path, source)
    )
    assert len(release_archive.canonical_archive_sha(tmp_path, source)) == 64


def test_worktree_archive_rejects_symlinked_tracked_member(tmp_path: Path):
    source = _commit_worktree_file(tmp_path, "tracked.txt", "before\n")
    external = tmp_path / "external.txt"
    external.write_text("outside\n", encoding="utf-8")
    (tmp_path / "tracked.txt").unlink()
    (tmp_path / "tracked.txt").symlink_to(external)

    with pytest.raises(ValueError, match="not a regular file"):
        release_archive.canonical_tar_from_worktree(tmp_path, source)


def test_worktree_archive_rejects_symlinked_parent(tmp_path: Path):
    source = _commit_worktree_file(tmp_path, "nested/tracked.txt", "before\n")
    external = tmp_path / "external"
    external.mkdir()
    (external / "tracked.txt").write_text("outside\n", encoding="utf-8")
    shutil.rmtree(tmp_path / "nested")
    (tmp_path / "nested").symlink_to(external, target_is_directory=True)

    with pytest.raises(ValueError, match="not a regular file"):
        release_archive.canonical_tar_from_worktree(tmp_path, source)


def test_release_archive_cli_writes_canonical_git_archive(monkeypatch, tmp_path: Path):
    source = _commit_worktree_file(tmp_path, "tracked.txt", "content\n")
    output = tmp_path / "archive.tar.gz"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "release_archive",
            "--root",
            str(tmp_path),
            "--source-commit",
            source,
            "--output",
            str(output),
        ],
    )

    assert release_archive.main() == 0
    assert output.read_bytes() == release_archive.canonical_archive_bytes(tmp_path, source)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _run_release_preflight(
    repo: Path, source_ref: str, *, mode: str = "exact-source"
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "check_release_preflight.py"),
            "--root",
            str(repo),
            "--source-commit",
            source_ref,
            "--mode",
            mode,
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
    )


def _build_candidate_merge(tmp_path: Path) -> tuple[Path, Path, str]:
    source_root = Path.cwd()
    repo = tmp_path / "source"
    remote = tmp_path / "origin.git"
    fresh = tmp_path / "fresh"
    repo.mkdir()
    for relative in (
        "ai_common.py",
        "finalize_release_freeze.py",
        "check_release_preflight.py",
        "release_archive.py",
    ):
        target = repo / "scripts" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / "scripts" / relative, target)
    (repo / "scripts" / "check_supply_chain.py").write_text(
        "import hashlib\n\n"
        "def sha256_text(value: str) -> str:\n"
        "    return hashlib.sha256(value.encode()).hexdigest()\n",
        encoding="utf-8",
    )
    for name in (
        "ai_capability_truth.py",
        "ai_japanese_capability.py",
        "check_pre_release_documentation_alignment.py",
    ):
        (repo / "scripts" / name).write_text("raise SystemExit(0)\n", encoding="utf-8")
    (repo / ".gitattributes").write_text(
        "release.json export-ignore\n"
        "next-release.json export-ignore\n"
        "release-state.json export-ignore\n"
        ".ai/cockpit/release-digests.json export-ignore\n"
        ".ai/cockpit/release-freeze.json export-ignore\n"
        ".ai/work-items/archive export-ignore\n"
        ".ai/work-items/active export-ignore\n"
        ".ai/cockpit/current_status.md export-ignore\n",
        encoding="utf-8",
    )
    (repo / "source.txt").write_text("base\n", encoding="utf-8")
    (repo / "install.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    installer_digest = hashlib.sha256((repo / "install.sh").read_bytes()).hexdigest()
    (repo / ".ai" / "cockpit").mkdir(parents=True)
    (repo / ".ai" / "cockpit" / "current_status.md").write_text(
        "- State: `no_active_work_item`\n", encoding="utf-8"
    )
    _write_json(
        repo / ".ai" / "cockpit" / "version.json",
        {"distributionVersion": 2, "contractSchema": 2, "releaseVersion": "0.5.40"},
    )
    _write_json(repo / ".ai" / "cockpit" / "release-freeze.json", {"state": "candidate"})
    _write_json(
        repo / ".ai" / "cockpit" / "release-digests.json",
        {"sourceCommit": "old", "artifacts": {}},
    )
    _write_json(
        repo / "release.json",
        {
            "releaseTag": "v0.5.39",
            "installerDigest": installer_digest,
            "releaseArchive": {"sha256": "old"},
        },
    )
    _write_json(
        repo / "next-release.json",
        {"releaseTag": "v0.5.40", "basedOnReleaseTag": "v0.5.39"},
    )
    _write_json(
        repo / "release-state.json",
        {
            "state": "candidate_prepared",
            "releaseTag": "v0.5.40",
            "previousRelease": "v0.5.39",
            "metadataDigests": {"published": "old"},
        },
    )
    policy = repo / ".ai" / "guards" / "governance_complexity_policy.yaml"
    policy.parent.mkdir(parents=True)
    policy.write_text(
        "max:\n  archiveGrowth: 538\nenforcement:\n  archiveGrowth: warning\n",
        encoding="utf-8",
    )
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release-test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base")
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    subprocess.run(
        ["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True,
    )
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-q", "-u", "origin", "main")
    _git(repo, "remote", "set-head", "origin", "main")
    _git(repo, "switch", "-q", "-c", "candidate")
    (repo / "source.txt").write_text("candidate\n", encoding="utf-8")
    contract = repo / ".ai" / "work-items" / "archive" / "2026" / "task.contract.json"
    _write_json(
        contract,
        {
            "scope": [
                "release.json",
                "release-state.json",
                ".ai/cockpit/release-freeze.json",
                ".ai/cockpit/release-digests.json",
            ]
        },
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "candidate")
    subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "finalize_release_freeze.py"),
            "--premerge-task",
            "task",
            "--source-commit",
            "origin/main",
            "--tag-target",
            "origin/main",
            "--metadata-commit",
            "origin/main",
        ],
        cwd=repo,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "freeze candidate")
    _git(repo, "switch", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "candidate", "-m", "merge candidate")
    merge_commit = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "-q", "origin", "main")
    _git(fresh.parent, "init", "-q", str(fresh))
    _git(fresh, "remote", "add", "origin", str(remote))
    _git(fresh, "fetch", "-q", "origin", "main:refs/remotes/origin/main")
    _git(fresh, "checkout", "--detach", "-q", merge_commit)
    return repo, fresh, merge_commit


def test_candidate_freeze_survives_real_no_ff_merge_and_detached_preflight(tmp_path):
    _, fresh, merge_commit = _build_candidate_merge(tmp_path)
    result = _run_release_preflight(fresh, "origin/main")
    assert result.returncode == 0, result.stderr
    assert f"source={merge_commit}" in result.stdout
    assert "release preflight passed" in result.stdout


def test_postmerge_preflight_rejects_included_content_after_candidate_merge(tmp_path):
    repo, fresh, _ = _build_candidate_merge(tmp_path)
    (repo / "source.txt").write_text("post-merge drift\n", encoding="utf-8")
    _git(repo, "add", "source.txt")
    _git(repo, "commit", "-q", "-m", "drift after merge")
    drift_commit = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "-q", "origin", "main")
    _git(fresh, "fetch", "-q", "origin", "main:refs/remotes/origin/main")
    _git(fresh, "checkout", "--detach", "-q", drift_commit)
    result = _run_release_preflight(fresh, "origin/main")
    assert result.returncode == 1
    assert "release preflight blocked" in result.stderr
    assert "archiveSha256 does not match regenerated archive" in result.stderr


def test_repository_readiness_accepts_included_content_after_historical_freeze(tmp_path):
    repo, fresh, _ = _build_candidate_merge(tmp_path)
    (repo / "source.txt").write_text("post-merge correction\n", encoding="utf-8")
    _git(repo, "add", "source.txt")
    _git(repo, "commit", "-q", "-m", "correction after historical freeze")
    correction_commit = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "-q", "origin", "main")
    _git(fresh, "fetch", "-q", "origin", "main:refs/remotes/origin/main")
    _git(fresh, "checkout", "--detach", "-q", correction_commit)

    result = _run_release_preflight(fresh, "origin/main", mode="repository-readiness")

    assert result.returncode == 0, result.stderr
    assert "release readiness passed" in result.stdout


def test_repository_readiness_keeps_policy_fail_closed_without_freeze_bytes():
    state = {
        "state": "candidate_prepared",
        "releaseTag": "v0.5.45",
        "previousRelease": "v0.5.44",
    }
    release = {"releaseTag": "v0.5.44"}
    candidate = {"releaseTag": "v0.5.45", "basedOnReleaseTag": "v0.5.44"}

    assert (
        preflight.validate_repository_readiness(
            state=state,
            release=release,
            candidate=candidate,
            active_work_items=[],
            archive_count=201,
            archive_max=200,
            archive_enforcement="warning",
        )
        == []
    )
    issues = preflight.validate_repository_readiness(
        state=state,
        release=release,
        candidate=candidate,
        active_work_items=["still-active"],
        archive_count=201,
        archive_max=200,
        archive_enforcement="error",
    )
    assert "active Work Items remain: still-active" in issues
    assert "archiveGrowth=201 exceeds configured maximum 200" in issues


def test_repository_readiness_allows_only_current_authorized_release_work_item(tmp_path):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    contract = {
        "workItemId": "release-v0550-publication-current-main",
        "baseCommit": "a" * 40,
        "requestedOperation": {
            "target": "repository_release",
            "action": "publish",
            "environment": "public_provider",
            "effect": "create_immutable_release_tag_and_public_assets",
            "authorityRequired": True,
        },
        "authorityEvidence": {"type": "user_authorization", "authorizedBy": "RayIori"},
        "executionDecision": {"status": "continue"},
    }
    (active / "release-v0550-publication-current-main.contract.json").write_text(
        json.dumps(contract), encoding="utf-8"
    )

    assert (
        preflight.release_readiness_active_work_item_issues(
            tmp_path, ["release-v0550-publication-current-main"]
        )
        == []
    )

    contract["authorityEvidence"] = {}
    (active / "release-v0550-publication-current-main.contract.json").write_text(
        json.dumps(contract), encoding="utf-8"
    )
    assert preflight.release_readiness_active_work_item_issues(
        tmp_path, ["release-v0550-publication-current-main"]
    ) == ["active Work Items remain: release-v0550-publication-current-main"]

    (active / "ordinary.contract.json").write_text("{}", encoding="utf-8")
    assert preflight.release_readiness_active_work_item_issues(
        tmp_path, ["ordinary", "release-v0550-publication-current-main"]
    ) == ["active Work Items remain: ordinary, release-v0550-publication-current-main"]


def test_repository_policy_context_reads_active_work_items_and_warning_policy(tmp_path):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    (active / "z.contract.json").write_text("{}\n", encoding="utf-8")
    (active / "a.contract.json").write_text("{}\n", encoding="utf-8")
    archive = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive.mkdir(parents=True)
    (archive / "one.contract.json").write_text("{}\n", encoding="utf-8")
    policy = tmp_path / ".ai" / "guards" / "governance_complexity_policy.yaml"
    policy.parent.mkdir(parents=True)
    policy.write_text(
        "max:\n  archiveGrowth: 200\nenforcement:\n  archiveGrowth: warning\n",
        encoding="utf-8",
    )

    assert preflight.repository_policy_context(tmp_path) == (
        ["a", "z"],
        1,
        200,
        "warning",
    )


def test_release_identity_ref_rejects_head():
    with pytest.raises(ReleasePreflightError, match="concrete SHA or controlled origin ref"):
        resolve_release_identity_ref(Path.cwd(), "HEAD", "metadataCommit")


def test_load_object_rejects_invalid_json(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ReleasePreflightError, match="must be a JSON object"):
        _load_object(path, "fixture")


def test_load_object_rejects_malformed_json(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ReleasePreflightError, match="missing or invalid"):
        _load_object(path, "fixture")


def test_finalize_release_freeze_requires_clean_synchronized_default_branch(monkeypatch, tmp_path):
    monkeypatch.setattr(finalizer, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(finalizer, "discover_remote_default_candidates", lambda _run: [])
    assert finalizer.main() == 1


def _configure_finalizer(
    monkeypatch,
    tmp_path: Path,
    *,
    branch: str = "main",
    head: str = "commit",
    remote_head: str = "commit",
    active_task: str | None = None,
    release_state: str = '{"metadataDigests":{"published":"old"}}\n',
) -> list[tuple[str, str]]:
    (tmp_path / ".ai" / "cockpit").mkdir(parents=True)
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    if active_task is not None:
        (active / f"{active_task}.contract.json").write_text(
            '{"scope":["release.json","release-state.json",".ai/cockpit/release-freeze.json",'
            '".ai/cockpit/release-digests.json"]}\n',
            encoding="utf-8",
        )
    (tmp_path / ".ai" / "cockpit" / "current_status.md").write_text(
        "- State: `no_active_work_item`\n", encoding="utf-8"
    )
    (tmp_path / ".ai" / "cockpit" / "release-freeze.json").write_text(
        '{"state":"candidate"}\n', encoding="utf-8"
    )
    (tmp_path / ".ai" / "cockpit" / "release-digests.json").write_text(
        '{"format":"ai-cockpit-release-digests","version":1,"sourceCommit":"old",'
        '"releaseTag":"v0.5.39","artifacts":{"install.sh":"stale","release.json":"old"}}\n',
        encoding="utf-8",
    )
    (tmp_path / "release.json").write_text(
        '{"releaseTag":"v0.5.39","installerDigest":"old","releaseArchive":{"sha256":"old"}}\n',
        encoding="utf-8",
    )
    (tmp_path / "install.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (tmp_path / "release-state.json").write_text(release_state, encoding="utf-8")
    monkeypatch.setattr(finalizer, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        finalizer, "discover_remote_default_candidates", lambda _run: [("origin", "main")]
    )

    def fake_git(args):
        outputs = {
            ("branch", "--show-current"): f"{branch}\n",
            ("status", "--porcelain", "--untracked-files=all"): "",
            ("rev-parse", "HEAD"): f"{head}\n",
            ("rev-parse", "origin/main"): f"{remote_head}\n",
            ("rev-parse", "runtime^{commit}"): "runtime\n",
        }
        return SimpleNamespace(returncode=0, stdout=outputs.get(tuple(args), ""), stderr="")

    monkeypatch.setattr(finalizer, "run_git", fake_git)
    materialized = []
    monkeypatch.setattr(
        finalizer,
        "canonical_source_tree_from_worktree",
        lambda _root, commit: materialized.append(("tree", commit)) or "tree",
    )
    monkeypatch.setattr(
        finalizer,
        "canonical_archive_sha_from_worktree",
        lambda _root, commit: materialized.append(("archive", commit)) or "archive",
    )
    monkeypatch.setattr(finalizer, "refresh_release_derived_reports", lambda _root: None)
    return materialized


def _archive_finalizer_task(tmp_path: Path) -> None:
    archive = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive.mkdir(parents=True)
    (archive / "task.contract.json").write_text(
        '{"scope":["release.json","release-state.json",".ai/cockpit/release-freeze.json",'
        '".ai/cockpit/release-digests.json"]}\n',
        encoding="utf-8",
    )


def _finalize_premerge(source_identity: str) -> int:
    return finalizer.main(
        premerge_task="task",
        source_commit=source_identity,
        tag_target=source_identity,
        metadata_commit=source_identity,
    )


def test_finalize_release_freeze_writes_post_close_lifecycle_evidence(monkeypatch, tmp_path):
    _configure_finalizer(monkeypatch, tmp_path)

    assert (
        finalizer.main(
            source_commit="a" * 40,
            tag_target="a" * 40,
            metadata_commit="b" * 40,
        )
        == 0
    )
    freeze = json.loads((tmp_path / ".ai" / "cockpit" / "release-freeze.json").read_text())
    assert freeze["lifecycle"]["state"] == "closed_and_synchronized"
    assert freeze["lifecycle"]["command"] == "make ai-close-work-item"
    assert freeze["sourceCommit"] == "a" * 40
    assert freeze["tagTarget"] == "a" * 40
    assert freeze["metadataCommit"] == "b" * 40
    release = json.loads((tmp_path / "release.json").read_text())
    assert release["releaseArchive"]["sha256"] == "archive"
    assert (
        release["installerDigest"]
        == hashlib.sha256((tmp_path / "install.sh").read_bytes()).hexdigest()
    )
    verification = release["capabilities"]["sha256ArchiveVerification"]
    assert verification["supported"] is True
    assert verification["verified"] is True
    assert verification["status"] == "verified"
    release_state = json.loads((tmp_path / "release-state.json").read_text())
    assert (
        release_state["metadataDigests"]["published"]
        == hashlib.sha256((tmp_path / "release.json").read_bytes()).hexdigest()
    )
    release_digests = json.loads(
        (tmp_path / ".ai" / "cockpit" / "release-digests.json").read_text()
    )
    assert release_digests["sourceCommit"] == "a" * 40
    assert release_digests["tagTarget"] == "a" * 40
    assert release_digests["metadataCommit"] == "b" * 40
    assert release_digests["artifacts"] == {
        "release.json": hashlib.sha256((tmp_path / "release.json").read_bytes()).hexdigest(),
        "install.sh": hashlib.sha256((tmp_path / "install.sh").read_bytes()).hexdigest(),
    }


def test_finalizer_preserves_capability_truth_without_release_metadata_self_reference(
    monkeypatch, tmp_path
):
    """Breaks if mutable release metadata is bound into its own archive evidence."""
    _configure_finalizer(monkeypatch, tmp_path)
    evidence = tmp_path / "tests" / "release_evidence.py"
    evidence.parent.mkdir()
    evidence.write_text("# release evidence\n", encoding="utf-8")
    matrix_path = tmp_path / "docs" / "reference" / "capability-truth-matrix.json"
    _write_json(
        matrix_path,
        {
            "statusVocabulary": [
                "implemented",
                "template_only",
                "adopter_installed",
                "planned",
            ],
            "capabilities": [
                {
                    "id": "quick_install_release_archive_digest",
                    "status": "implemented",
                    "claim": "Release metadata is evidence-bound.",
                    "limitations": "Fixture only.",
                    "sourceEvidence": ["install.sh"],
                    "testEvidence": ["tests/release_evidence.py"],
                    "commandEvidence": ["make check-release-preflight"],
                    "freshness": make_record(
                        environment=current_environment(),
                        scope=["install.sh", "tests/release_evidence.py"],
                        now=datetime.now(UTC),
                    ),
                    "evidenceSource": capability_truth.build_evidence_source(
                        ["install.sh"], ["tests/release_evidence.py"], root=tmp_path
                    ),
                }
            ],
        },
    )
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["capabilities"][0]["digest"] = capability_truth.row_digest(matrix["capabilities"][0])
    _write_json(matrix_path, matrix)

    assert finalizer.main(source_commit="a" * 40, tag_target="a" * 40) == 0
    assert capability_truth.validate_matrix(matrix_path, root=tmp_path) == []


def test_finalizer_refreshes_derived_reports_before_worktree_archive_binding(monkeypatch, tmp_path):
    _configure_finalizer(monkeypatch, tmp_path)
    events: list[str] = []
    monkeypatch.setattr(
        finalizer,
        "refresh_release_derived_reports",
        lambda _root: events.append("refresh"),
        raising=False,
    )
    monkeypatch.setattr(
        finalizer,
        "canonical_source_tree_from_worktree",
        lambda _root, _commit: events.append("tree") or "tree",
    )
    monkeypatch.setattr(
        finalizer,
        "canonical_archive_sha_from_worktree",
        lambda _root, _commit: events.append("archive") or "archive",
    )
    monkeypatch.setattr(finalizer, "regenerate_capability_truth", lambda _root: None)

    assert finalizer.main(source_commit="a" * 40, tag_target="a" * 40) == 0
    assert events == ["refresh", "tree", "archive"]


def test_finalize_release_freeze_runtime_mode_binds_exact_detached_source(monkeypatch, tmp_path):
    materialized = _configure_finalizer(
        monkeypatch,
        tmp_path,
        branch="",
        head="runtime",
        remote_head="default",
    )

    assert finalizer.main(runtime_source_commit="runtime", runtime_default_branch="main") == 0
    assert materialized == [("tree", "runtime"), ("archive", "runtime")]
    freeze = json.loads((tmp_path / ".ai" / "cockpit" / "release-freeze.json").read_text())
    assert freeze["sourceCommit"] == "runtime"
    assert freeze["tagTarget"] == "runtime"
    assert freeze["metadataCommit"] == "runtime"
    assert freeze["lifecycle"]["state"] == "closed_and_synchronized"
    assert freeze["lifecycle"]["defaultBranch"] == "main"


def test_runtime_release_freeze_does_not_rewrite_source_bound_capability_truth(
    monkeypatch, tmp_path
):
    _configure_finalizer(monkeypatch, tmp_path, branch="", head="runtime", remote_head="default")
    regenerated = []
    monkeypatch.setattr(
        finalizer,
        "regenerate_capability_truth",
        lambda _root: regenerated.append("matrix"),
    )

    assert finalizer.main(runtime_source_commit="runtime", runtime_default_branch="main") == 0
    assert regenerated == []


def test_finalize_release_freeze_runtime_requires_controlled_default_branch(monkeypatch, tmp_path):
    _configure_finalizer(monkeypatch, tmp_path, branch="", head="runtime")

    assert finalizer.main(runtime_source_commit="runtime") == 1
    assert finalizer.main(runtime_source_commit="runtime", runtime_default_branch="../main") == 1


def test_finalize_release_freeze_imports_without_optional_supply_chain_packages():
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            "import finalize_release_freeze; assert finalize_release_freeze.sha256_text('x')",
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "scripts")},
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_finalize_release_freeze_fails_closed_on_malformed_release_state(monkeypatch, tmp_path):
    _configure_finalizer(monkeypatch, tmp_path, release_state="[]\n")
    assert finalizer.main() == 1


def test_finalize_release_freeze_candidate_mode_binds_to_work_item_branch(monkeypatch, tmp_path):
    _configure_finalizer(
        monkeypatch,
        tmp_path,
        branch="codex/task",
        head="candidate-commit",
        remote_head="default-commit",
        active_task="task",
    )

    assert finalizer.main(candidate_task="task") == 0
    freeze = json.loads((tmp_path / ".ai" / "cockpit" / "release-freeze.json").read_text())
    assert freeze["lifecycle"]["state"] == "candidate_prepared"
    assert freeze["lifecycle"]["candidateBranch"] == "codex/task"
    assert freeze["lifecycle"]["defaultBranch"] == "main"


def test_finalize_release_freeze_premerge_requires_archived_work_item(monkeypatch, tmp_path):
    materialized = _configure_finalizer(
        monkeypatch,
        tmp_path,
        branch="codex/task",
        remote_head="old-commit",
    )

    assert _finalize_premerge("origin/main") == 1
    _archive_finalizer_task(tmp_path)
    assert _finalize_premerge("origin/main") == 0
    assert materialized == [("tree", "commit"), ("archive", "commit")]
    freeze = json.loads((tmp_path / ".ai" / "cockpit" / "release-freeze.json").read_text())
    assert freeze["lifecycle"]["state"] == "premerge_finalized"
    assert freeze["lifecycle"]["command"] == "make finalize-release-freeze-premerge TASK=task"


def test_finalize_release_freeze_premerge_rejects_unresolved_source_identity(monkeypatch, tmp_path):
    _archive_finalizer_task(tmp_path)
    materialized = _configure_finalizer(monkeypatch, tmp_path, branch="codex/task")
    release_before = (tmp_path / "release.json").read_bytes()

    assert _finalize_premerge("missing/ref") == 1
    assert materialized == []
    assert (tmp_path / "release.json").read_bytes() == release_before


def test_main_accepts_frozen_candidate(tmp_path, monkeypatch, capsys):
    (tmp_path / ".ai" / "cockpit").mkdir(parents=True)
    (tmp_path / ".ai" / "guards").mkdir(parents=True)
    (tmp_path / ".ai" / "work-items" / "active").mkdir(parents=True)
    (tmp_path / ".ai" / "work-items" / "archive").mkdir(parents=True)
    (tmp_path / "release.json").write_text(
        '{"releaseTag":"v0.5.39","installerDigest":"'
        + "c" * 64
        + '","releaseArchive":{"sha256":"abc"}}',
        encoding="utf-8",
    )
    (tmp_path / "next-release.json").write_text(
        '{"releaseTag":"v0.5.40","basedOnReleaseTag":"v0.5.39"}', encoding="utf-8"
    )
    (tmp_path / "release-state.json").write_text(
        '{"state":"candidate_prepared","releaseTag":"v0.5.40","previousRelease":"v0.5.39"}',
        encoding="utf-8",
    )
    (tmp_path / ".ai" / "cockpit" / "release-freeze.json").write_text(
        '{"state":"frozen","sourceTree":"tree","archiveSha256":"abc",'
        '"sourceCommit":"' + "a" * 40 + '","tagTarget":"' + "a" * 40 + '",'
        '"metadataCommit":"' + "b" * 40 + '","releaseTag":"v0.5.39",'
        '"lifecycle":{"state":"closed_and_synchronized",'
        '"command":"make ai-close-work-item","baseCommit":"tree",'
        '"worktreeClean":true}}',
        encoding="utf-8",
    )
    (tmp_path / ".ai" / "cockpit" / "release-digests.json").write_text(
        '{"sourceCommit":"' + "a" * 40 + '","tagTarget":"' + "a" * 40 + '",'
        '"metadataCommit":"' + "b" * 40 + '","releaseTag":"v0.5.39"}',
        encoding="utf-8",
    )
    (tmp_path / ".ai" / "guards" / "governance_complexity_policy.yaml").write_text(
        "archiveGrowth: 10\n", encoding="utf-8"
    )
    monkeypatch.setattr(preflight, "canonical_archive_sha", lambda root, commit: "abc")
    monkeypatch.setattr(preflight, "canonical_source_tree", lambda root, commit: "tree")
    monkeypatch.setattr(preflight, "resolve_source_commit", lambda root, ref: "a" * 40)
    monkeypatch.setattr(preflight, "source_file_sha256", lambda root, commit, path: "c" * 64)
    monkeypatch.setattr(
        preflight,
        "source_json_object",
        lambda root, commit, path: {"releaseVersion": "0.5.40"},
    )
    monkeypatch.setattr(
        "sys.argv",
        ["check_release_preflight", "--root", str(tmp_path), "--source-commit", "HEAD"],
    )
    assert preflight.main() == 0
    assert "release preflight passed" in capsys.readouterr().out
