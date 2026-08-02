import stat
from pathlib import Path

from installer.conflict_matrix import classify_installation_conflicts, classify_relative_path


def test_empty_target_is_safe_and_inspection_is_read_only(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    findings = classify_installation_conflicts(tmp_path)

    assert findings == []
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before


def test_detects_required_filesystem_conflicts(tmp_path: Path) -> None:
    (tmp_path / ".ai").mkdir()
    (tmp_path / "AGENTS.md").write_text("existing", encoding="utf-8")
    (tmp_path / "Makefile").write_text("ai-start:\n", encoding="utf-8")
    (tmp_path / "agents.md").write_text("case conflict", encoding="utf-8")
    (tmp_path / ".ai" / ".installing").write_text("interrupted", encoding="utf-8")
    (tmp_path / ".ai" / ".install.lock").write_text("concurrent", encoding="utf-8")
    (tmp_path / ".ai" / "cockpit").mkdir()
    (tmp_path / ".ai" / "cockpit" / "upgrade-conflict-report.json").write_text(
        "{}", encoding="utf-8"
    )
    (tmp_path / ".ai" / "work-items" / "active").mkdir(parents=True)
    (tmp_path / ".ai" / "work-items" / "active" / "open.contract.json").write_text(
        "{}", encoding="utf-8"
    )
    (tmp_path / "readonly").mkdir()
    (tmp_path / "readonly").chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        findings = classify_installation_conflicts(tmp_path)
    finally:
        (tmp_path / "readonly").chmod(stat.S_IRWXU)

    states = {finding.scenario: finding.status for finding in findings}
    assert states["existing_ai"] == "requires_review"
    assert states["existing_agents"] == "requires_review"
    assert states["reserved_make_target"] == "blocked"
    assert states["case_conflict"] == "requires_review"
    assert states["interrupted_install"] == "requires_review"
    assert states["concurrent_install"] == "blocked"
    assert states["failed_upgrade"] == "requires_review"
    assert states["active_work_item"] == "blocked"
    assert states["read_only_path"] == "blocked"


def test_detects_git_symlink_nested_and_submodule_markers(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("deadbeef\n", encoding="utf-8")
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
    (tmp_path / "nested" / ".git").mkdir(parents=True)
    (tmp_path / "submodule").mkdir()
    (tmp_path / "submodule" / ".git").write_text(
        "gitdir: ../.git/modules/submodule\n", encoding="utf-8"
    )
    (tmp_path / "linked").symlink_to(tmp_path / "outside")

    states = {
        finding.scenario: finding.status for finding in classify_installation_conflicts(tmp_path)
    }

    assert states["detached_head"] == "warning"
    assert states["dirty_worktree"] == "warning"
    assert states["nested_git"] == "requires_review"
    assert states["submodule"] == "requires_review"
    assert states["symlink"] == "blocked"


def test_path_traversal_and_modified_managed_file_are_blocked_or_reviewed(tmp_path: Path) -> None:
    (tmp_path / ".ai" / "guards").mkdir(parents=True)
    (tmp_path / ".ai" / "guards" / "checks.yaml").write_text("modified", encoding="utf-8")

    states = {
        finding.scenario: finding.status for finding in classify_installation_conflicts(tmp_path)
    }

    assert classify_relative_path("../escape") == "blocked"
    assert states["modified_managed_file"] == "requires_review"
