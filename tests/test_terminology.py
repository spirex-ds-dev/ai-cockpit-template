"""Tests for the canonical terminology registry."""

import pytest

from scripts.ai_terminology import (
    CALIBRATION_PROFILES,
    GOVERNANCE_PROFILES,
    STATUS_COLORS,
    STATUS_LABELS,
    validate_calibration_profile,
    validate_governance_profile,
    validate_status_color,
)


def test_canonical_governance_profiles_are_separate_from_calibration_profiles() -> None:
    assert GOVERNANCE_PROFILES == ("light", "standard", "strict")
    assert CALIBRATION_PROFILES == ("lite", "standard", "strict")
    assert validate_governance_profile("light") == "light"
    assert validate_calibration_profile("lite") == "lite"
    with pytest.raises(ValueError, match="governance profile"):
        validate_governance_profile("lite")
    with pytest.raises(ValueError, match="calibration profile"):
        validate_calibration_profile("light")


def test_status_colors_and_human_labels_are_canonical_in_three_locales() -> None:
    assert STATUS_COLORS == ("green", "yellow", "red", "unknown")
    assert validate_status_color("green") == "green"
    assert STATUS_LABELS["green"] == {"en": "green", "ja": "緑", "zh-CN": "绿色"}
    assert STATUS_LABELS["unknown"] == {"en": "unknown", "ja": "不明", "zh-CN": "未知"}
    with pytest.raises(ValueError, match="status color"):
        validate_status_color("amber")
