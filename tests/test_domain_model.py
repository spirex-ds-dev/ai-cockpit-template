from __future__ import annotations

import pytest

from scripts.ai_domain_model import (
    CANONICAL_TRANSITIONS,
    LIFECYCLE_STATES,
    CapabilityClaim,
    Closure,
    Contract,
    Decision,
    DomainService,
    Evidence,
    Finding,
    HumanDecision,
    Receipt,
    Risk,
    Transition,
    WorkItem,
)


def evidence(kind: str = "preflight", **extra: object) -> Evidence:
    return Evidence(kind=kind, digest="sha256:evidence", **extra)


def test_domain_vocabulary_owns_all_core_governance_objects() -> None:
    assert "created" in LIFECYCLE_STATES
    assert CANONICAL_TRANSITIONS["created"] == "preflight_ready"
    assert WorkItem("wi").work_item_id == "wi"
    assert Contract("wi", 2).work_item_id == "wi"
    assert Receipt("EV-1", "sha256:receipt").event_id == "EV-1"
    assert Decision("review", "continue").outcome == "continue"
    assert Transition("created", "preflight_ready").target == "preflight_ready"
    assert Finding("checker", "reason").reason_code == "reason"
    assert Risk("medium", "compatibility").area == "compatibility"
    assert HumanDecision("reviewer", "approve").decision == "approve"
    assert CapabilityClaim("ai_governance", "supported").state == "supported"
    assert Closure("wi", "closed").state == "closed"


def test_domain_service_accepts_only_the_next_evidence_bound_transition() -> None:
    result = DomainService().transition(
        WorkItem("wi", "created"), "preflight_ready", evidence=evidence()
    )
    assert result.allowed is True
    assert result.state == "preflight_ready"
    assert result.event_id and result.event_id.startswith("EV-")


@pytest.mark.parametrize(
    "candidate",
    [
        Evidence(kind="preflight", digest=""),
        Evidence(kind="preflight", digest="sha256:evidence", stale=True),
        Evidence(kind="preflight", digest="sha256:evidence", contradictory=True),
        Evidence(kind="preflight", digest="sha256:evidence", remote_consistent=False),
    ],
)
def test_domain_service_fails_closed_for_malformed_or_untrusted_evidence(
    candidate: Evidence,
) -> None:
    result = DomainService().transition(
        WorkItem("wi", "created"), "preflight_ready", evidence=candidate
    )
    assert result.allowed is False
    assert result.resume_condition


def test_domain_service_rejects_noncanonical_transition_before_adapter_can_reinterpret_it() -> None:
    result = DomainService().transition(
        WorkItem("wi", "created"), "closed", evidence=evidence("closure")
    )
    assert result.allowed is False
    assert result.reason == "transition is not in the canonical order"
