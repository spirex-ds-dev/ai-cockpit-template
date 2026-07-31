from __future__ import annotations

from pathlib import Path

import ai_calibration_profiles as profiles
from ai_calibrate import proposed_profile
from ai_common import parse_yaml


def test_proposal_projects_lite_controls_without_claiming_human_selection(
    tmp_path: Path,
) -> None:
    proposal_path = tmp_path / "proposal.yaml"
    proposal_path.write_text(
        proposed_profile({"detectedFacts": {}, "suggestedBoundaries": {}}),
        encoding="utf-8",
    )
    proposal = parse_yaml(proposal_path)
    policy = profiles.load_policy(Path(".ai/calibration/profiles.yaml"))

    calibration = proposal["calibrationProfile"]
    assert calibration == {
        "level": "lite",
        "selectedBy": "pending_human",
        "selectedAt": "pending",
        "reasons": [],
        "requiredControls": policy.required_controls("lite"),
        "deferredControls": policy.deferred_controls("lite"),
    }
