import os
import subprocess
from pathlib import Path

import ai_common


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def init_repo(tmp_path: Path) -> str:
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "base")
    return git(tmp_path, "rev-parse", "HEAD")


def test_git_helpers_ignore_ambient_git_dir_and_work_tree(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    other = tmp_path / "other"
    repo.mkdir()
    other.mkdir()
    base = init_repo(repo)
    init_repo(other)
    monkeypatch.setattr(ai_common, "PROJECT_ROOT", repo)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_INDEX_FILE", str(other / "index"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(other / "global.gitconfig"))

    (repo / "tracked.txt").write_text("task\n", encoding="utf-8")

    assert ai_common.current_head() == base
    assert ai_common.changed_paths({"baseCommit": base, "baselineDirtyPaths": []}) == [
        "tracked.txt"
    ]
    assert all(not key.startswith("GIT_") for key in ai_common.clean_git_environment())


def test_committed_changes_since_base_remain_visible(tmp_path, monkeypatch):
    base = init_repo(tmp_path)
    monkeypatch.setattr(ai_common, "PROJECT_ROOT", tmp_path)
    (tmp_path / "tracked.txt").write_text("task\n", encoding="utf-8")
    git(tmp_path, "commit", "-am", "task")

    assert ai_common.changed_paths({"baseCommit": base, "baselineDirtyPaths": []}) == [
        "tracked.txt"
    ]


def test_unchanged_preexisting_dirty_path_is_excluded(tmp_path, monkeypatch):
    base = init_repo(tmp_path)
    monkeypatch.setattr(ai_common, "PROJECT_ROOT", tmp_path)
    (tmp_path / "tracked.txt").write_text("preexisting\n", encoding="utf-8")
    dirty = ai_common.capture_dirty_baseline()

    assert ai_common.changed_paths({"baseCommit": base, "baselineDirtyPaths": dirty}) == []
    assert ai_common.changed_paths(
        {"baseCommit": base, "baselineDirtyPaths": dirty}, ignore_baseline_dirty=True
    ) == ["tracked.txt"]

    (tmp_path / "tracked.txt").write_text("changed during task\n", encoding="utf-8")
    assert ai_common.changed_paths({"baseCommit": base, "baselineDirtyPaths": dirty}) == [
        "tracked.txt"
    ]


def test_deleting_preexisting_dirty_path_is_visible(tmp_path, monkeypatch):
    base = init_repo(tmp_path)
    monkeypatch.setattr(ai_common, "PROJECT_ROOT", tmp_path)
    dirty_path = tmp_path / "tracked.txt"
    dirty_path.write_text("preexisting\n", encoding="utf-8")
    dirty = ai_common.capture_dirty_baseline()
    dirty_path.unlink()

    assert ai_common.changed_name_status({"baseCommit": base, "baselineDirtyPaths": dirty}) == [
        ("D", "tracked.txt")
    ]


def test_rename_checks_source_and_destination(tmp_path, monkeypatch):
    base = init_repo(tmp_path)
    monkeypatch.setattr(ai_common, "PROJECT_ROOT", tmp_path)
    git(tmp_path, "mv", "tracked.txt", "renamed.txt")

    assert ai_common.changed_paths({"baseCommit": base, "baselineDirtyPaths": []}) == [
        "renamed.txt",
        "tracked.txt",
    ]


def test_ci_base_commit_environment_overrides_contract(tmp_path, monkeypatch):
    base = init_repo(tmp_path)
    monkeypatch.setattr(ai_common, "PROJECT_ROOT", tmp_path)
    (tmp_path / "new.txt").write_text("new\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "new")
    monkeypatch.setenv("AI_BASE_COMMIT", base)

    assert ai_common.changed_paths({"baseCommit": "invalid", "baselineDirtyPaths": []}) == [
        "new.txt"
    ]


def test_mode_only_changes_break_baseline_fingerprint(tmp_path, monkeypatch):
    base = init_repo(tmp_path)
    monkeypatch.setattr(ai_common, "PROJECT_ROOT", tmp_path)
    tracked = tmp_path / "tracked.txt"
    os.chmod(tracked, 0o755)
    dirty = ai_common.capture_dirty_baseline()
    os.chmod(tracked, 0o644)

    assert ai_common.changed_paths({"baseCommit": base, "baselineDirtyPaths": dirty}) == [
        "tracked.txt"
    ]


def test_segment_glob_does_not_cross_directory_boundaries():
    assert ai_common.matches("src/*.py", "src/deep/file.py") is False
    assert ai_common.matches("src/**/*.py", "src/deep/file.py") is True
    assert ai_common.matches("**/src/**", "pkg/src/deep/file.py") is True


def test_matches_reuses_compiled_segment_patterns(monkeypatch):
    ai_common._compiled_segment_pattern.cache_clear()
    original_compile = ai_common.re.compile
    calls = []

    def count_compile(pattern):
        calls.append(pattern)
        return original_compile(pattern)

    monkeypatch.setattr(ai_common.re, "compile", count_compile)

    assert ai_common.matches("docs/**/*.md", "docs/quality/gates.md") is True
    assert ai_common.matches("docs/**/*.md", "docs/quality/gates.md") is True

    assert calls == ["docs", "[^/]*\\.md"]


def test_matches_retains_the_full_ownership_preview_segment_working_set(monkeypatch):
    ai_common._compiled_segment_pattern.cache_clear()
    original_compile = ai_common.re.compile
    calls = []

    def count_compile(pattern):
        calls.append(pattern)
        return original_compile(pattern)

    monkeypatch.setattr(ai_common.re, "compile", count_compile)
    patterns = [f"archive-{index}.json" for index in range(300)]

    for _ in range(2):
        for pattern in patterns:
            assert ai_common.matches(pattern, pattern) is True

    assert len(calls) == len(patterns)
