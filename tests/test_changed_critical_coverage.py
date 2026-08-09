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


def test_adoption_bootstrap_exemption_is_contract_bound_and_narrow(tmp_path):
    contract_path = tmp_path / "adoption.contract.json"
    contract_path.write_text(
        json.dumps(
            {
                "workItemId": "adopt_ai_cockpit",
                "adoptionBootstrapPaths": [
                    "scripts/ai_*.py",
                    "scripts/check_changed_critical_coverage.py",
                ],
            }
        ),
        encoding="utf-8",
    )

    assert check_changed_critical_coverage.adoption_bootstrap_paths(
        [
            "scripts/ai_finish.py",
            "scripts/check_changed_critical_coverage.py",
            "scripts/check_critical_coverage.py",
        ],
        contract_path,
    ) == [
        "scripts/ai_finish.py",
        "scripts/check_changed_critical_coverage.py",
    ]

    contract_path.write_text(
        json.dumps(
            {"workItemId": "ordinary-work-item", "adoptionBootstrapPaths": ["scripts/ai_*.py"]}
        ),
        encoding="utf-8",
    )
    assert (
        check_changed_critical_coverage.adoption_bootstrap_paths(
            ["scripts/ai_finish.py"], contract_path
        )
        == []
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
        "candidate_snapshot",
        lambda **_kwargs: {
            "baseCommit": "a" * 40,
            "candidateHead": "b" * 40,
            "candidateFiles": [{"path": "scripts/ai_finish.py"}],
            "candidateTreeDigest": "c" * 64,
            "candidateDiffDigest": "d" * 64,
            "candidateStateDigest": "c" * 64,
        },
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
    binding = json.loads(report_path.read_text(encoding="utf-8"))["binding"]
    assert binding["baseCommit"] == "a" * 40
    assert binding["candidateHead"]
    assert binding["candidateStateDigest"]


def test_candidate_snapshot_binds_content_not_only_the_changed_path(monkeypatch, tmp_path):
    tracked = tmp_path / "scripts" / "ai_finish.py"
    tracked.parent.mkdir()
    tracked.write_text("first\n", encoding="utf-8")
    outputs = {
        ("git", "rev-parse", "HEAD"): "b" * 40 + "\n",
        ("git", "diff", "--name-only", "a" * 40 + "...HEAD"): "",
        ("git", "diff", "--name-only"): "scripts/ai_finish.py\n",
        ("git", "diff", "--cached", "--name-only"): "",
        ("git", "ls-files", "--others", "--exclude-standard"): "",
        ("git", "diff", "--binary", "a" * 40 + "...HEAD"): "",
        ("git", "diff", "--binary", "--cached"): "",
        ("git", "diff", "--binary"): "diff --git a/scripts/ai_finish.py b/scripts/ai_finish.py\n",
    }

    def run(command, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(check_changed_critical_coverage.subprocess, "run", run)
    first = check_changed_critical_coverage.candidate_snapshot(base="a" * 40, project_root=tmp_path)
    tracked.write_text("second\n", encoding="utf-8")
    second = check_changed_critical_coverage.candidate_snapshot(
        base="a" * 40, project_root=tmp_path
    )

    assert [item["path"] for item in first["candidateFiles"]] == [
        item["path"] for item in second["candidateFiles"]
    ]
    assert first["candidateTreeDigest"] != second["candidateTreeDigest"]


def test_candidate_snapshot_rejects_contract_unowned_dirty_path(monkeypatch, tmp_path):
    (tmp_path / "foreign.txt").write_text("foreign\n", encoding="utf-8")
    contract = tmp_path / "task.contract.json"
    contract.write_text(
        json.dumps({"scope": ["scripts/**"], "baselineDirtyPaths": []}), encoding="utf-8"
    )
    outputs = {
        ("git", "rev-parse", "HEAD"): "b" * 40 + "\n",
        ("git", "diff", "--name-only", "a" * 40 + "...HEAD"): "",
        ("git", "diff", "--name-only"): "foreign.txt\n",
        ("git", "diff", "--cached", "--name-only"): "",
        ("git", "ls-files", "--others", "--exclude-standard"): "",
    }

    def run(command, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(check_changed_critical_coverage.subprocess, "run", run)
    with pytest.raises(ValueError, match="Contract-unowned path"):
        check_changed_critical_coverage.candidate_snapshot(
            base="a" * 40, project_root=tmp_path, contract_path=contract
        )


def test_candidate_snapshot_allows_known_lifecycle_surfaces(monkeypatch, tmp_path):
    paths = [
        "fixture.txt",
        ".ai/work-items/active/task.contract.json",
        ".ai/work-items/active/task.outcome.json",
        ".ai/cockpit/task_report.json",
        ".ai/work-items/starts/task.json",
    ]
    for path in paths:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(path, encoding="utf-8")
    contract = tmp_path / ".ai/work-items/active/task.contract.json"
    contract.write_text(
        json.dumps({"workItemId": "task", "scope": ["fixture.txt"], "baselineDirtyPaths": []}),
        encoding="utf-8",
    )
    outputs = {
        ("git", "rev-parse", "HEAD"): "b" * 40 + "\n",
        ("git", "diff", "--name-only", "a" * 40 + "...HEAD"): "",
        ("git", "diff", "--name-only"): "\n".join(paths) + "\n",
        ("git", "diff", "--cached", "--name-only"): "",
        ("git", "ls-files", "--others", "--exclude-standard"): "",
        ("git", "diff", "--binary", "a" * 40 + "...HEAD"): "",
        ("git", "diff", "--binary", "--cached"): "",
        ("git", "diff", "--binary"): "",
    }

    def run(command, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(check_changed_critical_coverage.subprocess, "run", run)
    snapshot = check_changed_critical_coverage.candidate_snapshot(
        base="a" * 40, project_root=tmp_path, contract_path=contract
    )

    assert [item["path"] for item in snapshot["candidateFiles"]] == [
        ".ai/work-items/active/task.contract.json",
        ".ai/work-items/starts/task.json",
        "fixture.txt",
    ]
    assert snapshot["excludedDerivedPaths"] == [
        ".ai/cockpit/task_report.json",
        ".ai/work-items/active/task.outcome.json",
    ]


def test_candidate_snapshot_ignores_derived_outcome_changes_in_diff_binding(monkeypatch, tmp_path):
    """Outcome persistence must not invalidate the candidate it records."""
    fixture = tmp_path / "fixture.txt"
    fixture.write_text("candidate\n", encoding="utf-8")
    contract = tmp_path / ".ai/work-items/active/task.contract.json"
    contract.parent.mkdir(parents=True)
    contract.write_text(
        json.dumps({"workItemId": "task", "scope": ["fixture.txt"], "baselineDirtyPaths": []}),
        encoding="utf-8",
    )
    outcome = tmp_path / ".ai/work-items/active/task.outcome.json"
    outcome.write_text("first outcome\n", encoding="utf-8")
    paths = [
        "fixture.txt",
        ".ai/work-items/active/task.contract.json",
        ".ai/work-items/active/task.outcome.json",
    ]

    def run(command, **_kwargs):
        command = tuple(command)
        if command == ("git", "rev-parse", "HEAD"):
            output = "b" * 40 + "\n"
        elif command in {
            ("git", "diff", "--name-only", "a" * 40 + "...HEAD"),
            ("git", "diff", "--name-only"),
        }:
            output = "\n".join(paths) + "\n"
        elif command == ("git", "diff", "--cached", "--name-only") or command == (
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
        ):
            output = ""
        elif command == ("git", "diff", "--binary"):
            output = f"derived outcome: {outcome.read_text(encoding='utf-8')}"
        else:
            output = ""
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(check_changed_critical_coverage.subprocess, "run", run)
    first = check_changed_critical_coverage.candidate_snapshot(
        base="a" * 40, project_root=tmp_path, contract_path=contract
    )
    outcome.write_text("second outcome\n", encoding="utf-8")
    second = check_changed_critical_coverage.candidate_snapshot(
        base="a" * 40, project_root=tmp_path, contract_path=contract
    )

    assert first["candidateDiffDigest"] == second["candidateDiffDigest"]
    assert first["candidateTreeDigest"] == second["candidateTreeDigest"]
    assert first["excludedDerivedPaths"] == [".ai/work-items/active/task.outcome.json"]


def test_not_applicable_coverage_writes_a_bound_receipt(monkeypatch, tmp_path):
    policy_path = tmp_path / "policy.json"
    report_path = tmp_path / "target" / "coverage.json"
    policy_path.write_text(json.dumps({"version": 1, "criticalFiles": {}}), encoding="utf-8")
    binding = {
        "baseCommit": "a" * 40,
        "candidateHead": "b" * 40,
        "candidateFiles": [{"path": "fixture.txt", "state": "present", "sha256": "c" * 64}],
        "candidateTreeDigest": "d" * 64,
        "candidateDiffDigest": "e" * 64,
        "candidateStateDigest": "d" * 64,
    }
    monkeypatch.setattr(
        check_changed_critical_coverage, "candidate_snapshot", lambda **_kwargs: binding
    )

    assert (
        check_changed_critical_coverage.run_predictor(
            base="a" * 40,
            policy_path=policy_path,
            report_path=report_path,
            project_root=tmp_path,
            run_command=lambda _command: pytest.fail("no test command should run"),
            critical_minimums={},
        )
        == 0
    )
    receipt = json.loads(report_path.read_text(encoding="utf-8"))
    assert receipt["applicability"]["reason"] == "no_critical_script_changed"
    assert receipt["binding"] == binding
