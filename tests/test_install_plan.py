from pathlib import Path

from ai_install_plan import STEP_NAMES, build_wizard_plan
from ai_installer_detection import detect_installation
from ai_installer_evidence import InstallationPreview
from ai_installer_repository import RepositoryFacts


def test_wizard_plan_has_exactly_ten_stages_and_operator_fields() -> None:
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

    preview = InstallationPreview(
        adds=41,
        modifies=1,
        skips=2,
        source_code_changes=False,
        branch="adopt/ai-cockpit",
    )
    plan = build_wizard_plan(
        detection,
        stack="multi",
        options={"force": False},
        branch="adopt/ai-cockpit",
        profile="standard",
        preview=preview,
    )

    assert plan.step_names == STEP_NAMES
    assert plan.step_names == (
        "Target Repository",
        "Readiness",
        "Installation Mode",
        "Governance Profile",
        "Planned Changes",
        "Conflict Review",
        "Explicit Confirmation",
        "Installation",
        "Verification",
        "Next Action",
    )
    assert len(plan.steps) == 10
    for step in plan.steps:
        assert step.purpose and step.why and step.facts and step.suggested_value
        assert step.option_impact and step.example and step.write_status
        assert step.expected_result and step.stop_condition and step.checklist
    assert plan.profile == "standard"
    assert plan.preview == preview
    assert plan.to_dict()["steps"][4]["facts"] == {
        "adds": 41,
        "modifies": 1,
        "skips": 2,
        "sourceCodeChanges": False,
        "branch": "adopt/ai-cockpit",
    }
    assert plan.to_dict()["steps"][5]["facts"]["conflicts"] == []
    assert "calibration remains separate" in plan.steps[9].expected_result.lower()
    assert "REPORT_LANGUAGE=<conversation-locale>" in plan.steps[9].example
