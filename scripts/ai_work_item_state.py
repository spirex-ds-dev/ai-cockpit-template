"""Compatibility adapter for the shared Work Item domain service."""

from __future__ import annotations

import argparse
import json
from typing import Any

from ai_domain_model import (
    CANONICAL_TRANSITIONS,
    LIFECYCLE_STATES,
    DomainService,
    Evidence,
    Transition,
    WorkItem,
    transition_event_id,
)

# Public aliases retain the established adapter contract.
STATES = LIFECYCLE_STATES
CANONICAL = CANONICAL_TRANSITIONS
_DOMAIN = DomainService()


def event_id(work_item: str, current: str, target: str, evidence: dict[str, Any]) -> str:
    """Return the established event identity via the shared domain model."""
    return transition_event_id(
        work_item, Transition(current, target), Evidence.from_mapping(evidence)
    )


def transition(
    current: str, target: str, *, work_item: str = "unknown", evidence: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Adapt the domain decision to the legacy JSON-compatible payload."""
    result = _DOMAIN.transition(
        WorkItem(work_item, current), target, evidence=Evidence.from_mapping(evidence)
    )
    return result.as_legacy_dict()


def recover(
    state: str,
    *,
    interrupted: bool = False,
    provider_status: str = "consistent",
    base_status: str = "current",
) -> dict[str, Any]:
    """Adapt bounded recovery facts without reinterpreting lifecycle state."""
    return _DOMAIN.recover(
        WorkItem("unknown", state),
        interrupted=interrupted,
        provider_status=provider_status,
        base_status=base_status,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default="created")
    parser.add_argument("--target", default="preflight_ready")
    args = parser.parse_args()
    print(json.dumps(transition(args.state, args.target), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
