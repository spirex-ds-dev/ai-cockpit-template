from __future__ import annotations

from pathlib import Path

from ai_common import parse_yaml
from ai_project_profile import validate_profile


def test_declared_calibration_profile_is_valid_and_legacy_profile_remains_readable() -> None:
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
