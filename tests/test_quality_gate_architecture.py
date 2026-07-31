import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"
REGISTRY = ROOT / ".ai" / "quality" / "gates.yaml"


def _target_block(name: str) -> str:
    text = MAKEFILE.read_text(encoding="utf-8")
    return text.split(f"{name}:", 1)[1].split("\n\n", 1)[0]


def test_quality_entry_points_have_explicit_compatibility_semantics():
    text = MAKEFILE.read_text(encoding="utf-8")
    assert "quality-fast:" in text
    assert "quality-standard:" in text
    assert "quality-full:" in text
    assert "quality-release:" in text
    assert "quality:\n\t+$(QUALITY_MAKE) --no-print-directory quality-full" in text
    assert "quality-gates: quality-full" in text
    assert "define RUN_QUALITY_GATE" in text
    assert "$(call RUN_QUALITY_GATE,project-format-check,static)" in text
    assert "$(call RUN_QUALITY_GATE,project-test,tests)" in text
    assert "$(call RUN_QUALITY_GATE,check-sbom,supply-chain)" in text
    assert "scripts/summarize_quality_gates.py" in text


def test_default_quality_entrypoint_routes_without_duplicating_gate_commands():
    routed = _target_block("ai-cockpit-quality")
    standard = _target_block("quality-standard")

    assert "scripts/determine_governance_profile.py" in routed
    assert "dispatchTarget" in routed
    assert "$(QUALITY_MAKE)" in routed
    assert "quality-fast" in standard
    assert "project-test" in standard
    assert "check-ai-reference-impact" in standard
    assert "check-ai-test-weakening" in standard
    assert "quality-full" not in standard
    assert "quality-release" not in standard


def test_standard_quality_dry_run_uses_only_its_required_owners():
    result = subprocess.run(
        ["make", "-n", "quality-standard"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "quality-fast" in result.stdout
    assert "project-test" in result.stdout
    assert "check-ai-reference-impact" in result.stdout
    assert "check-ai-test-weakening" in result.stdout
    assert "quality-full" not in result.stdout
    assert "quality-release" not in result.stdout


def test_specialized_debug_targets_remain_but_are_not_quality_full_subgates():
    text = MAKEFILE.read_text(encoding="utf-8")
    for target in (
        "check-trust-guards:",
        "check-critical-domain-guards:",
        "check-decision-protocol:",
        "check-baseline-evidence:",
    ):
        assert target in text
    heavy = _target_block("quality-heavy")
    assert "check-trust-guards" not in heavy
    assert "check-critical-domain-guards" not in heavy
    assert "check-decision-protocol" not in heavy
    assert "check-baseline-evidence" not in heavy


def test_registry_declares_no_parallel_write_conflicts():
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    seen: dict[tuple[str, str], str] = {}
    for gate, config in data["gates"].items():
        for path in config.get("writes", []):
            key = (config.get("parallelGroup", ""), path)
            assert key not in seen, f"{path} conflicts between {seen.get(key)} and {gate}"
            seen[key] = gate


def test_release_preserves_security_and_installation_ownership():
    text = MAKEFILE.read_text(encoding="utf-8")
    release = _target_block("quality-release")
    for required in ("quality-full", "quality-installation", "quality-release-evidence"):
        assert required in release
    for required in (
        "check-bandit-baseline",
        "check-sbom",
        "check-provenance",
        "check-secret-scanning",
    ):
        assert required in text


def test_smoke_assigns_quality_installation_and_release_to_distinct_jobs():
    smoke = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    assert "  template-smoke:" in smoke
    assert "  installation-smoke:" in smoke
    assert "  release-evidence:" in smoke
    installation = smoke.split("  installation-smoke:", 1)[1].split("\n  release-evidence:", 1)[0]
    release = smoke.split("  release-evidence:", 1)[1].split("\n  ci-evidence:", 1)[0]
    assert "needs: template-smoke" not in installation
    assert "needs: template-smoke" not in release
    assert "needs: [template-smoke, installation-smoke, release-evidence]" in smoke
    assert "actions/upload-artifact@" in smoke
    assert "name: Upload quality diagnostics" in smoke
    assert "if: always()" in smoke
    assert smoke.count("make quality") == 1


def test_installation_smoke_archives_active_outcome_before_commit_and_guards():
    smoke = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    installation = smoke.split("  installation-smoke:", 1)[1].split("\n  release-evidence:", 1)[0]
    finish = "make ai-finish TASK=adopt_ai_cockpit"
    archive = "make archive-work-item CONTRACT=.ai/work-items/active/adopt_ai_cockpit.contract.json"
    active = "if test -f .ai/work-items/active/adopt_ai_cockpit.contract.json; then"
    archived = "test -f .ai/work-items/archive/2026/adopt_ai_cockpit.contract.json"
    assert finish in installation
    assert archive in installation
    assert active in installation
    assert archived in installation
    assert installation.index(finish) < installation.index(active) < installation.index(archive)
    assert (
        installation.index(archive) < installation.index(archived) < installation.index("git add .")
    )
    assert installation.index(archived) < installation.index("make check-ai-coverage-guard")


def test_smoke_uses_node24_upload_artifact_release_for_quality_diagnostics():
    smoke = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    upload = smoke.split("- name: Upload quality diagnostics", 1)[1].split(
        "- name: Run template AI checks", 1
    )[0]
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in upload
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" not in smoke
    assert "target/coverage.json" in upload


def test_quality_full_uses_commit_and_run_bound_session_directories():
    text = MAKEFILE.read_text(encoding="utf-8")
    assert "target/quality/sessions" in text
    assert "QUALITY_SESSION_ID" in text
    assert "GITHUB_RUN_ID" in text
    assert "--session-id" in text
    assert "--run-id" in text
    assert "trap 'printf" in text
    assert "target/quality/current-session.txt' EXIT" in text


def test_quality_full_uses_owned_phase_cleanup_helper():
    full = _target_block("quality-full")
    assert "scripts/run_quality_session.py" in full
    assert "quality-fast" in full
    assert "quality-heavy" in full


def test_full_quality_runs_canonical_release_state_consistency_gate():
    result = subprocess.run(
        ["make", "-n", "quality"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--gate check-release-state-consistency" in result.stdout
