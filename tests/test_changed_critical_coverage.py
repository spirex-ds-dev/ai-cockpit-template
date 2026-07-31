import json
from pathlib import Path
from types import SimpleNamespace

import check_changed_critical_coverage
import pytest


def policy_for(path: str, *, minimum: float = 85.0, tests: list[str] | None = None) -> dict:
    return {
        "version": 1,
        "criticalFiles": {
            path: {
                "minimum": minimum,
                "tests": tests or ["tests/test_subject.py"],
            }
        },
    }


def test_changed_critical_selection_uses_declared_tests_and_existing_floor():
    selected, tests = check_changed_critical_coverage.select_changed_critical(
        ["README.md", "scripts/ai_finish.py"],
        policy_for(
            "scripts/ai_finish.py",
            tests=["tests/test_finish_readiness.py", "tests/test_core_gates.py"],
        ),
        {"scripts/ai_finish.py": 85.0},
    )

    assert selected == ["scripts/ai_finish.py"]
    assert tests == ["tests/test_finish_readiness.py", "tests/test_core_gates.py"]


def test_changed_critical_selection_fails_closed_without_test_mapping():
    with pytest.raises(TypeError, match="missing changed-critical test mapping"):
        check_changed_critical_coverage.select_changed_critical(
            ["scripts/ai_finish.py"],
            {"version": 1, "criticalFiles": {}},
            {"scripts/ai_finish.py": 85.0},
        )


def test_changed_critical_selection_rejects_floor_drift():
    with pytest.raises(ValueError, match="does not match authoritative floor"):
        check_changed_critical_coverage.select_changed_critical(
            ["scripts/ai_finish.py"],
            policy_for("scripts/ai_finish.py", minimum=84.0),
            {"scripts/ai_finish.py": 85.0},
        )


def test_focused_coverage_reports_only_selected_critical_failures():
    report = {
        "files": {
            "scripts/ai_finish.py": {
                "summary": {"percent_covered": 84.26},
            }
        }
    }

    failures = check_changed_critical_coverage.focused_coverage_failures(
        report,
        ["scripts/ai_finish.py"],
        {"scripts/ai_finish.py": 85.0},
    )

    assert failures == ["scripts/ai_finish.py: 84.26% is below 85%"]


def test_git_changed_files_includes_committed_worktree_and_untracked(monkeypatch):
    outputs = {
        ("git", "diff", "--name-only", "a" * 40 + "...HEAD"): "README.md\n",
        ("git", "diff", "--name-only"): "scripts/ai_finish.py\n",
        ("git", "diff", "--cached", "--name-only"): "tests/staged_test.py\n",
        ("git", "ls-files", "--others", "--exclude-standard"): "tests/new_test.py\n",
    }

    def run(command, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(check_changed_critical_coverage.subprocess, "run", run)

    assert check_changed_critical_coverage.git_changed_files("a" * 40) == [
        "README.md",
        "scripts/ai_finish.py",
        "tests/staged_test.py",
        "tests/new_test.py",
    ]


def test_predictor_runs_declared_tests_and_checks_generated_report(tmp_path, monkeypatch):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            policy_for(
                "scripts/ai_finish.py",
                tests=["tests/test_finish_readiness.py", "tests/test_core_gates.py"],
            )
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "coverage.json"
    commands = []

    monkeypatch.setattr(
        check_changed_critical_coverage,
        "git_changed_files",
        lambda _base: ["scripts/ai_finish.py"],
    )

    def run(command: list[str]) -> int:
        commands.append(command)
        report_path.write_text(
            json.dumps(
                {
                    "files": {
                        "scripts/ai_finish.py": {
                            "summary": {"percent_covered": 85.5},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        return 0

    result = check_changed_critical_coverage.run_predictor(
        base="a" * 40,
        policy_path=policy_path,
        report_path=report_path,
        project_root=Path("."),
        run_command=run,
        critical_minimums={"scripts/ai_finish.py": 85.0},
    )

    assert result == 0
    assert commands
    assert commands[0][-2:] == [
        "tests/test_finish_readiness.py",
        "tests/test_core_gates.py",
    ]
    assert f"--cov-report=json:{report_path}" in commands[0]
