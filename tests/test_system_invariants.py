import json
import os
import shutil
from pathlib import Path

import check_system_invariants
import pytest
from check_system_invariants import release_contract_issues

ROOT = Path(__file__).resolve().parents[1]


def write_release_contract_fixture(root, target="quality"):
    (root / "docs" / "getting-started").mkdir(parents=True)
    metadata = {"publicContract": {"projectQualityTarget": target}}
    (root / "release.json").write_text(json.dumps(metadata), encoding="utf-8")
    marker = f"<!-- public-quality-target: {target} -->\n"
    for name in ("installation.md", "installation.ja.md", "installation.zh-CN.md"):
        (root / "docs" / "getting-started" / name).write_text(marker, encoding="utf-8")
    return metadata


def _archive_summary_version_issues(issues):
    return [
        issue
        for issue in issues
        if "archived Summary summaryVersion must be absent or 1/2 when present" in issue
    ]


def _isolated_repository_view(tmp_path, *writable_paths: Path):
    """Build a linked repository view and copy only files this test mutates."""
    copy = tmp_path / "repository"
    shutil.copytree(
        ROOT,
        copy,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".worktrees",
            "target",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
        ),
        copy_function=os.symlink,
    )
    for path in writable_paths:
        destination = copy / path.relative_to(ROOT)
        destination.unlink()
        shutil.copy2(path, destination)
    return copy


def _archive_summary_source() -> Path:
    return next((ROOT / ".ai" / "work-items" / "archive").rglob("*.summary.json"))


def test_release_contract_accepts_consistent_public_quality_target(tmp_path):
    metadata = write_release_contract_fixture(tmp_path)
    assert release_contract_issues(tmp_path, metadata) == []


def test_release_contract_rejects_documentation_drift(tmp_path):
    metadata = write_release_contract_fixture(tmp_path)
    (tmp_path / "docs" / "getting-started" / "installation.ja.md").write_text(
        "<!-- public-quality-target: stale -->\n", encoding="utf-8"
    )
    assert release_contract_issues(tmp_path, metadata) == [
        "docs/getting-started/installation.ja.md: public quality target differs from release.json"
    ]


def test_release_contract_rejects_invalid_target(tmp_path):
    metadata = write_release_contract_fixture(tmp_path, target="quality; rm -rf")
    assert release_contract_issues(tmp_path, metadata) == [
        "release.json public project quality target is missing or invalid"
    ]


@pytest.mark.parametrize("summary_version", [None, 1])
def test_system_invariants_allow_legacy_archive_summary_versions(
    tmp_path, monkeypatch, summary_version
):
    archive_summary_source = _archive_summary_source()
    copy = _isolated_repository_view(tmp_path, archive_summary_source)
    archive_summary = copy / archive_summary_source.relative_to(ROOT)
    data = json.loads(archive_summary.read_text(encoding="utf-8"))
    if summary_version is None:
        data.pop("summaryVersion", None)
    else:
        data["summaryVersion"] = summary_version
    archive_summary.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(
        check_system_invariants, "exercise_installer", lambda *_args, **_kwargs: None
    )
    issues = check_system_invariants.invariant_issues(copy)
    assert _archive_summary_version_issues(issues) == []


def test_system_invariants_reject_archive_summary_invalid_version(tmp_path, monkeypatch):
    archive_summary_source = _archive_summary_source()
    copy = _isolated_repository_view(tmp_path, archive_summary_source)
    archive_summary = copy / archive_summary_source.relative_to(ROOT)
    data = json.loads(archive_summary.read_text(encoding="utf-8"))
    data["summaryVersion"] = 3
    archive_summary.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(
        check_system_invariants, "exercise_installer", lambda *_args, **_kwargs: None
    )
    issues = check_system_invariants.invariant_issues(copy)
    assert _archive_summary_version_issues(issues) == [
        f"{archive_summary.relative_to(copy)}: archived Summary summaryVersion must be absent or 1/2 when present"
    ]


def test_system_invariants_reject_missing_required_baselines(tmp_path, monkeypatch):
    missing_paths = (
        ROOT / "requirements-dev.lock",
        ROOT / ".ai" / "cockpit" / "bandit_low_risk_baseline.json",
        ROOT / ".ai" / "cockpit" / "sbom.json",
        ROOT / ".ai" / "cockpit" / "provenance.json",
        ROOT / "SECURITY.md",
    )
    copy = _isolated_repository_view(tmp_path, *missing_paths)
    for source_path in missing_paths:
        path = copy / source_path.relative_to(ROOT)
        path.unlink()
        assert source_path.is_file()
    monkeypatch.setattr(
        check_system_invariants, "exercise_installer", lambda *_args, **_kwargs: None
    )

    issues = check_system_invariants.invariant_issues(copy)

    assert "requirements-dev.lock is missing" in issues
    assert "bandit low-risk baseline is missing" in issues
    assert "supply-chain SBOM baseline is missing" in issues
    assert "supply-chain provenance baseline is missing" in issues
    assert "SECURITY.md is missing" in issues


def test_system_invariants_ignore_make_options_before_documented_target(tmp_path, monkeypatch):
    copy = _isolated_repository_view(tmp_path)
    assert not (ROOT / "docs" / "make-options.md").exists()
    (copy / "docs" / "make-options.md").write_text(
        "Use `make -n quality` to inspect the dry-run graph.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        check_system_invariants, "exercise_installer", lambda *_args, **_kwargs: None
    )

    issues = check_system_invariants.invariant_issues(copy)

    assert "documentation references missing Make target: -n" not in issues


def test_system_invariants_resolve_makefile_option_before_documented_target(tmp_path, monkeypatch):
    copy = _isolated_repository_view(tmp_path)
    assert not (ROOT / "docs" / "makefile-option.md").exists()
    (copy / "docs" / "makefile-option.md").write_text(
        "Use `make -f Makefile.ai quality-fast` through the installed makefile.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        check_system_invariants, "exercise_installer", lambda *_args, **_kwargs: None
    )

    issues = check_system_invariants.invariant_issues(copy)

    assert "documentation references missing Make target: -f" not in issues
    assert "documentation references missing Make target: Makefile.ai" not in issues
    assert "documentation references missing Make target: quality-fast" not in issues
