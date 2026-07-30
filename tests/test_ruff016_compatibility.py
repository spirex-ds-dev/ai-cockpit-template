from pathlib import Path

from ai_common import parse_yaml

ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY_MODULES = {
    "scripts/ai_baseline_evidence.py",
    "scripts/ai_check_archive_recovery.py",
    "scripts/ai_check_budget_impact.py",
    "scripts/ai_check_serial_order.py",
    "scripts/ai_decision_protocol.py",
    "scripts/ai_detached_uninstaller.py",
    "scripts/ai_generate_task_outcome.py",
    "scripts/ai_install_plan.py",
    "scripts/ai_intent_policy.py",
    "scripts/ai_issue_log.py",
    "scripts/ai_lifecycle_facts.py",
    "scripts/ai_project_doctor.py",
    "scripts/ai_purge.py",
    "scripts/ai_render_task_outcome.py",
    "scripts/ai_render_task_outcome_multilingual.py",
    "scripts/ai_render_task_outcome_pr.py",
    "scripts/ai_scenario_policy.py",
    "scripts/ai_task_event_log.py",
    "scripts/ai_upgrade_conflict_report.py",
    "scripts/ai_upgrade_proposal.py",
    "scripts/ai_wizard_io.py",
}


def test_ruff016_compatibility_contract_and_coverage_association_are_explicit():
    requirements = (ROOT / "requirements-dev.in").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    policy = parse_yaml(ROOT / ".ai" / "guards" / "coverage_policy.yaml")

    assert "ruff==0.16.0" in requirements
    assert "$(AI_PYTHON) -m ruff check scripts tests" in makefile
    association = policy["associations"]["ruff016Compatibility"]
    assert set(association["production"]) == COMPATIBILITY_MODULES
    assert association["tests"] == ["tests/test_ruff016_compatibility.py"]
