import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_check_ai_pr_uses_aggregate_validator():
    result = subprocess.run(
        ["make", "-n", "check-ai-pr", "AI_BASE_COMMIT=abc123"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert 'check-ai-pr-core AI_BASE_COMMIT="abc123"' in result.stdout
    assert 'scripts/ai_check_pr.py --base "$(AI_BASE_COMMIT)"' in (ROOT / "Makefile").read_text(
        encoding="utf-8"
    )


def test_project_test_parallel_entrypoints_use_the_fail_closed_manifest_runner():
    shard = subprocess.run(
        ["make", "-n", "project-test-shard", "SHARD=core"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    aggregate = subprocess.run(
        ["make", "-n", "project-test-aggregate"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert shard.returncode == 0, shard.stdout + shard.stderr
    assert "quality_test_manifest.py run-shard" in shard.stdout
    assert '--shard "core"' in shard.stdout
    assert "quality_test_manifest.py --root" not in shard.stdout
    assert aggregate.returncode == 0, aggregate.stdout + aggregate.stderr
    assert "quality_test_manifest.py aggregate" in aggregate.stdout


def test_check_ai_pr_runs_fast_predictors_before_aggregate_validation():
    result = subprocess.run(
        ["make", "-n", "check-ai-pr", "AI_BASE_COMMIT=abc123"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    ordered_markers = (
        "project-format-check",
        "project-lint",
        "check-changed-critical-coverage",
        "check-ai-pr-core",
    )
    positions = [result.stdout.index(marker) for marker in ordered_markers]
    assert positions == sorted(positions)


def test_source_and_installed_makefiles_expose_the_same_post_archive_recovery_target():
    source = (ROOT / "Makefile").read_text(encoding="utf-8")
    installed = (ROOT / "templates/make/Makefile.ai").read_text(encoding="utf-8")

    for text in (source, installed):
        assert "ai-open-post-archive-recovery:" in text
        assert "scripts/ai_post_archive_recovery.py" in text
        assert "HOSTED_REPOSITORY" in text
        assert "HOSTED_RUN_ID" in text
        assert "HOSTED_JOB_ID" in text


def test_pr_audit_restores_tracked_aggregate_evidence_before_audit():
    source = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert 'aggregate_receipt="target/quality/project-test-aggregate/receipt.json"' in source
    assert 'git ls-files --error-unmatch "$$aggregate_receipt"' in source
    assert 'git restore --source=HEAD --worktree -- "$$aggregate_receipt"' in source
    assert source.index("aggregate_receipt=") < source.index("scripts/ai_check_pr.py")


def test_quality_full_restores_tracked_aggregate_evidence_before_exit():
    source = (ROOT / "Makefile").read_text(encoding="utf-8")
    quality_full = source.split("quality-full-owned:", 1)[1].split(
        "# Backward-compatible aliases", 1
    )[0]

    assert "trap" in quality_full
    assert 'aggregate_receipt="target/quality/project-test-aggregate/receipt.json"' in quality_full
    assert 'git ls-files --error-unmatch "$$aggregate_receipt"' in quality_full
    assert 'git restore --source=HEAD --worktree -- "$$aggregate_receipt"' in quality_full
    assert quality_full.index("trap") < quality_full.index("run_quality_session.py")


def test_project_test_shards_skip_empty_git_diff_before_applying_changes():
    text = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "scripts/quality_shard_workspace.py run" in text


def test_source_and_installed_makefiles_expose_the_same_conflict_successor_target():
    source = (ROOT / "Makefile").read_text(encoding="utf-8")
    installed = (ROOT / "templates/make/Makefile.ai").read_text(encoding="utf-8")

    for text in (source, installed):
        assert "ai-transition-conflict-successor:" in text
        assert "--transition-conflict-successor" in text


def test_normal_pr_does_not_run_release_only_source_bound_reassessment():
    result = subprocess.run(
        ["make", "-n", "check-ai-pr", "AI_BASE_COMMIT=abc123"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "check-source-bound-evidence" not in result.stdout


def test_makefile_exposes_source_bound_evidence_gate():
    result = subprocess.run(
        ["make", "-n", "check-source-bound-evidence"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "scripts/ai_capability_truth.py" in result.stdout
    assert "scripts/ai_japanese_capability.py --check --require-final-reassessment" in result.stdout
    assert "scripts/check_pre_release_documentation_alignment.py" in result.stdout


def test_docs_metadata_composes_capability_claim_binding_without_a_new_gate():
    result = subprocess.run(
        ["make", "-n", "check-docs-metadata"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "scripts/check_docs_metadata.py" in result.stdout
    assert "scripts/ai_check_capability_claims.py" in result.stdout
    checks = (ROOT / ".ai/cockpit/checks.yaml").read_text(encoding="utf-8")
    assert "check-capability-claims" not in checks


def test_project_lint_checks_locked_ruff_version_before_rule_evaluation():
    result = subprocess.run(
        ["make", "-n", "project-lint"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    version_check = result.stdout.index("scripts/check_dev_tool_versions.py")
    ruff_check = result.stdout.index("-m ruff check scripts tests")
    assert version_check < ruff_check


def test_project_format_check_checks_locked_ruff_version_before_format_evaluation():
    result = subprocess.run(
        ["make", "-n", "project-format-check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    version_check = result.stdout.index("scripts/check_dev_tool_versions.py")
    ruff_format = result.stdout.index("-m ruff format --check scripts tests")
    assert version_check < ruff_format


def test_project_format_check_runs_ruff_format_check():
    result = subprocess.run(
        ["make", "-n", "project-format-check"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "ruff format --check scripts tests" in result.stdout
    assert "git diff --check" in result.stdout


def test_makefile_exposes_real_absurd_injection_document_alignment_check():
    result = subprocess.run(
        ["make", "-n", "check-real-absurd-injection-docs"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "scripts/check_real_absurd_injection_docs.py" in result.stdout


def test_supply_chain_checks_are_exposed_as_make_targets():
    result = subprocess.run(
        [
            "make",
            "-n",
            "check-sbom",
            "check-provenance",
            "check-secret-scanning",
            "check-dependency-vulnerabilities",
            "check-bandit-baseline",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "scripts/check_bandit_baseline.py" in result.stdout
    assert "scripts/check_supply_chain.py sbom" in result.stdout
    assert "scripts/check_supply_chain.py provenance" in result.stdout
    assert "scripts/check_supply_chain.py secrets" in result.stdout
    assert "scripts/check_supply_chain.py vulnerabilities" in result.stdout


def test_makefile_exposes_ordered_pre_edit_preparation_entrypoint():
    result = subprocess.run(
        [
            "make",
            "-n",
            "ai-prepare-implementation",
            "CONTRACT=.ai/work-items/active/example.contract.json",
            "SUMMARY=.ai/work-items/active/example.summary.json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    preflight = result.stdout.index("ai-preflight")
    checkpoint = result.stdout.index("ai-checkpoint")
    assert preflight < checkpoint
    assert 'STAGE="before_edit"' in result.stdout


def test_target_root_synchronization_does_not_forward_caller_default_summary():
    result = subprocess.run(
        [
            "make",
            "-n",
            "ai-synchronize-work-item",
            "TARGET_ROOT=/tmp/pre-capability-work-item",
            "CONTRACT=.ai/work-items/active/target.contract.json",
            "BASE_REMOTE=origin",
            "BASE_BRANCH=main",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert '--project-root "/tmp/pre-capability-work-item"' in result.stdout
    assert "--summary" not in result.stdout


def test_synchronization_make_target_forwards_target_root_to_runtime():
    result = subprocess.run(
        [
            "make",
            "-n",
            "ai-synchronize-work-item",
            "CONTRACT=.ai/work-items/active/example.contract.json",
            "SUMMARY=.ai/work-items/active/example.summary.json",
            "BASE_REMOTE=origin",
            "BASE_BRANCH=main",
            "TARGET_ROOT=/governed-target",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert '--project-root "/governed-target"' in result.stdout


def test_makefile_forwards_amendment_revalidation_binding_to_checkpoint_writer():
    result = subprocess.run(
        [
            "make",
            "-n",
            "ai-checkpoint",
            "CONTRACT=.ai/work-items/active/example.contract.json",
            "SUMMARY=.ai/work-items/active/example.summary.json",
            "STAGE=contract_amendment_revalidation",
            "PREVIOUS_CONTRACT_HASH=before-edit-hash",
            "AMENDMENT_REASON=required-regression",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert '--previous-contract-hash "before-edit-hash"' in result.stdout
    assert '--reason "required-regression"' in result.stdout


def test_project_test_uses_stricter_coverage_floor():
    result = subprocess.run(
        ["make", "-n", "project-test-owned"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "--cov-fail-under=85.10" in result.stdout


def test_project_test_owned_runs_the_bounded_manifest_shards_and_aggregate():
    result = subprocess.run(
        ["make", "-n", "project-test-owned"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "project-test-manifest" in result.stdout
    assert "project-test-shards" in result.stdout
    assert "-j5" in result.stdout
    assert "project-test-aggregate" in result.stdout
    assert "project-test-receipt" in result.stdout
    assert "-m pytest -q --cov=scripts" not in result.stdout


def test_project_test_exposes_each_bounded_shard_alias():
    result = subprocess.run(
        ["make", "-n", "project-test-shard-core"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "scripts/quality_shard_workspace.py run" in result.stdout
    assert '--shard "core"' in result.stdout


def test_project_test_shards_isolate_mutating_tests_in_source_bound_worktrees():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    coordinator = (ROOT / "scripts" / "quality_shard_workspace.py").read_text(encoding="utf-8")

    assert "scripts/quality_shard_workspace.py run" in makefile
    assert "--workspace-root" in makefile
    assert '["worktree", "add", "--detach"' in coordinator
    assert '["worktree", "remove", "--force"' in coordinator
    assert "copy_current_evidence" in coordinator
    assert "regenerate_workspace" in coordinator
    assert "publish_artifacts" in coordinator
    assert "quality_test_manifest.py" in coordinator


def test_project_test_manifest_is_a_public_make_target_with_live_collection():
    result = subprocess.run(
        ["make", "-n", "project-test-manifest"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "scripts/quality_test_manifest.py" in result.stdout
    assert "--output target/quality/project-test-manifest.json" in result.stdout
    assert "--plan-output target/quality/project-test-shard-plan.json" in result.stdout


def test_coverage_floor_rejects_a_result_that_only_rounds_to_85(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    covered = [f"value_{index} = {index}" for index in range(1, 170)]
    uncovered = ["def uncovered():", *[f"    value_{index} = {index}" for index in range(30)]]
    uncovered.append("    return value_29")
    (tmp_path / "subject.py").write_text(
        "\n".join([*covered, *uncovered]) + "\n",
        encoding="utf-8",
    )
    test_path = tmp_path / "test_subject.py"
    test_path.write_text(
        "import subject\n\n\ndef test_subject():\n    assert subject.value_1 == 1\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(test_path),
            "--cov=subject",
            "--cov-report=term",
            "--cov-fail-under=85",
            f"--cov-config={ROOT / 'pyproject.toml'}",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert "Total coverage: 84.58%" in result.stdout
    assert result.returncode != 0, result.stdout + result.stderr


def test_quality_runs_static_tests_and_evidence_as_explicit_phases():
    result = subprocess.run(
        ["make", "-n", "quality"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "quality-full" in result.stdout
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "quality-static:" in makefile
    assert "quality-tests:" in makefile
    assert "quality-evidence:" in makefile
    assert "check-trust-guards" in makefile
    assert "check-critical-domain-guards" in makefile
    assert "check-decision-protocol" in makefile
    assert "check-baseline-evidence" in makefile
    assert "--cov-fail-under=85.10" in makefile
    assert "\n\t+$(AI_PYTHON) scripts/run_quality_gate.py" not in makefile
    quality_section = makefile.split("quality-full:", 1)[1].split("# Backward-compatible", 1)[0]
    assert "\n\t+@set -eu;" not in quality_section


def test_quality_busy_recovery_uses_a_canonical_make_command():
    lock_script = ROOT / "scripts" / "quality_session_lock.py"
    assert lock_script.is_file()
    text = lock_script.read_text(encoding="utf-8")
    assert "Retry: make quality" in text
    assert "BUSY_EXIT_CODE = 75" in text


def test_quality_summary_receives_governance_receipt_metadata_when_available():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert 'QUALITY_PROFILE="$$profile"' in makefile
    assert 'QUALITY_ESCALATIONS="$$escalations"' in makefile
    assert '--profile "$(QUALITY_PROFILE)"' in makefile
    assert "$(QUALITY_ESCALATIONS)" in makefile


def test_project_governance_make_targets_are_public():
    result = subprocess.run(
        [
            "make",
            "-n",
            "cockpit-doctor",
            "cockpit-calibrate",
            "cockpit-validate-calibration",
            "check-ai-guard-calibration",
            "ai-onboard",
            "PHASE=2",
            "ai-preflight",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ai_project_doctor.py" in result.stdout
    assert "ai_calibrate.py generate" in result.stdout
    assert "ai_check_guard_calibration.py" in result.stdout
    assert "ai_onboard.py" in result.stdout
    assert "ai_preflight_review.py" in result.stdout


def test_governance_quality_keeps_release_graph_outside_active_work_item_routing():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    template = (ROOT / "templates/make/Makefile.ai").read_text(encoding="utf-8")

    assert '"verificationEscalations"' in makefile
    for content in (makefile, template):
        assert "quality-release:" in content

    assert (
        'if $(PYTHON_EXECUTABLE) -c \'import json, sys; raise SystemExit(0 if "release_preflight"'
        not in makefile
    )
    assert (
        'if $(PYTHON) -c \'import json, sys; raise SystemExit(0 if "release_preflight"'
        not in template
    )
    assert "\n\t+$(AI_NESTED_MAKE) --no-print-directory quality-" not in template


def test_lockfile_reproducibility_uses_python_module_invocation():
    result = subprocess.run(
        ["make", "-n", "check-lockfile-reproducibility", "PYTHON=python3"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "-m piptools compile" in result.stdout
    assert "$(dir $(abspath $(PYTHON)))pip-compile" not in result.stdout
    resolved = shutil.which("python3")
    assert resolved is not None
    assert f'"{resolved}" -m piptools compile' in result.stdout
    assert f'"{ROOT}/python3" -m piptools compile' not in result.stdout


def test_lockfile_reproducibility_normalizes_nonsemantic_via_comments():
    result = subprocess.run(
        ["make", "-n", "check-lockfile-reproducibility", "PYTHON=python3"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "awk '/^    # via/" in result.stdout
    assert "normalized/generated.lock" in result.stdout


def test_lockfile_reproducibility_fails_when_compiler_fails(tmp_path):
    failing_python = tmp_path / "failing-python"
    failing_python.write_text("#!/bin/sh\nexit 17\n", encoding="utf-8")
    failing_python.chmod(0o755)

    result = subprocess.run(
        ["make", "check-lockfile-reproducibility", f"PYTHON={failing_python}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0, result.stdout + result.stderr


def test_make_prefers_project_venv_and_allows_explicit_python_override(tmp_path):
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"AI_PYTHON", "PYTHON", "MAKEFLAGS", "MAKEOVERRIDES"}
    }
    makefile_content = (ROOT / "Makefile").read_text(encoding="utf-8")
    (tmp_path / "Makefile").write_text(makefile_content, encoding="utf-8")

    # When no .venv exists, defaults to python3
    automatic_no_venv = subprocess.run(
        ["make", "-n", "test"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        env=clean_env,
    )
    assert automatic_no_venv.returncode == 0
    assert "python3 -m pytest" in automatic_no_venv.stdout

    # When .venv exists, uses .venv/bin/python
    venv_python = tmp_path / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()

    automatic_with_venv = subprocess.run(
        ["make", "-n", "test"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        env=clean_env,
    )
    assert automatic_with_venv.returncode == 0
    assert ".venv/bin/python -m pytest" in automatic_with_venv.stdout

    # Explicit override works regardless
    explicit = subprocess.run(
        ["make", "-n", "test", "PYTHON=/custom/python"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        env=clean_env,
    )
    assert explicit.returncode == 0
    assert "/custom/python -m pytest" in explicit.stdout


def test_nested_make_keeps_bytecode_suppression_when_ai_python_is_in_environment():
    environment = {**os.environ, "AI_PYTHON": "/ambient/python"}
    result = subprocess.run(
        ["make", "-n", "ai-finish", "TASK=example"],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PYTHONDONTWRITEBYTECODE=1" in result.stdout
    assert "/ambient/python scripts/ai_finish.py" not in result.stdout


def test_ai_finish_forwards_explicit_report_language_without_implicit_archive():
    result = subprocess.run(
        ["make", "-n", "ai-finish", "TASK=example", "REPORT_LANGUAGE=zh-CN"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert '--language "zh-CN"' in result.stdout
    assert "--archive" not in result.stdout
    assert "env -u ARCHIVE -u MAKEFLAGS -u MAKEOVERRIDES" in result.stdout


def test_ai_finish_defaults_report_language_when_not_supplied_and_template_matches():
    result = subprocess.run(
        ["make", "-n", "ai-finish", "TASK=example", "REPORT_LANGUAGE="],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert '--language "en"' in result.stdout
    for path in (ROOT / "Makefile", ROOT / "templates" / "make" / "Makefile.ai"):
        text = path.read_text(encoding="utf-8")
        assert "$(or $(REPORT_LANGUAGE),en)" in text


def test_ai_finish_keeps_archive_one_shot_in_both_make_entrypoints():
    for path in (ROOT / "Makefile", ROOT / "templates" / "make" / "Makefile.ai"):
        text = path.read_text(encoding="utf-8")
        finish_recipe = text.split("ai-finish:\n", 1)[1].split("\n\n", 1)[0]
        assert "env -u ARCHIVE -u MAKEFLAGS -u MAKEOVERRIDES" in finish_recipe
        assert "$(if $(filter true,$(ARCHIVE)),--archive)" in finish_recipe


def test_make_entrypoint_is_exported_and_all_recursive_calls_use_it():
    for path in (ROOT / "Makefile", ROOT / "templates" / "make" / "Makefile.ai"):
        text = path.read_text(encoding="utf-8")
        assert "override AI_COCKPIT_MAKE_ENTRYPOINT := $(firstword $(MAKEFILE_LIST))" in text
        assert "export AI_COCKPIT_MAKE_ENTRYPOINT" in text
        assert 'AI_NESTED_MAKE = "$(MAKE)" -f "$(AI_COCKPIT_MAKE_ENTRYPOINT)"' in text
        assert "$(shell command -v make)" not in text
        assert '"$${MAKE:-make}"' not in text


def test_ai_pre_merge_clears_base_commit_for_quality_steps():
    env = {**os.environ, "AI_BASE_COMMIT": "abc123"}
    template_makefile_content = (ROOT / "templates" / "make" / "Makefile.ai").read_text(
        encoding="utf-8"
    )
    assert "env -u AI_BASE_COMMIT" in template_makefile_content
    result = subprocess.run(
        ["make", "-n", "ai-pre-merge", "AI_BASE_COMMIT=abc123"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "env -u AI_BASE_COMMIT -u AI_COCKPIT_EXECUTION_MODE -u MAKEFLAGS -u MAKEOVERRIDES"
        in result.stdout
    )
    assert 'check-ai-diff-ownership AI_BASE_COMMIT="abc123"' in result.stdout
    assert 'check-ai-pr AI_BASE_COMMIT="abc123"' in result.stdout


def test_check_ai_no_active_branch_is_read_only(tmp_path):
    # Make implementations may render shell recipe indentation differently.
    makefile_content = (ROOT / "Makefile").read_text(encoding="utf-8")
    (tmp_path / "Makefile").write_text(makefile_content, encoding="utf-8")

    result = subprocess.run(
        ["make", "-n", "check-ai", "AI_BASE_COMMIT=abc123"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    else_match = re.search(r"\n\s*else\b", result.stdout)
    assert else_match, result.stdout
    no_active_branch = result.stdout[else_match.end() :]
    assert "ai_generate_status.py --no-active" not in no_active_branch
    assert "check-ai-status-consistency" in no_active_branch
    assert "check-ai-guards" not in no_active_branch
    assert "check-ai-agent-risk" not in no_active_branch
    assert "check-ai-review-policy" not in no_active_branch
    assert "check-ai-diff-ownership" in no_active_branch
    assert 'check-ai-pr AI_BASE_COMMIT="abc123"' in no_active_branch


def test_distributed_makefile_no_active_branch_requires_pr_gate():
    template = (ROOT / "templates" / "make" / "Makefile.ai").read_text(encoding="utf-8")

    assert "check-ai-diff-ownership" in template
    assert 'test -n "$(AI_BASE_COMMIT)"' in template
    assert 'check-ai-pr AI_BASE_COMMIT="$(AI_BASE_COMMIT)"' in template


def test_release_preflight_requires_current_japanese_capability_evidence(tmp_path):
    marker = tmp_path / "injected"
    source_commit = f'bad"; touch {marker}; #'
    probe = tmp_path / "probe.py"
    probe.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "print(json.dumps({'argv': sys.argv[1:], "
        "'source': os.environ.get('RELEASE_PREFLIGHT_SOURCE_COMMIT')}))\n",
        encoding="utf-8",
    )
    probe.chmod(0o755)
    result = subprocess.run(
        [
            "make",
            "check-release-preflight",
            f"RELEASE_PREFLIGHT_SOURCE_COMMIT={source_commit}",
            f"PYTHON={probe}",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    records = [
        json.loads(line)
        for line in result.stdout.splitlines()
        if line.startswith("{") and '"argv"' in line
    ]
    assert records == [
        {
            "argv": ["scripts/ai_capability_truth.py"],
            "source": source_commit,
        },
        {
            "argv": [
                "scripts/ai_japanese_capability.py",
                "--check",
                "--require-final-reassessment",
            ],
            "source": source_commit,
        },
        {
            "argv": ["scripts/check_pre_release_documentation_alignment.py"],
            "source": source_commit,
        },
        {
            "argv": ["scripts/check_release_preflight.py", "--root", "."],
            "source": source_commit,
        },
    ]
    assert not marker.exists()


def test_release_readiness_uses_japanese_evidence_and_repository_mode(tmp_path):
    probe = tmp_path / "probe.py"
    probe.write_text(
        "#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps({'argv': sys.argv[1:]}))\n",
        encoding="utf-8",
    )
    probe.chmod(0o755)

    result = subprocess.run(
        ["make", "check-release-readiness", f"PYTHON={probe}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    records = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    assert records == [
        {"argv": ["scripts/ai_capability_truth.py"]},
        {
            "argv": [
                "scripts/ai_japanese_capability.py",
                "--check",
                "--require-final-reassessment",
            ]
        },
        {"argv": ["scripts/check_pre_release_documentation_alignment.py"]},
        {
            "argv": [
                "scripts/check_release_preflight.py",
                "--root",
                ".",
                "--mode",
                "repository-readiness",
            ]
        },
    ]


def test_makefile_exposes_paired_japanese_status_generation_and_validation():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "generate-cockpit-status-ja:" in makefile
    assert (
        "scripts/ai_generate_status.py $(CONTRACT) $(STATUS_ARGS) "
        "--language ja --output target/ai_cockpit_status.ja.md"
    ) in makefile
    assert "check-ai-status-ja:" in makefile
    assert (
        "scripts/ai_check_status.py target/ai_cockpit_status.ja.md "
        "$(SUMMARY_ARGS) $(STATUS_ARGS) --language ja"
    ) in makefile


def test_task_outcome_pr_make_entrypoint_accepts_explicit_language():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert (
        'scripts/ai_render_task_outcome_pr.py "$(OUTCOME)" "$(PROFILE)" '
        '$(if $(LANGUAGE),--language "$(LANGUAGE)")'
    ) in makefile
