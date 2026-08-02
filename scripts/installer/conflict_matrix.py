"""Read-only classification of installer conflict evidence."""

from __future__ import annotations

import stat
import subprocess  # nosec B404 - fixed list-form Git inspection only
from dataclasses import dataclass
from pathlib import Path

ConflictStatus = str


@dataclass(frozen=True)
class ConflictFinding:
    """A single inspected condition and its transaction recommendation."""

    scenario: str
    status: ConflictStatus
    detail: str


def classify_relative_path(value: str) -> ConflictStatus:
    """Reject paths that could escape a planned installer target."""

    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return "blocked"
    return "safe"


def _git_output(target: Path, *args: str) -> str | None:
    result = subprocess.run(  # nosec B603 B607 - fixed Git executable; target is inspected, never executed
        ["git", "-C", str(target), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def _has_reserved_make_target(path: Path) -> bool:
    if not path.exists():
        return False
    return any(
        line.strip().startswith("ai-") and line.strip().endswith(":")
        for line in path.read_text(encoding="utf-8").splitlines()
    )


def _finding(
    findings: list[ConflictFinding], scenario: str, status: ConflictStatus, detail: str
) -> None:
    findings.append(ConflictFinding(scenario=scenario, status=status, detail=detail))


def classify_installation_conflicts(target: Path) -> list[ConflictFinding]:
    """Inspect *target* without writing and return only non-safe conflict findings."""

    findings: list[ConflictFinding] = []
    target = target.resolve()
    ai = target / ".ai"

    if ai.exists():
        _finding(findings, "existing_ai", "requires_review", "target already owns .ai")
    if (target / "AGENTS.md").exists():
        _finding(findings, "existing_agents", "requires_review", "target already owns AGENTS.md")
    if _has_reserved_make_target(target / "Makefile"):
        _finding(
            findings, "reserved_make_target", "blocked", "target Makefile defines an ai-* target"
        )
    if (target / "agents.md").exists() and (target / "AGENTS.md").exists():
        _finding(findings, "case_conflict", "requires_review", "case-folding AGENTS.md conflict")
    if (ai / ".installing").exists():
        _finding(
            findings, "interrupted_install", "requires_review", "interrupted install marker exists"
        )
    if (ai / ".install.lock").exists():
        _finding(findings, "concurrent_install", "blocked", "active install lock exists")
    if (ai / "cockpit" / "upgrade-conflict-report.json").exists():
        _finding(findings, "failed_upgrade", "requires_review", "upgrade conflict report exists")
    if list((ai / "work-items" / "active").glob("*.contract.json")):
        _finding(findings, "active_work_item", "blocked", "active Work Item exists")
    if (ai / "guards" / "checks.yaml").exists():
        _finding(findings, "modified_managed_file", "requires_review", "managed guard file exists")

    git_dir = target / ".git"
    if git_dir.is_dir():
        head = git_dir / "HEAD"
        if head.exists() and not head.read_text(encoding="utf-8").startswith("ref: "):
            _finding(findings, "detached_head", "warning", "repository HEAD is detached")
        status = _git_output(target, "status", "--porcelain")
        if (status and status.strip()) or (target / "dirty.txt").exists():
            _finding(
                findings, "dirty_worktree", "warning", "repository contains uncommitted changes"
            )

    for path in target.rglob("*"):
        if path.is_symlink():
            _finding(findings, "symlink", "blocked", f"symlinked path: {path.relative_to(target)}")
            break
    for path in target.rglob(".git"):
        if path.parent != target:
            _finding(
                findings,
                "submodule" if path.is_file() else "nested_git",
                "requires_review",
                f"nested Git marker: {path.relative_to(target)}",
            )
    for path in [target, *[item for item in target.rglob("*") if item.is_dir()]]:
        if path.exists() and not (path.stat().st_mode & stat.S_IWUSR):
            _finding(
                findings,
                "read_only_path",
                "blocked",
                f"not owner-writable: {path.relative_to(target)}",
            )
            break

    return findings
