"""Core typed domain model for governed Work Item facts and transitions.

This module owns lifecycle vocabulary and the decision that advances a Work
Item.  Other scripts may adapt its results, but must not re-declare transition
legality or evidence requirements.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

LIFECYCLE_STATES = (
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
CANONICAL_TRANSITIONS = {
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
REQUIRED_EVIDENCE_KIND = {
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


@dataclass(frozen=True)
class WorkItem:
    work_item_id: str
    state: str = "created"


@dataclass(frozen=True)
class Contract:
    work_item_id: str
    version: int


@dataclass(frozen=True)
class Evidence:
    kind: str
    digest: str
    stale: bool = False
    contradictory: bool = False
    remote_consistent: bool | None = None

    @classmethod
    def from_mapping(cls, value: dict[str, Any] | None) -> Evidence:
        value = value or {}
        return cls(
            kind=str(value.get("type", "")),
            digest=str(value.get("digest", "")),
            stale=bool(value.get("stale")),
            contradictory=bool(value.get("contradictory")),
            remote_consistent=value.get("remoteConsistent"),
        )


@dataclass(frozen=True)
class Receipt:
    event_id: str
    digest: str


@dataclass(frozen=True)
class Decision:
    category: str
    outcome: str


@dataclass(frozen=True)
class Transition:
    current: str
    target: str


@dataclass(frozen=True)
class Finding:
    checker_id: str
    reason_code: str


@dataclass(frozen=True)
class Risk:
    level: str
    area: str


@dataclass(frozen=True)
class HumanDecision:
    decided_by: str
    decision: str


@dataclass(frozen=True)
class CapabilityClaim:
    capability: str
    state: str


@dataclass(frozen=True)
class Closure:
    work_item_id: str
    state: str


@dataclass(frozen=True)
class TransitionResult:
    allowed: bool
    state: str
    target: str
    reason: str
    resume_condition: str = ""
    event_id: str | None = None

    def as_legacy_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "allowed": self.allowed,
            "state": self.state,
            "target": self.target,
            "resumeCondition": self.resume_condition,
            "reason": self.reason,
        }
        if self.event_id:
            result["eventId"] = self.event_id
        return result


def transition_event_id(work_item_id: str, transition: Transition, evidence: Evidence) -> str:
    payload = json.dumps(
        {
            "workItem": work_item_id,
            "current": transition.current,
            "target": transition.target,
            "evidence": {
                "type": evidence.kind,
                "digest": evidence.digest,
                "stale": evidence.stale,
                "contradictory": evidence.contradictory,
                "remoteConsistent": evidence.remote_consistent,
            },
        },
        sort_keys=True,
    )
    return "EV-" + hashlib.sha256(payload.encode()).hexdigest()[:16]


class DomainService:
    """The sole authority for bounded Work Item lifecycle decisions."""

    def transition(
        self, work_item: WorkItem, target: str, *, evidence: Evidence | None = None
    ) -> TransitionResult:
        evidence = evidence or Evidence(kind="", digest="")
        current = work_item.state
        transition = Transition(current, target)
        if current not in LIFECYCLE_STATES or target not in LIFECYCLE_STATES:
            return TransitionResult(
                False,
                current,
                target,
                "unknown state",
                "Use a declared lifecycle state.",
            )
        if current == target:
            return TransitionResult(
                True,
                current,
                target,
                "idempotent no-op",
                event_id=transition_event_id(work_item.work_item_id, transition, evidence),
            )
        expected = CANONICAL_TRANSITIONS.get(current)
        if target != expected:
            return TransitionResult(
                False,
                current,
                target,
                "transition is not in the canonical order",
                f"Move through {expected or 'a recovery state'} with evidence.",
            )
        required_kind = REQUIRED_EVIDENCE_KIND.get(target)
        if not required_kind or evidence.kind != required_kind or not evidence.digest:
            return TransitionResult(
                False,
                current,
                target,
                "required evidence is missing or malformed",
                f"Provide {required_kind} evidence with a digest.",
            )
        if evidence.stale or evidence.contradictory or evidence.remote_consistent is False:
            return TransitionResult(
                False,
                current,
                target,
                "evidence is stale, contradictory, or locally/remotely inconsistent",
                "Reconcile the evidence and retry the transition.",
            )
        return TransitionResult(
            True,
            target,
            target,
            "transition accepted",
            event_id=transition_event_id(work_item.work_item_id, transition, evidence),
        )

    def recover(
        self,
        work_item: WorkItem,
        *,
        interrupted: bool = False,
        provider_status: str = "consistent",
        base_status: str = "current",
    ) -> dict[str, Any]:
        if work_item.state not in LIFECYCLE_STATES:
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
            "state": work_item.state,
            "recoverable": work_item.state not in {"closed", "cancelled"},
            "reason": "no recovery action required",
        }
