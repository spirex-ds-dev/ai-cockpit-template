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
    assert "quality-full:" in text
    assert "quality-release:" in text
    assert "quality:\n\t+$(QUALITY_MAKE) --no-print-directory quality-full" in text
    assert "quality-gates: quality-full" in text
    assert "define RUN_QUALITY_GATE" in text
    assert "$(call RUN_QUALITY_GATE,project-format-check,static)" in text
    assert "$(call RUN_QUALITY_GATE,project-test,tests)" in text
    assert "$(call RUN_QUALITY_GATE,check-sbom,supply-chain)" in text
    assert "scripts/summarize_quality_gates.py" in text


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


def test_quality_full_uses_commit_and_run_bound_session_directories():
    text = MAKEFILE.read_text(encoding="utf-8")
    assert "target/quality/sessions" in text
    assert "QUALITY_SESSION_ID" in text
    assert "GITHUB_RUN_ID" in text
    assert "--session-id" in text
    assert "--run-id" in text
    assert "trap 'printf" in text
    assert "target/quality/current-session.txt' EXIT" in text
