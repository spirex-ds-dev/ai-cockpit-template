"""Canonical machine terms and their human-facing locale labels.

Governance Profile and Calibration Profile are separate domains.  Their shared
values do not make ``lite`` and ``light`` interchangeable.
"""

from __future__ import annotations

from typing import Final

GOVERNANCE_PROFILES: Final = ("light", "standard", "strict")
CALIBRATION_PROFILES: Final = ("lite", "standard", "strict")
STATUS_COLORS: Final = ("green", "yellow", "red", "unknown")

STATUS_LABELS: Final = {
    "green": {"en": "green", "ja": "緑", "zh-CN": "绿色"},
    "yellow": {"en": "yellow", "ja": "黄", "zh-CN": "黄色"},
    "red": {"en": "red", "ja": "赤", "zh-CN": "红色"},
    "unknown": {"en": "unknown", "ja": "不明", "zh-CN": "未知"},
}


def _validate(value: object, allowed: tuple[str, ...], domain: str) -> str:
    if isinstance(value, str) and value in allowed:
        return value
    raise ValueError(f"unsupported {domain}: {value!r}; expected one of {list(allowed)}")


def validate_governance_profile(value: object) -> str:
    """Return one Governance Profile or reject cross-domain input."""

    return _validate(value, GOVERNANCE_PROFILES, "governance profile")


def validate_calibration_profile(value: object) -> str:
    """Return one Calibration Profile or reject cross-domain input."""

    return _validate(value, CALIBRATION_PROFILES, "calibration profile")


def validate_status_color(value: object) -> str:
    """Return one human-facing status color or reject an invented color."""

    return _validate(value, STATUS_COLORS, "status color")
