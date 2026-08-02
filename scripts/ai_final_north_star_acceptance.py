"""Derive a bounded final remediation decision from explicit evidence facts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

DECISIONS = frozenset({"GO", "CONDITIONAL_GO", "NO_GO"})
REQUIRED_DIMENSIONS = frozenset(
    {
        "installation",
        "upgrade",
        "uninstall",
        "lifecycle",
        "absurd_tests",
        "injection",
        "unknown",
        "agent_self_assertion",
        "real_adopter",
        "provider_evidence",
        "enterprise_boundary",
        "task_outcome",
        "documentation",
        "multilingual",
        "performance",
        "code_quality",
        "stale_assets",
        "recovery",
        "capability_truth",
        "north_star",
    }
)


class FinalAcceptanceError(ValueError):
    """Raised when a final decision lacks the facts needed to support it."""


def evaluate(record: Mapping[str, Any]) -> dict[str, Any]:
    dimensions = record.get("dimensions")
    if not isinstance(dimensions, Mapping):
        raise FinalAcceptanceError("dimensions must be an object")
    missing = sorted(REQUIRED_DIMENSIONS.difference(dimensions))
    if missing:
        raise FinalAcceptanceError(f"missing dimensions: {', '.join(missing)}")
    for name, item in dimensions.items():
        if name not in REQUIRED_DIMENSIONS or not isinstance(item, Mapping):
            raise FinalAcceptanceError("dimensions must contain only named evidence objects")
        if not isinstance(item.get("status"), str) or not isinstance(
            item.get("evidence"), Sequence
        ):
            raise FinalAcceptanceError(f"dimension {name} lacks status or evidence")
    decision = record.get("decision")
    if decision not in DECISIONS:
        raise FinalAcceptanceError("decision must be GO, CONDITIONAL_GO, or NO_GO")
    external_ready = all(
        dimensions[name].get("status") == "verified"
        for name in ("real_adopter", "provider_evidence")
    )
    if decision == "GO" and not external_ready:
        raise FinalAcceptanceError("GO requires verified real_adopter and provider_evidence")
    return {
        "decision": decision,
        "dimensions": dict(dimensions),
        "limitations": list(record.get("limitations", [])),
    }
