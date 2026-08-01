import json
import subprocess
import sys
from pathlib import Path

import pytest
import real_adopter_reference_validation as validation


def test_evidence_pack_rejects_a_template_or_fixture_reference():
    """Break caught: a controlled fixture could be misrepresented as a real adopter."""
    project = validation.ReferenceProject(
        identifier="fixture",
        category="service",
        remote_url="https://github.com/spirex-ds-dev/ai-cockpit-template.git",
        stack="python",
        required_markers=("pyproject.toml",),
        native_tool_command=None,
    )

    with pytest.raises(validation.ReferenceValidationError, match="template or fixture"):
        validation.validate_reference_project(project)


def test_evidence_pack_requires_every_lifecycle_phase_and_not_run_recovery():
    """Break caught: missing lifecycle evidence or a bare not_run result becomes a pass."""
    phases = {
        phase: validation.phase_result("not_run", "native tooling unavailable", "install Xcode")
        for phase in validation.REQUIRED_PHASES
    }
    phases["install"] = validation.phase_result("executed", "installer completed")
    pack = validation.build_evidence_pack(
        validation.REFERENCE_PROJECTS[1],
        revision="a" * 40,
        baseline_paths=("Package.swift", "README.md"),
        changed_paths=(".ai/project/capabilities.json", "AGENTS.md"),
        phases=phases,
    )

    validation.validate_evidence_pack(pack)
    assert pack["providerEvidence"] == "not_verified"
    assert pack["diff"]["preservedProductPaths"] is True
    assert pack["phases"]["calibration"]["recoveryCondition"] == "install Xcode"


def test_evidence_pack_rejects_product_source_changes():
    """Break caught: installation changes an adopter product path without an explainable owner."""
    phases = {
        phase: validation.phase_result("executed", "completed")
        for phase in validation.REQUIRED_PHASES
    }
    pack = validation.build_evidence_pack(
        validation.REFERENCE_PROJECTS[0],
        revision="b" * 40,
        baseline_paths=("src/service.py", "README.md"),
        changed_paths=("src/service.py", ".ai/project/capabilities.json"),
        phases=phases,
    )

    with pytest.raises(validation.ReferenceValidationError, match="product paths"):
        validation.validate_evidence_pack(pack)


def test_evidence_pack_recognizes_installer_owned_runtime_and_managed_regions():
    """Break caught: a real install is rejected because its own runtime files look like product edits."""
    phases = {
        phase: validation.phase_result("executed", "completed")
        for phase in validation.REQUIRED_PHASES
    }
    pack = validation.build_evidence_pack(
        validation.REFERENCE_PROJECTS[0],
        revision="c" * 40,
        baseline_paths=("pyproject.toml",),
        changed_paths=(
            ".gitignore",
            "scripts/ai_start.py",
            "scripts/__pycache__/ai_input_trust.cpython-314.pyc",
            ".cursor/rules/ai-cockpit.mdc",
        ),
        phases=phases,
    )

    validation.validate_evidence_pack(pack)
    assert pack["diff"]["productPaths"] == []


def test_cli_writes_one_independent_pack_per_catalog_project(tmp_path: Path):
    """Break caught: a runner emits one aggregate report instead of three independent packs."""
    output = tmp_path / "packs"
    payload = validation.write_simulated_evidence_packs(output)

    assert [item["projectId"] for item in payload] == ["httpx", "alamofire", "turborepo"]
    paths = sorted(output.glob("*.json"))
    assert len(paths) == 3
    assert all(
        json.loads(path.read_text(encoding="utf-8"))["providerEvidence"] == "not_verified"
        for path in paths
    )


def test_command_receipt_preserves_a_fail_closed_external_command_result():
    """Break caught: an unsuccessful reference command is recorded as executed success."""
    receipt = validation.command_phase_result(
        [sys.executable, "-c", "raise SystemExit(7)"], Path.cwd()
    )

    assert receipt["status"] == "blocked"
    assert "exit 7" in receipt["detail"]
    assert "recoveryCondition" in receipt


def test_command_receipt_records_timeout_as_blocked_with_a_resume_path():
    """Break caught: an over-budget reference probe hangs the entire evidence run."""
    receipt = validation.command_phase_result(
        [sys.executable, "-c", "import time; time.sleep(2)"], Path.cwd(), timeout_seconds=0.01
    )

    assert receipt["status"] == "blocked"
    assert "timed out" in receipt["detail"]
    assert "Increase" in receipt["recoveryCondition"]


def test_command_receipt_does_not_disclose_a_local_worktree_path(tmp_path: Path):
    """Break caught: archived reference evidence leaks a machine-specific clone location."""
    receipt = validation.command_phase_result(
        [sys.executable, "-c", "pass", str(tmp_path)], tmp_path
    )

    assert str(tmp_path) not in json.dumps(receipt)


def test_calibration_sequence_runs_read_only_doctor_before_profile_generation(tmp_path: Path):
    """Break caught: calibration fails because the required Doctor report was never generated."""
    commands = validation.calibration_commands(Path("/template"), tmp_path)

    assert commands[0][1].endswith("scripts/ai_project_doctor.py")
    assert commands[0][-2:] == (
        "--output",
        str(tmp_path.resolve() / "target/ai_project_doctor_report.json"),
    )
    assert commands[1][1].endswith("scripts/ai_calibrate.py")
    assert "--report" in commands[1]


def test_changed_path_collection_includes_untracked_installer_runtime(tmp_path: Path):
    """Break caught: untracked installer files disappear from the before/after diff evidence."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "product.txt").write_text("changed", encoding="utf-8")

    assert validation.changed_paths(tmp_path) == (".ai/manifest.json", "product.txt")


def test_disposable_remote_replaces_the_public_origin_without_touching_it(tmp_path: Path):
    """Break caught: a reference lifecycle could push its temporary branch to the source project."""
    repo = tmp_path / "reference"
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/example/reference.git"],
        cwd=repo,
        check=True,
    )

    remote = validation.configure_disposable_remote(repo)

    assert remote.is_dir()
    assert subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=repo, text=True, capture_output=True, check=True
    ).stdout.strip() == str(remote)
    assert subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "main"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    assert (
        subprocess.run(
            ["git", "config", "--get", "receive.shallowUpdate"],
            cwd=remote,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        == "true"
    )


def test_adoption_install_command_binds_to_the_disposable_origin(tmp_path: Path):
    """Break caught: first-adoption setup omits the local remote and can use a source remote."""
    command = validation.adoption_install_command(
        Path("/template/scripts/install_ai_cockpit.py"), tmp_path, "python", "main"
    )

    assert "--create-adoption" in command
    assert command[command.index("--base-remote") + 1] == "origin"
    assert command[command.index("--base-branch") + 1] == "main"


def test_first_work_item_phase_requires_both_contract_and_start_receipt(tmp_path: Path):
    """Break caught: a partial adoption is reported as a usable first Work Item."""
    active = tmp_path / ".ai/work-items/active"
    starts = tmp_path / ".ai/work-items/starts"
    active.mkdir(parents=True)
    starts.mkdir(parents=True)
    (active / "adopt_ai_cockpit.contract.json").write_text("{}", encoding="utf-8")

    assert validation.first_work_item_phase(tmp_path)["status"] == "blocked"

    (starts / "adopt_ai_cockpit.json").write_text("{}", encoding="utf-8")
    assert validation.first_work_item_phase(tmp_path)["status"] == "executed"


def test_scope_violation_phase_removes_the_probe_after_the_guard_runs(tmp_path: Path):
    """Break caught: a scope-violation probe leaves an undeclared product change behind."""
    script = tmp_path / "scripts" / "ai_check_scope.py"
    script.parent.mkdir()
    script.write_text("raise SystemExit(1)\n", encoding="utf-8")
    contract = tmp_path / ".ai/work-items/active/adopt_ai_cockpit.contract.json"
    contract.parent.mkdir(parents=True)
    contract.write_text("{}", encoding="utf-8")

    result = validation.scope_violation_phase(tmp_path)

    assert result["status"] == "executed"
    assert not (tmp_path / "reference-outside-contract.txt").exists()


def test_injection_phase_requires_the_installed_policy_to_reject_external_instructions(
    tmp_path: Path,
):
    """Break caught: an installed clone treats external instruction text as authorization."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "ai_input_trust.py").write_text(
        "class SourceType: WEB = 'web'\n"
        "class GovernanceRequest:\n"
        "    def __init__(self, **kwargs): pass\n"
        "def evaluate_governance_request(request):\n"
        "    return type('Decision', (), {'decision': 'block'})()\n",
        encoding="utf-8",
    )

    assert validation.injection_phase(tmp_path)["status"] == "executed"
