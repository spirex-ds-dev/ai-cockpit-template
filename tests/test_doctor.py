import subprocess
import sys
from pathlib import Path

import ai_common
import ai_doctor
import ai_start

ROOT = Path(__file__).resolve().parents[1]


def test_doctor_git_environment_helper_excludes_git_overrides():
    assert all(not key.startswith("GIT_") for key in ai_common.clean_git_environment())


def test_doctor_reports_isolated_unrelated_malformed_linked_worktree(tmp_path, monkeypatch):
    foreign = tmp_path / "foreign"
    identity = ai_start.LinkedWorktreeIdentity(foreign, "main", "other-task")
    monkeypatch.setattr(
        ai_doctor, "linked_worktree_identity_report", lambda **_kwargs: ([identity], [])
    )

    _passed, warnings, _failures = ai_doctor.diagnose(tmp_path)

    assert any(
        "isolated for unrelated starts" in warning and "other-task" in warning
        for warning in warnings
    )


def test_doctor_projects_blocked_outcome_traffic_light_gate_and_recovery(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    (active / "task.outcome.json").write_text(
        '{"status":"blocked","humanStatusColor":"red","failedGate":"quality","recoveryCondition":"retry quality"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_doctor, "linked_worktree_identity_report", lambda **_kwargs: ([], []))
    _, warnings, _ = ai_doctor.diagnose(tmp_path)
    assert any(
        "color=red" in item and "gate=quality" in item and "retry quality" in item
        for item in warnings
    )


def test_doctor_aggregates_conflicting_installation_facts_with_recovery(tmp_path, monkeypatch):
    monkeypatch.setattr(
        ai_doctor,
        "installation_diagnosis",
        lambda _root: {
            "requestedVersion": "0.5.48",
            "installedVersion": "0.5.42",
            "sourceCommit": "a" * 40,
            "releaseTag": "v0.5.42",
            "assetDigests": {"template.tar.gz": "b" * 64},
            "conflicts": ["requested version does not match installed version"],
        },
    )
    monkeypatch.setattr(ai_doctor, "linked_worktree_identity_report", lambda **_kwargs: ([], []))

    passed, _warnings, failures = ai_doctor.diagnose(tmp_path)

    assert any("requestedVersion=0.5.48" in item for item in passed)
    assert any("installedVersion=0.5.42" in item for item in passed)
    assert any("assetDigest template.tar.gz=" + "b" * 64 in item for item in passed)
    assert any("installation contradiction" in item and "Recovery:" in item for item in failures)


def test_doctor_aggregates_targets_blocked_outcome_and_missing_hosted_snapshot(tmp_path):
    (tmp_path / "Makefile").write_text(
        "ai-doctor:\n\t@true\nai-prepare-hosted-verification-snapshot:\n\t@true\n",
        encoding="utf-8",
    )
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    (active / "task.outcome.json").write_text(
        '{"workItemId":"task","status":"blocked","humanStatusColor":"red",'
        '"failedGate":"quality","recoveryCondition":"retry quality"}',
        encoding="utf-8",
    )

    facts = ai_doctor.runtime_diagnosis(tmp_path)

    assert facts["availableTargets"] == ["ai-doctor", "ai-prepare-hosted-verification-snapshot"]
    assert facts["outcomes"][0]["humanStatusColor"] == "red"
    assert facts["hostedSnapshot"]["state"] == "not_ready"
    assert "ai-prepare-hosted-verification-snapshot" in facts["hostedSnapshot"]["recovery"]


def test_doctor_rejects_a_successor_receipt_with_a_foreign_outcome_digest(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    outcome = active / "task.outcome.json"
    outcome.write_text(
        '{"workItemId":"task","status":"blocked","humanStatusColor":"red"}',
        encoding="utf-8",
    )
    (active / "task.successor-receipt.json").write_text(
        '{"schemaVersion":1,"transition":"quarantined","predecessor":{"workItemId":"task"},'
        '"predecessorOutcomeDigest":"' + "0" * 64 + '",'
        '"successor":{"workItemId":"fix","branch":"codex/fix","baseCommit":"' + "a" * 40 + '"},'
        '"successorWorkItemId":"fix","issue":"https://github.com/spirex-ds-dev/ai-cockpit-template/issues/682",'
        '"authority":"RayIori","reason":"repair"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_doctor, "linked_worktree_identity_report", lambda **_kwargs: ([], []))

    _, _, failures = ai_doctor.diagnose(tmp_path)

    assert any("outcome_digest_mismatch" in item for item in failures)


def test_doctor_passes_hard_prerequisites_for_repository():
    passed, warnings, failures = ai_doctor.diagnose(ROOT)
    assert not failures
    assert passed
    assert any("Coverage Guard" in warning for warning in warnings)
    assert any("role=template maintenance" in item for item in passed)


def test_doctor_requires_python_311_or_newer(monkeypatch, tmp_path):
    class VersionInfo(tuple):
        major = 3
        minor = 10

    monkeypatch.setattr(
        ai_doctor.sys,
        "version_info",
        VersionInfo((3, 10, 14, "final", 0)),
    )

    passed, _, failures = ai_doctor.diagnose(tmp_path)

    assert "Python 3.11 or newer is required" in failures
    assert not any("satisfies 3.11+" in item for item in passed)


def test_doctor_fails_without_git_repository_or_initial_commit(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ai_doctor.py"), "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "[FAIL] Run inside a Git repository" in result.stdout
    assert "[FAIL] Create an initial Git commit" in result.stdout


def test_doctor_warns_for_unconfigured_project_quality(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / "Makefile.ai.stack").write_text(
        "PROJECT_TEST = printf 'ERROR: configure PROJECT_TEST' >&2; false\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)

    _, warnings, failures = ai_doctor.diagnose(tmp_path)
    assert not failures
    assert any("placeholders" in warning for warning in warnings)


def test_doctor_reports_adoption_ready_when_configuration_complete(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / "Makefile.ai.stack").write_text("PROJECT_TEST = true\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".ai" / "guards").mkdir(parents=True)
    (tmp_path / ".ai" / "guards" / "coverage_policy.yaml").write_text(
        "adoptionReviewed: true\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)
    monkeypatch.setattr(ai_doctor, "readiness_failures", lambda _root: [])

    passed, warnings, failures = ai_doctor.diagnose(tmp_path)
    assert not failures
    assert any("Adoption readiness configuration is complete" in item for item in passed)
    assert any("Coverage Guard" in warning for warning in warnings)


def test_doctor_warns_when_worktree_is_dirty(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)
    (tmp_path / "dirty.txt").write_text("pending\n", encoding="utf-8")

    _, warnings, failures = ai_doctor.diagnose(tmp_path)
    assert not failures
    assert any("worktree is dirty" in warning for warning in warnings)


def test_doctor_warns_when_stack_file_is_missing(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)

    _, warnings, failures = ai_doctor.diagnose(tmp_path)
    assert not failures
    assert any("Makefile.ai.stack is missing" in warning for warning in warnings)


def test_doctor_command_ok_handles_os_error(monkeypatch):
    def raise_os_error(*_args, **_kwargs):
        raise OSError("missing")

    monkeypatch.setattr(ai_doctor.subprocess, "run", raise_os_error)
    assert ai_doctor.command_ok(Path("."), "git", "status") is False


def test_doctor_diagnose_handles_git_status_os_error(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)

    original_run = ai_doctor.subprocess.run

    def selective_run(command, **kwargs):
        if command[:2] == ["git", "status"]:
            raise OSError("git unavailable")
        return original_run(command, **kwargs)

    monkeypatch.setattr(ai_doctor.subprocess, "run", selective_run)
    passed, _, failures = ai_doctor.diagnose(tmp_path)
    assert not failures
    assert any("Git worktree is clean" in item for item in passed)


def test_doctor_detects_nul_delimited_dirty_status_records(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)

    original_run = ai_doctor.subprocess.run

    def selective_run(command, **kwargs):
        if command[:3] == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(
                command, 0, stdout=" M plain.txt\0 M dir/line1\nline2.txt\0", stderr=""
            )
        return original_run(command, **kwargs)

    monkeypatch.setattr(ai_doctor.subprocess, "run", selective_run)
    _, warnings, failures = ai_doctor.diagnose(tmp_path)
    assert not failures
    assert any("worktree is dirty" in warning for warning in warnings)
    assert all("line2.txt" not in warning or "dirty" in warning for warning in warnings)


def test_doctor_main_prints_warnings_without_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        ai_doctor,
        "diagnose",
        lambda _root: (["ok"], ["needs review"], []),
    )
    monkeypatch.setattr(sys, "argv", ["ai_doctor.py", "--root", str(tmp_path)])
    assert ai_doctor.main() == 0
    output = capsys.readouterr().out
    assert "[WARN] needs review" in output
    assert "[PASS] ok" in output


def test_doctor_main_returns_nonzero_on_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        ai_doctor, "diagnose", lambda _root: ([], [], ["Run inside a Git repository"])
    )
    monkeypatch.setattr(sys, "argv", ["ai_doctor.py", "--root", str(tmp_path)])
    assert ai_doctor.main() == 1
    assert "[FAIL]" in capsys.readouterr().out
