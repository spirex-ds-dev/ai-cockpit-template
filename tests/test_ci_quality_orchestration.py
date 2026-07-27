from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY = ROOT / ".github" / "workflows" / "compatibility.yml"
SMOKE = ROOT / ".github" / "workflows" / "smoke.yml"
MAKEFILE = ROOT / "Makefile"


def test_python_matrix_uses_lightweight_compatibility_command():
    workflow = COMPATIBILITY.read_text(encoding="utf-8")

    assert "os: [ubuntu-latest, macos-latest]" in workflow
    assert 'python: ["3.10", "3.11", "3.14"]' in workflow
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


def test_pr_evidence_scope_records_skipped_release_jobs_without_requiring_them():
    smoke = SMOKE.read_text(encoding="utf-8")
    evidence = smoke.split("  ci-evidence:", 1)[1]

    assert "needs: [template-smoke, installation-smoke, release-evidence]" in evidence
    assert "needs.template-smoke.result" in evidence
    assert "needs.installation-smoke.result" in evidence
    assert "needs.release-evidence.result" in evidence
    assert (
        'requiredJobNames: ["template-smoke", "installation-smoke", "release-evidence"]' in evidence
    )


def test_ci_evidence_is_terminal_aggregate_job():
    smoke = SMOKE.read_text(encoding="utf-8")
    template = smoke.split("  installation-smoke:", 1)[0]

    assert "Generate independently verifiable CI evidence" not in template
    assert "  ci-evidence:" in smoke
    assert "if: always()" in smoke.split("  ci-evidence:", 1)[1]
    assert smoke.index("  ci-evidence:") > smoke.index("  release-evidence:")


def test_release_evidence_requires_explicit_release_intent():
    smoke = SMOKE.read_text(encoding="utf-8")
    release = smoke.split("  release-evidence:", 1)[1].split("  ci-evidence:", 1)[0]

    assert "RELEASE_PREPARATION_INTENT" in release
    assert '[[ "$RELEASE_PREPARATION_INTENT" == "true" ]]' in release
    assert "No explicit release-preparation intent" in release


def test_compatibility_target_disables_coverage_overhead():
    makefile = MAKEFILE.read_text(encoding="utf-8")
    target = makefile.split("compatibility-test:", 1)[1].split("\n\n", 1)[0]

    assert "pytest -q --no-cov" in target
    assert "tests/test_input_trust.py" in target
    assert "tests/test_input_trust_corpus.py" in target
    assert "tests/test_workflows.py" in target
    assert "tests/test_ci_quality_orchestration.py" in target
