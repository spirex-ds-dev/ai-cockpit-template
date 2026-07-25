from pathlib import Path

from ai_install_plan import STEP_NAMES, build_wizard_plan
from ai_installer_detection import detect_installation
from ai_installer_repository import RepositoryFacts


def test_wizard_plan_has_exactly_eight_steps_and_operator_fields() -> None:
    facts = RepositoryFacts(
        root=Path("/tmp/project"),
        commit="abc",
        branch="main",
        remote="origin",
        remote_url="https://example.invalid/project.git",
        default_branch="main",
        clean=True,
        tracked_hygiene=(),
        conflicts=(),
        active_work_items=(),
        symlink_risks=(),
    )
    detection = detect_installation(
        facts=facts,
        mode="new_adoption",
        available_tools={"git", "python", "make", "curl", "sh"},
        stacks={"python", "ios"},
    )

    plan = build_wizard_plan(detection, stack="multi", options={"force": False}, branch="main")

    assert plan.step_names == STEP_NAMES
    assert len(plan.steps) == 8
    for step in plan.steps:
        assert step.purpose and step.why and step.facts and step.suggested_value
        assert step.option_impact and step.example and step.write_status
        assert step.expected_result and step.stop_condition and step.checklist
    assert plan.to_dict()["steps"][6]["name"] == "Installation Plan Review"
