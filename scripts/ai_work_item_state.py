"""Deterministic Work Item lifecycle transition and recovery evaluator."""

from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

STATES = (
    "created",
    "preflight_ready",
    "implementation_active",
    "verification_pending",
    "finish_ready",
    "archived",
    "pushed",
    "pr_open",
    "merged",
    "close_authorized",
    "closed",
    "paused",
    "blocked",
    "cancelled",
    "rollback",
    "stale",
)
CANONICAL = {
    "created": "preflight_ready",
    "preflight_ready": "implementation_active",
    "implementation_active": "verification_pending",
    "verification_pending": "finish_ready",
    "finish_ready": "archived",
    "archived": "pushed",
    "pushed": "pr_open",
    "pr_open": "merged",
    "merged": "close_authorized",
    "close_authorized": "closed",
}
REQUIRED_EVIDENCE = {
    "preflight_ready": "preflight",
    "verification_pending": "verification",
    "finish_ready": "finish",
    "archived": "archive",
    "pushed": "push",
    "pr_open": "pr",
    "merged": "merge",
    "close_authorized": "close_authorization",
    "closed": "closure",
}


def event_id(work_item: str, current: str, target: str, evidence: dict[str, Any]) -> str:
    payload = json.dumps(
        {"workItem": work_item, "current": current, "target": target, "evidence": evidence},
        sort_keys=True,
    )
    return "EV-" + hashlib.sha256(payload.encode()).hexdigest()[:16]


def transition(
    current: str, target: str, *, work_item: str = "unknown", evidence: dict[str, Any] | None = None
) -> dict[str, Any]:
    evidence = evidence or {}
    result: dict[str, Any] = {
        "allowed": False,
        "state": current,
        "target": target,
        "resumeCondition": "",
    }
    if current not in STATES or target not in STATES:
        result.update(reason="unknown state", resumeCondition="Use a declared lifecycle state.")
        return result
    if current == target:
        result.update(
            allowed=True,
            reason="idempotent no-op",
            eventId=event_id(work_item, current, target, evidence),
        )
        return result
    expected = CANONICAL.get(current)
    if target != expected:
        result.update(
            reason="transition is not in the canonical order",
            resumeCondition=f"Move through {expected or 'a recovery state'} with evidence.",
        )
        return result
    required = REQUIRED_EVIDENCE.get(target)
    if not required or evidence.get("type") != required or not evidence.get("digest"):
        result.update(
            reason="required evidence is missing or malformed",
            resumeCondition=f"Provide {required} evidence with a digest.",
        )
        return result
    if (
        evidence.get("stale")
        or evidence.get("contradictory")
        or evidence.get("remoteConsistent") is False
    ):
        result.update(
            reason="evidence is stale, contradictory, or locally/remotely inconsistent",
            resumeCondition="Reconcile the evidence and retry the transition.",
        )
        return result
    result.update(
        allowed=True,
        state=target,
        reason="transition accepted",
        eventId=event_id(work_item, current, target, evidence),
    )
    return result


def recover(
    state: str,
    *,
    interrupted: bool = False,
    provider_status: str = "consistent",
    base_status: str = "current",
) -> dict[str, Any]:
    if state not in STATES:
        return {"state": "blocked", "recoverable": False, "reason": "unknown state"}
    if provider_status != "consistent" or base_status != "current":
        return {
            "state": "stale",
            "recoverable": True,
            "reason": "external or base evidence is inconsistent",
            "resumeCondition": "Reconcile provider and base evidence before retry.",
        }
    if interrupted:
        return {
            "state": "paused",
            "recoverable": True,
            "reason": "operation was interrupted",
            "resumeCondition": "Resume from the last durable event; do not duplicate archive or cleanup.",
        }
    return {
        "state": state,
        "recoverable": state not in {"closed", "cancelled"},
        "reason": "no recovery action required",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default="created")
    parser.add_argument("--target", default="preflight_ready")
    args = parser.parse_args()
    print(json.dumps(transition(args.state, args.target), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
