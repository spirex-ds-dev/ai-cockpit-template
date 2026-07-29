import json
import os
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY = ROOT / ".github" / "workflows" / "compatibility.yml"
SMOKE = ROOT / ".github" / "workflows" / "smoke.yml"
MAKEFILE = ROOT / "Makefile"


def _release_evidence_script() -> str:
    workflow = yaml.safe_load(SMOKE.read_text(encoding="utf-8"))
    job = workflow["jobs"].get("release-evidence")
    assert job is not None, "release-evidence Job is missing"
    step = next(
        item for item in job["steps"] if item.get("name") == "Verify release evidence ownership"
    )
    return (
        step["run"]
        .replace("${{ github.event.pull_request.base.sha || github.event.before }}", "base")
        .replace("${{ github.sha }}", "head")
    )


def _aggregate_evidence_script() -> str:
    workflow = yaml.safe_load(SMOKE.read_text(encoding="utf-8"))
    job = workflow["jobs"].get("ci-evidence")
    assert job is not None, "ci-evidence Job is missing"
    step = next(
        item
        for item in job["steps"]
        if item.get("name") == "Generate and validate aggregate CI evidence"
    )
    return (
        step["run"]
        .replace("${{ github.event.pull_request.head.sha || github.sha }}", "a" * 40)
        .replace("${{ github.sha }}", "b" * 40)
        .replace(
            "${{ github.event_name == 'pull_request' && 'pull_request_merge_ref' || 'direct_commit' }}",
            "pull_request_merge_ref",
        )
    )


def _run_release_evidence(tmp_path: Path, *, release_intent: bool) -> subprocess.CompletedProcess:
    command_dir = tmp_path / "bin"
    command_dir.mkdir()
    make_calls = tmp_path / "make-calls.txt"
    make_command = command_dir / "make"
    make_command.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$MAKE_CALLS"\n',
        encoding="utf-8",
    )
    make_command.chmod(0o755)
    git_command = command_dir / "git"
    git_command.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\n' release.json\n",
        encoding="utf-8",
    )
    git_command.chmod(0o755)
    environment = {
        **os.environ,
        "MAKE_CALLS": str(make_calls),
        "PATH": f"{command_dir}{os.pathsep}{os.environ['PATH']}",
        "RELEASE_PREPARATION_INTENT": "true" if release_intent else "false",
    }
    return subprocess.run(
        ["bash", "-c", _release_evidence_script()],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_aggregate_evidence(
    tmp_path: Path,
    *,
    template: str,
    installation: str,
    release: str,
) -> tuple[subprocess.CompletedProcess, dict]:
    command_dir = tmp_path / "bin"
    command_dir.mkdir()
    make_command = command_dir / "make"
    make_command.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    make_command.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": f"{command_dir}{os.pathsep}{os.environ['PATH']}",
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_RUN_ID": "30272658885",
        "TEMPLATE_RESULT": template,
        "INSTALLATION_RESULT": installation,
        "RELEASE_RESULT": release,
    }
    result = subprocess.run(
        ["bash", "-c", _aggregate_evidence_script()],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    evidence = json.loads((tmp_path / "ci-release-evidence.json").read_text(encoding="utf-8"))
    return result, evidence


def test_python_matrix_uses_lightweight_compatibility_command():
    workflow = COMPATIBILITY.read_text(encoding="utf-8")

    assert "os: [ubuntu-latest, macos-latest]" in workflow
    assert 'python: ["3.11", "3.14"]' in workflow
    assert "Run Python compatibility tests" in workflow
    assert "run: make compatibility-test" in workflow
    assert "run: make quality" not in workflow
    assert "timeout-minutes: 10" in workflow


def test_full_quality_has_one_workflow_owner():
    compatibility = COMPATIBILITY.read_text(encoding="utf-8")
    smoke = SMOKE.read_text(encoding="utf-8")

    assert compatibility.count("make quality") == 0
    assert smoke.count("make quality") == 1
    assert "Run repository quality gates" in smoke
    assert "timeout --foreground 25m make quality" in smoke
    assert "quality heartbeat" in smoke
    assert "Publish quality timing summary" in smoke
    assert "$GITHUB_STEP_SUMMARY" in smoke


def test_release_preflight_precedes_expensive_quality():
    smoke = SMOKE.read_text(encoding="utf-8")
    assert smoke.index("Verify documented public release contract") < smoke.index(
        "Run repository quality gates"
    )


def test_quality_is_phased_before_expensive_test_graph():
    makefile = MAKEFILE.read_text(encoding="utf-8")
    assert "quality-static:" in makefile
    assert "quality-tests:" in makefile
    assert "quality-evidence:" in makefile
    assert makefile.index("quality-static:") < makefile.index("quality-tests:")


def test_release_preparation_is_scoped_to_release_file_changes():
    smoke = SMOKE.read_text(encoding="utf-8")
    assert "Determine release preparation scope" in smoke
    assert 'git diff --name-only "${AI_BASE_COMMIT}...HEAD"' in smoke
    assert "next-release\\.json" in smoke
    assert "AI_RELEASE_PREPARATION=1" in smoke
    assert "AI_RELEASE_PREPARATION=0" in smoke
    assert 'if [[ "$AI_RELEASE_PREPARATION" == "1" ]]' in smoke
    assert "release contract validation is not applicable" in smoke
    assert "release-preparation" in smoke
    assert "RELEASE_PREPARATION_INTENT" in smoke


def test_ordinary_pr_release_evidence_skips_all_release_contract_checks(tmp_path):
    result = _run_release_evidence(tmp_path, release_intent=False)

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "make-calls.txt").exists()
    assert "No explicit release-preparation intent" in result.stdout


def test_explicit_release_intent_runs_release_contract_checks(tmp_path):
    result = _run_release_evidence(tmp_path, release_intent=True)

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "make-calls.txt").read_text(encoding="utf-8").splitlines() == [
        "check-release-state-consistency",
        "check-release-distribution",
    ]


def test_ci_evidence_is_terminal_and_requires_all_three_jobs():
    workflow = yaml.safe_load(SMOKE.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    assert "needs" not in jobs["installation-smoke"]
    assert "needs" not in jobs["release-evidence"]
    assert jobs["ci-evidence"]["needs"] == [
        "template-smoke",
        "installation-smoke",
        "release-evidence",
    ]
    assert jobs["ci-evidence"]["if"] == "always()"


def test_aggregate_generator_records_all_successful_jobs(tmp_path):
    result, evidence = _run_aggregate_evidence(
        tmp_path,
        template="success",
        installation="success",
        release="success",
    )

    assert result.returncode == 0, result.stderr
    assert evidence["state"] == "candidate"
    assert evidence["conclusion"] == "success"
    assert evidence["failureReasons"] == []
    assert evidence["requiredJobNames"] == [
        "template-smoke",
        "installation-smoke",
        "release-evidence",
    ]
    assert evidence["workflowRuns"][0]["jobs"] == [
        {"name": "template-smoke", "conclusion": "success"},
        {"name": "installation-smoke", "conclusion": "success"},
        {"name": "release-evidence", "conclusion": "success"},
    ]


def test_aggregate_generator_preserves_failure_and_skipped_results(tmp_path):
    result, evidence = _run_aggregate_evidence(
        tmp_path,
        template="failure",
        installation="skipped",
        release="skipped",
    )

    assert result.returncode == 1
    assert evidence["state"] == "failed"
    assert evidence["conclusion"] == "failure"
    assert evidence["failureReasons"] == [
        "template-smoke:failure",
        "installation-smoke:skipped",
        "release-evidence:skipped",
    ]
    assert "One or more required CI jobs did not succeed." in result.stderr


def test_compatibility_target_disables_coverage_overhead():
    makefile = MAKEFILE.read_text(encoding="utf-8")
    target = makefile.split("compatibility-test:", 1)[1].split("\n\n", 1)[0]

    assert "pytest -q --no-cov" in target
    assert "tests/test_input_trust.py" in target
    assert "tests/test_input_trust_corpus.py" in target
    assert "tests/test_workflows.py" in target
    assert "tests/test_ci_quality_orchestration.py" in target
