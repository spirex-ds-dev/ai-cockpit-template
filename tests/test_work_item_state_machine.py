from __future__ import annotations

import json
import subprocess
import sys

import pytest

import scripts.ai_work_item_state as state_adapter
from scripts.ai_work_item_state import CANONICAL, STATES, event_id, recover, transition


def evidence(kind: str = "preflight", **extra: object) -> dict[str, object]:
    return {"type": kind, "digest": "sha256:evidence", **extra}


def test_declared_states_and_canonical_order_are_complete():
    assert len(STATES) == 16
    assert CANONICAL["created"] == "preflight_ready"
    assert CANONICAL["close_authorized"] == "closed"


def test_valid_transition_requires_matching_evidence():
    result = transition("created", "preflight_ready", work_item="wi", evidence=evidence())
    assert result["allowed"] is True
    assert result["state"] == "preflight_ready"
    assert result["eventId"].startswith("EV-")


@pytest.mark.parametrize(
    "current,target", [("created", "closed"), ("archived", "closed"), ("merged", "pushed")]
)
def test_invalid_order_fails_closed(current: str, target: str):
    result = transition(current, target, evidence=evidence("closure", remoteConsistent=True))
    assert result["allowed"] is False
    assert result["resumeCondition"]


def test_missing_stale_contradictory_and_remote_evidence_fail_closed():
    for item in (
        {},
        evidence(stale=True),
        evidence(contradictory=True),
        evidence(remoteConsistent=False),
    ):
        assert transition("created", "preflight_ready", evidence=item)["allowed"] is False


def test_same_state_is_idempotent_and_event_is_stable():
    ev = evidence()
    first = transition("created", "created", work_item="wi", evidence=ev)
    second = transition("created", "created", work_item="wi", evidence=ev)
    assert first == second
    assert event_id("wi", "created", "created", ev) == first["eventId"]


def test_recovery_covers_interruption_and_consistency_failures():
    assert recover("archived", interrupted=True)["state"] == "paused"
    assert recover("archived", provider_status="partial")["state"] == "stale"
    assert recover("archived", base_status="stale")["recoverable"] is True
    assert recover("closed")["recoverable"] is False
    assert recover("not-a-state")["recoverable"] is False


def test_cli_is_deterministic_and_never_claims_invalid_transition():
    command = [
        sys.executable,
        "scripts/ai_work_item_state.py",
        "--state",
        "created",
        "--target",
        "closed",
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    assert payload["allowed"] is False
    assert "reason" in payload


def test_adapter_delegates_transition_decision_to_the_domain_service(
    monkeypatch: pytest.MonkeyPatch,
):
    class Result:
        def as_legacy_dict(self):
            return {"allowed": False, "state": "created", "target": "closed", "reason": "delegated"}

    class Domain:
        def __init__(self):
            self.call = None

        def transition(self, work_item, target, *, evidence):
            self.call = (work_item, target, evidence)
            return Result()

    domain = Domain()
    monkeypatch.setattr(state_adapter, "_DOMAIN", domain)
    assert state_adapter.transition("created", "closed", work_item="wi")["reason"] == "delegated"
    assert domain.call[0].work_item_id == "wi"
    assert domain.call[1] == "closed"
