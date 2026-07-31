from __future__ import annotations

from pathlib import Path

import ai_calibration_profiles as profiles
from ai_calibrate import proposed_profile
from ai_common import parse_yaml
from ai_project_profile import validate_profile

POLICY = Path(".ai/calibration/profiles.yaml")


def selection(level: str, policy: profiles.CalibrationProfilePolicy) -> dict[str, object]:
    return {
        "level": level,
        "selectedBy": "human",
        "selectedAt": "2026-08-01T00:00:00Z",
        "reasons": ["Initial internal adoption"],
        "requiredControls": policy.required_controls(level),
        "deferredControls": policy.deferred_controls(level),
    }


def test_policy_resolves_exact_cumulative_controls_and_lite_exclusions() -> None:
    policy = profiles.load_policy(POLICY)

    assert policy.levels == ("lite", "standard", "strict")
    assert policy.required_controls("lite") == [
        "source_paths",
        "test_paths",
        "generated_paths",
        "protected_paths",
        "quality_command",
        "default_branch",
        "project_owner",
        "reviewer",
        "major_unknowns",
    ]
    assert set(policy.required_controls("standard")) > set(policy.required_controls("lite"))
    assert set(policy.required_controls("strict")) > set(policy.required_controls("standard"))
    assert "release_evidence" not in policy.required_controls("lite")
    assert "external_identity_evidence" not in policy.required_controls("lite")
    assert "release_evidence" in policy.deferred_controls("lite")
    assert policy.deferred_controls("strict") == []


def test_selection_requires_human_evidence_and_exact_control_projection() -> None:
    policy = profiles.load_policy(POLICY)
    value = selection("lite", policy)

    assert profiles.validate_selection(value, policy) == []

    value["selectedBy"] = "agent"
    value["selectedAt"] = "not-a-time"
    value["reasons"] = []
    value["requiredControls"] = ["source_paths"]
    value["deferredControls"] = []
    issues = profiles.validate_selection(value, policy)

    assert "calibrationProfile.selectedBy must be human" in issues
    assert "calibrationProfile.selectedAt must be an ISO-8601 timestamp" in issues
    assert "calibrationProfile.reasons must contain at least one non-empty string" in issues
    assert "calibrationProfile.requiredControls do not match the selected level" in issues
    assert "calibrationProfile.deferredControls do not match the selected level" in issues


def test_upgrades_are_monotonic_without_downgrade_exception() -> None:
    policy = profiles.load_policy(POLICY)

    assert (
        profiles.validate_selection(selection("standard", policy), policy, previous_level="lite")
        == []
    )
    assert (
        profiles.validate_selection(selection("strict", policy), policy, previous_level="standard")
        == []
    )
    assert (
        profiles.validate_selection(selection("strict", policy), policy, previous_level="lite")
        == []
    )

    contradictory = selection("strict", policy)
    contradictory["transition"] = {
        "originalLevel": "strict",
        "newLevel": "lite",
    }
    issues = profiles.validate_selection(contradictory, policy, previous_level="standard")
    assert "calibrationProfile.transition.originalLevel does not match previous level" in issues
    assert "calibrationProfile.transition.newLevel does not match selected level" in issues


def test_downgrade_requires_complete_bounded_risk_acceptance() -> None:
    policy = profiles.load_policy(POLICY)
    value = selection("lite", policy)

    assert (
        "calibrationProfile downgrade requires transition evidence"
        in profiles.validate_selection(value, policy, previous_level="standard")
    )

    closed = [
        control
        for control in policy.required_controls("standard")
        if control not in policy.required_controls("lite")
    ]
    value["transition"] = {
        "originalLevel": "standard",
        "newLevel": "lite",
        "reason": "The repository is now an isolated prototype.",
        "closedControls": closed,
        "riskAcceptedBy": "repository-owner",
        "effectiveScope": ["prototype/**"],
    }
    assert profiles.validate_selection(value, policy, previous_level="standard") == []

    value["transition"]["closedControls"] = ["ci_policy"]
    value["transition"]["riskAcceptedBy"] = ""
    issues = profiles.validate_selection(value, policy, previous_level="standard")
    assert "calibrationProfile.transition.closedControls do not match the downgrade" in issues
    assert "calibrationProfile.transition.riskAcceptedBy must be a non-empty string" in issues


def test_policy_rejects_unknown_levels_and_duplicate_controls(tmp_path: Path) -> None:
    malformed = tmp_path / "profiles.yaml"
    malformed.write_text(
        "version: 1\nlevels:\n  - lite\n  - standard\n  - strict\ncontrols:\n"
        "  lite:\n    - source_paths\n  standard:\n    - source_paths\n"
        "  strict:\n    - release_evidence\n",
        encoding="utf-8",
    )

    try:
        profiles.load_policy(malformed)
    except profiles.CalibrationProfileError as exc:
        assert "duplicate control" in str(exc)
    else:
        raise AssertionError("malformed policy must fail closed")

    policy = profiles.load_policy(POLICY)
    assert profiles.validate_selection({"level": "release"}, policy) == [
        "calibrationProfile.level must be one of ['lite', 'standard', 'strict']"
    ]


def test_project_profile_keeps_legacy_compatibility_and_validates_declared_profile() -> None:
    current = parse_yaml(Path(".ai/project_profile.yaml"))
    assert validate_profile(current, require_approval=True) == []

    legacy = dict(current)
    legacy.pop("calibrationProfile", None)
    assert validate_profile(legacy, require_approval=True) == []

    malformed = dict(current)
    malformed["calibrationProfile"] = {"level": "lite"}
    assert any(
        issue.startswith("calibrationProfile.selectedBy")
        for issue in validate_profile(malformed, require_approval=True)
    )


def test_generated_proposal_exposes_lite_projection_without_claiming_human_selection(
    tmp_path: Path,
) -> None:
    rendered = proposed_profile({"detectedFacts": {}, "suggestedBoundaries": {}})
    proposal_path = tmp_path / "proposal.yaml"
    proposal_path.write_text(rendered, encoding="utf-8")
    proposed = parse_yaml(proposal_path)
    assert isinstance(proposed, dict)
    policy = profiles.load_policy(POLICY)

    calibration = proposed["calibrationProfile"]
    assert calibration["level"] == "lite"
    assert calibration["selectedBy"] == "pending_human"
    assert calibration["selectedAt"] == "pending"
    assert calibration["reasons"] == []
    assert calibration["requiredControls"] == policy.required_controls("lite")
    assert calibration["deferredControls"] == policy.deferred_controls("lite")
    assert not [
        issue
        for issue in validate_profile(proposed, require_approval=False)
        if issue.startswith("calibrationProfile")
    ]
