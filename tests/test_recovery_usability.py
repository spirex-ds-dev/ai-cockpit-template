from __future__ import annotations

import copy

import ai_recovery_usability as recovery
import pytest


def guidance(scenario: str) -> dict[str, object]:
    return {
        "scenario": scenario,
        "currentState": "The operation stopped before completion.",
        "writesPerformed": ["The local receipt was written."],
        "rolledBack": ["The temporary checkout was removed."],
        "notRolledBack": ["The remote branch remains unchanged."],
        "nextCommand": "make ai-assess-recovery ARGS='--status target/status.json'",
        "humanInterventionRequired": False,
    }


def test_every_declared_recovery_scenario_has_complete_user_guidance() -> None:
    reports = recovery.validate_recovery_set(
        [guidance(scenario) for scenario in recovery.SCENARIOS]
    )

    assert {report.scenario for report in reports} == recovery.SCENARIOS
    rendered = recovery.render_recovery_report(reports[0])
    for label in (
        "Current state:",
        "Writes performed:",
        "Rolled back:",
        "Not rolled back:",
        "Next command:",
        "Human intervention required:",
    ):
        assert label in rendered
    assert "source code" not in rendered.lower()


@pytest.mark.parametrize(
    "field",
    (
        "currentState",
        "writesPerformed",
        "rolledBack",
        "notRolledBack",
        "nextCommand",
        "humanInterventionRequired",
    ),
)
def test_incomplete_guidance_fails_closed(field: str) -> None:
    value = guidance("conflict")
    value.pop(field)

    with pytest.raises(recovery.RecoveryGuidanceError, match=field):
        recovery.validate_guidance(value)


def test_unknown_and_duplicate_scenarios_fail_closed() -> None:
    unknown = guidance("not_a_scenario")
    with pytest.raises(recovery.RecoveryGuidanceError, match="unknown recovery scenario"):
        recovery.validate_guidance(unknown)

    reports = [guidance(scenario) for scenario in recovery.SCENARIOS]
    reports.append(copy.deepcopy(reports[0]))
    with pytest.raises(recovery.RecoveryGuidanceError, match="must not be duplicated"):
        recovery.validate_recovery_set(reports)


def test_malformed_rollback_information_fails_closed() -> None:
    value = guidance("closure_incomplete")
    value["notRolledBack"] = "unknown"

    with pytest.raises(recovery.RecoveryGuidanceError, match="notRolledBack"):
        recovery.validate_guidance(value)
