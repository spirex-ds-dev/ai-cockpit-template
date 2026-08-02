"""Validate and render source-independent recovery guidance for common failures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

SCENARIOS = frozenset(
    {
        "interrupted_install",
        "upgrade_failed",
        "lock_remaining",
        "branch_recovery_failed",
        "conflict",
        "closure_incomplete",
        "evidence_stale",
        "unknown_source",
        "provider_unavailable",
    }
)


class RecoveryGuidanceError(ValueError):
    """Raised when a recovery report would leave a user without a safe path."""


@dataclass(frozen=True)
class RecoveryGuidance:
    scenario: str
    current_state: str
    writes_performed: tuple[str, ...]
    rolled_back: tuple[str, ...]
    not_rolled_back: tuple[str, ...]
    next_command: str
    human_intervention_required: bool


def _items(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RecoveryGuidanceError(f"{field} must be a list of non-empty strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise RecoveryGuidanceError(f"{field} must be a list of non-empty strings")
    return tuple(value)


def validate_guidance(value: Mapping[str, Any]) -> RecoveryGuidance:
    """Reject incomplete recovery facts before they are shown to an ordinary user."""
    required = {
        "scenario",
        "currentState",
        "writesPerformed",
        "rolledBack",
        "notRolledBack",
        "nextCommand",
        "humanInterventionRequired",
    }
    missing = sorted(required.difference(value))
    if missing:
        raise RecoveryGuidanceError(f"missing required recovery fields: {', '.join(missing)}")

    scenario = value["scenario"]
    if scenario not in SCENARIOS:
        raise RecoveryGuidanceError(f"unknown recovery scenario: {scenario!r}")
    for field in ("currentState", "nextCommand"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise RecoveryGuidanceError(f"{field} must be a non-empty string")
    if not isinstance(value["humanInterventionRequired"], bool):
        raise RecoveryGuidanceError("humanInterventionRequired must be a boolean")

    return RecoveryGuidance(
        scenario=scenario,
        current_state=value["currentState"],
        writes_performed=_items(value["writesPerformed"], "writesPerformed"),
        rolled_back=_items(value["rolledBack"], "rolledBack"),
        not_rolled_back=_items(value["notRolledBack"], "notRolledBack"),
        next_command=value["nextCommand"],
        human_intervention_required=value["humanInterventionRequired"],
    )


def validate_recovery_set(values: Sequence[Mapping[str, Any]]) -> tuple[RecoveryGuidance, ...]:
    """Require exactly one complete report for every declared failure scenario."""
    reports = tuple(validate_guidance(value) for value in values)
    reported = [report.scenario for report in reports]
    if len(reported) != len(set(reported)):
        raise RecoveryGuidanceError("recovery scenarios must not be duplicated")
    missing = sorted(SCENARIOS.difference(reported))
    extra = sorted(set(reported).difference(SCENARIOS))
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing scenarios: {', '.join(missing)}")
        if extra:
            details.append(f"unknown scenarios: {', '.join(extra)}")
        raise RecoveryGuidanceError("; ".join(details))
    return reports


def render_recovery_report(guidance: RecoveryGuidance) -> str:
    """Render every required fact without requiring the user to inspect source code."""

    def listed(items: tuple[str, ...]) -> str:
        return "; ".join(items) if items else "None"

    human = "Yes — stop and ask the named owner." if guidance.human_intervention_required else "No"
    return "\n".join(
        (
            f"Recovery scenario: {guidance.scenario}",
            f"Current state: {guidance.current_state}",
            f"Writes performed: {listed(guidance.writes_performed)}",
            f"Rolled back: {listed(guidance.rolled_back)}",
            f"Not rolled back: {listed(guidance.not_rolled_back)}",
            f"Next command: {guidance.next_command}",
            f"Human intervention required: {human}",
        )
    )
