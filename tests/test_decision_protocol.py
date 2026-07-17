import json

import ai_decision_protocol


def report() -> dict:
    return {
        "workItemId": "task",
        "contractHash": "a" * 16,
        "preflightHash": "b" * 16,
        "status": "needs_human_confirmation",
        "humanDecisionRequest": {
            "whatHappened": ["The request is ambiguous."],
            "whyItMatters": "Continuing would require an unverified interpretation.",
            "options": [
                {"id": "A", "label": "Clarify", "effect": "Record the intended scope."},
                {"id": "B", "label": "Cancel", "effect": "Make no changes."},
            ],
            "recommendedOption": "A",
            "recommendationReason": "Clarification is safest.",
            "question": "Which option should be recorded?",
            "resumeCondition": "A fresh ready Preflight is required.",
        },
        "signals": [
            {"name": "Intent", "evidence": ["intent is ambiguous"]},
        ],
    }


def test_request_id_is_stable():
    assert ai_decision_protocol.request_id(report()) == "HDR-aaaaaaaaaaaaaaaa-bbbbbbbb"


def test_request_is_persisted_and_schema_validated(tmp_path):
    path = ai_decision_protocol.persist_request(report(), tmp_path)
    assert path is not None
    loaded = ai_decision_protocol.load_request(path.stem.removesuffix(".request"), tmp_path)
    assert loaded["decisionId"] == "HDR-aaaaaaaaaaaaaaaa-bbbbbbbb"
    assert loaded["evidence"]


def test_evidence_requires_a_current_option(tmp_path):
    path = ai_decision_protocol.persist_request(report(), tmp_path)
    request = ai_decision_protocol.load_request(path.stem.removesuffix(".request"), tmp_path)
    try:
        ai_decision_protocol.record_evidence(
            request,
            selected_option="STALE",
            decision="stale",
            decided_by="user",
            rationale="invalid",
            root=tmp_path,
        )
    except ValueError as exc:
        assert "selected option" in str(exc)
    else:
        raise AssertionError("stale option was accepted")


def test_valid_evidence_is_persisted(tmp_path):
    path = ai_decision_protocol.persist_request(report(), tmp_path)
    request = ai_decision_protocol.load_request(path.stem.removesuffix(".request"), tmp_path)
    evidence_path = ai_decision_protocol.record_evidence(
        request,
        selected_option="A",
        decision="Clarify",
        decided_by="user",
        rationale="The intended scope must be explicit.",
        root=tmp_path,
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["decisionId"] == request["decisionId"]
    assert evidence["source"] == "human_confirmation"
