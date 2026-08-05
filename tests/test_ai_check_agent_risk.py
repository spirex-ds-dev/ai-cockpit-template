import json
import sys

import ai_check_agent_risk


def test_agent_risk_allows_finish_stabilization_dependencies(monkeypatch):
    monkeypatch.setenv("AI_FINISH_STABILIZING", "1")
    contract = {
        "verification": [
            {"check": "aiWorkItem", "required": True},
            {"check": "aiScope", "required": True},
            {"check": "aiAgentRisk", "required": True},
            {"check": "aiSummary", "required": True},
            {"check": "aiStatus", "required": True},
            {"check": "aiStatusCheck", "required": True},
        ],
        "unknowns": [],
        "notCodable": False,
        "executionDecision": {"status": "continue"},
        "agentCapability": {"canImplement": True, "needsHumanDecision": False},
    }
    summary = {
        "verification": [
            {"check": "aiWorkItem", "result": "passed"},
            {"check": "aiScope", "result": "passed"},
        ]
    }
    assert ai_check_agent_risk.validate_agent_risks(contract, summary) == []


def test_agent_risk_helpers_extract_required_commands_and_statuses():
    contract = {"verification": [{"check": "quality", "required": True}, "bad"]}
    summary = {"verification": [{"check": "quality", "result": "passed"}]}

    assert ai_check_agent_risk.command_prefixes(contract) == ["quality"]
    assert ai_check_agent_risk.has_required_gate(["quality"], "quality")
    assert ai_check_agent_risk.matching_required_commands(["quality", "quality"], "quality") == [
        "quality",
        "quality",
    ]
    assert ai_check_agent_risk.summary_status(summary) == {"quality": "passed"}
    assert ai_check_agent_risk.checkpoint_evidence({"checkpointEvidence": [{"stage": "x"}]})


def test_agent_risk_rejects_unknowns_in_code_mode():
    issues = ai_check_agent_risk.validate_agent_risks(
        {
            "mode": "code",
            "unknowns": ["open"],
            "notCodable": False,
            "executionDecision": {"status": "continue"},
            "agentCapability": {"canImplement": True},
            "verification": [],
        },
        None,
    )
    assert any("mode code cannot proceed" in issue for issue in issues)


def test_agent_risk_rejects_human_decision_conflict():
    issues = ai_check_agent_risk.validate_agent_risks(
        {
            "mode": "code",
            "unknowns": [],
            "notCodable": False,
            "executionDecision": {"status": "continue"},
            "agentCapability": {"needsHumanDecision": True},
            "verification": [],
        },
        None,
    )
    assert any("needsHumanDecision" in issue for issue in issues)


def test_agent_risk_accepts_complete_gates_and_checkpoints():
    gates = ["aiWorkItem", "aiScope", "aiAgentRisk", "aiSummary", "aiStatus", "aiStatusCheck"]
    contract = {
        "mode": "code",
        "unknowns": [],
        "notCodable": False,
        "executionDecision": {"status": "continue"},
        "agentCapability": {"canImplement": True, "needsHumanDecision": False},
        "verification": [{"check": gate, "required": True} for gate in gates],
        "acceptance": ["done"],
        "checkpointPolicy": {
            "requiredBeforeFinish": True,
            "requiredStages": ["before_edit", "before_finish"],
        },
    }
    summary = {
        "verification": [{"check": gate, "result": "passed"} for gate in gates],
        "checkpointEvidence": [
            {
                "stage": stage,
                "recorded": True,
                "contractHash": "hash",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": len(gates),
                "requiredChecksPassed": 0 if stage == "before_edit" else len(gates),
            }
            for stage in ("before_edit", "before_finish")
        ],
    }
    assert (
        ai_check_agent_risk.validate_agent_risks(contract, summary, expected_contract_hash="hash")
        == []
    )


def test_agent_risk_rejects_before_edit_checkpoint_recorded_after_verification_started():
    contract = {
        "verification": [{"check": "quality", "required": True}],
        "acceptance": ["concrete acceptance evidence"],
        "unknowns": [],
        "checkpointPolicy": {
            "requiredBeforeFinish": True,
            "requiredStages": ["before_edit"],
        },
    }
    summary = {
        "checkpointEvidence": [
            {
                "stage": "before_edit",
                "recorded": True,
                "contractHash": "hash",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": 1,
                "requiredChecksPassed": 1,
            }
        ]
    }

    issues = ai_check_agent_risk.validate_agent_risks(
        contract, summary, expected_contract_hash="hash"
    )

    assert "before_edit checkpoint must be recorded before required verification" in issues


def _amended_checkpoint_contract() -> dict:
    return {
        "verification": [{"check": "quality", "required": True}],
        "acceptance": ["Concrete amended acceptance evidence."],
        "unknowns": [],
        "checkpointPolicy": {
            "requiredBeforeFinish": True,
            "requiredStages": ["before_edit"],
        },
    }


def _original_before_edit() -> dict:
    return {
        "stage": "before_edit",
        "recorded": True,
        "contractHash": "original-contract-hash",
        "acceptanceCount": 1,
        "unknownCount": 0,
        "requiredChecks": 1,
        "requiredChecksPassed": 0,
    }


def _amendment_revalidation(*, verification_started: bool = False) -> dict:
    record = {
        "stage": "contract_amendment_revalidation",
        "recorded": True,
        "originalBeforeEditContractHash": "original-contract-hash",
        "previousContractHash": "original-contract-hash",
        "contractHash": "amended-contract-hash",
        "acceptanceCount": 1,
        "unknownCount": 0,
        "requiredChecks": 1,
        "requiredChecksPassed": 0,
        "reason": "Expand scope for the required regression.",
        "verificationStarted": verification_started,
    }
    if verification_started:
        record.update(
            {
                "invalidatedRequiredChecks": ["quality"],
                "requiredChecksPassedAtAmendment": 1,
            }
        )
    return record


def test_agent_risk_accepts_original_before_edit_with_valid_append_only_amendment():
    """Break caught: a valid amended Contract is rejected by the original checkpoint hash."""
    issues = ai_check_agent_risk.validate_checkpoint_bindings(
        _amended_checkpoint_contract(),
        {
            "checkpointEvidence": [
                _original_before_edit(),
                _amendment_revalidation(),
            ]
        },
        expected_contract_hash="amended-contract-hash",
    )

    assert issues == []


def test_agent_risk_rejects_missing_or_verification_started_amendment_revalidation():
    """Break caught: stale or post-verification Contract scope is accepted without stricter evidence."""
    missing = ai_check_agent_risk.validate_checkpoint_bindings(
        _amended_checkpoint_contract(),
        {"checkpointEvidence": [_original_before_edit()]},
        expected_contract_hash="amended-contract-hash",
    )
    malformed_started = _amendment_revalidation(verification_started=True)
    malformed_started["invalidatedRequiredChecks"] = []
    started = ai_check_agent_risk.validate_checkpoint_bindings(
        _amended_checkpoint_contract(),
        {
            "checkpointEvidence": [
                _original_before_edit(),
                malformed_started,
            ]
        },
        expected_contract_hash="amended-contract-hash",
    )

    assert "missing contract_amendment_revalidation for stale before_edit Contract" in missing
    assert "contract_amendment_revalidation cannot follow required verification" in started


def test_agent_risk_accepts_post_verification_amendment_only_when_all_gates_are_invalidated():
    """Break caught: a stale passed gate survives a post-verification scope amendment."""
    issues = ai_check_agent_risk.validate_checkpoint_bindings(
        _amended_checkpoint_contract(),
        {
            "checkpointEvidence": [
                _original_before_edit(),
                _amendment_revalidation(verification_started=True),
            ]
        },
        expected_contract_hash="amended-contract-hash",
    )

    assert issues == []


def test_agent_risk_accepts_a_digest_chained_second_amendment():
    """Break caught: a valid second amendment is compared directly with before_edit."""
    first = _amendment_revalidation()
    second = _amendment_revalidation()
    second["previousContractHash"] = "amended-contract-hash"
    second["contractHash"] = "second-amendment-hash"
    issues = ai_check_agent_risk.validate_checkpoint_bindings(
        _amended_checkpoint_contract(),
        {
            "checkpointEvidence": [
                _original_before_edit(),
                first,
                second,
            ]
        },
        expected_contract_hash="second-amendment-hash",
    )

    assert issues == []


def _resumed_gate_contract(recorded_at: str) -> dict:
    gates = ["aiWorkItem", "aiScope", "aiAgentRisk", "aiSummary", "aiStatus", "aiStatusCheck"]
    return {
        "mode": "code",
        "unknowns": [],
        "notCodable": False,
        "executionDecision": {"status": "continue"},
        "agentCapability": {"canImplement": True, "needsHumanDecision": False},
        "verification": [{"check": gate, "required": True} for gate in gates],
        "acceptance": ["Use current-generation verification."],
        "resumeHistory": [{"recordedAt": recorded_at}],
    }


def _checkpoint_record(required_checks: int, passed: int) -> dict:
    return {
        "stage": "before_edit",
        "recorded": True,
        "contractHash": "hash",
        "acceptanceCount": 1,
        "unknownCount": 0,
        "requiredChecks": required_checks,
        "requiredChecksPassed": passed,
    }


def test_agent_risk_rejects_pre_resume_passes_as_stale():
    contract = _resumed_gate_contract("2026-07-29T07:30:00+00:00")
    gates = [item["check"] for item in contract["verification"]]
    summary = {
        "verification": [
            {
                "check": gate,
                "result": "passed",
                "executedAt": "2026-07-29T07:00:00+00:00",
            }
            for gate in gates
        ],
        "checkpointEvidence": [_checkpoint_record(len(gates), 0)],
    }

    issues = ai_check_agent_risk.validate_agent_risks(
        contract, summary, expected_contract_hash="hash"
    )

    assert "required AI hard gate is not passed in Summary: aiWorkItem" in issues


def test_agent_risk_accepts_post_resume_gate_results():
    contract = _resumed_gate_contract("2026-07-29T07:30:00+00:00")
    gates = [item["check"] for item in contract["verification"]]
    summary = {
        "verification": [
            {
                "check": gate,
                "result": "passed",
                "executedAt": "2026-07-29T07:31:00+00:00",
            }
            for gate in gates
        ],
        "checkpointEvidence": [_checkpoint_record(len(gates), 0)],
    }

    assert (
        ai_check_agent_risk.validate_agent_risks(contract, summary, expected_contract_hash="hash")
        == []
    )


def test_agent_risk_fails_closed_for_invalid_latest_resume_timestamp():
    contract = _resumed_gate_contract("not-a-timestamp")
    gates = [item["check"] for item in contract["verification"]]
    summary = {
        "verification": [
            {
                "check": gate,
                "result": "passed",
                "executedAt": "2026-07-29T07:31:00+00:00",
            }
            for gate in gates
        ],
        "checkpointEvidence": [_checkpoint_record(len(gates), 0)],
    }

    issues = ai_check_agent_risk.validate_agent_risks(
        contract, summary, expected_contract_hash="hash"
    )

    assert "latest resumeHistory.recordedAt is invalid" in issues


def test_agent_risk_accepts_checkpoint_full_hash_when_expected_hash_is_short():
    contract = {
        "verification": [
            {"check": gate, "required": True}
            for gate in (
                "aiWorkItem",
                "aiScope",
                "aiAgentRisk",
                "aiSummary",
                "aiStatus",
                "aiStatusCheck",
            )
        ],
        "acceptance": ["done"],
        "unknowns": [],
        "checkpointPolicy": {"requiredBeforeFinish": True, "requiredStages": ["before_finish"]},
    }
    summary = {
        "verification": [
            {"check": gate, "result": "passed"}
            for gate in (
                "aiWorkItem",
                "aiScope",
                "aiAgentRisk",
                "aiSummary",
                "aiStatus",
                "aiStatusCheck",
            )
        ],
        "checkpointEvidence": [
            {
                "stage": "before_finish",
                "recorded": True,
                "contractHash": "0123456789abcdef0123456789abcdef",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": 6,
                "requiredChecksPassed": 6,
            }
        ],
    }
    assert (
        ai_check_agent_risk.validate_agent_risks(
            contract, summary, expected_contract_hash="0123456789abcdef"
        )
        == []
    )


def test_agent_risk_rejects_missing_gate_and_failed_required_gate():
    contract = {
        "verification": [
            {"check": "quality", "required": True},
            {"check": "aiWorkItem", "required": True},
            {"check": "aiAgentRisk", "required": True},
        ],
        "mode": "code",
        "unknowns": [],
        "notCodable": False,
        "executionDecision": {"status": "continue"},
        "agentCapability": {"needsHumanDecision": False},
    }
    issues = ai_check_agent_risk.validate_agent_risks(
        contract,
        {
            "verification": [
                {"check": "quality", "result": "failed"},
                {"check": "aiWorkItem", "result": "failed"},
            ]
        },
    )
    assert any("missing required AI hard gate" in issue for issue in issues)
    assert any(
        "required AI hard gate is not passed in Summary: aiWorkItem" in issue for issue in issues
    )


def test_agent_risk_rejects_invalid_checkpoint_evidence():
    contract = {
        "verification": [],
        "acceptance": ["done"],
        "unknowns": [],
        "checkpointPolicy": {
            "requiredBeforeFinish": True,
            "requiredStages": ["before_finish"],
        },
    }
    summary = {
        "checkpointEvidence": [
            {
                "stage": "before_finish",
                "recorded": True,
                "contractHash": "stale",
                "acceptanceCount": 0,
                "unknownCount": 1,
                "requiredChecks": 1,
                "requiredChecksPassed": 0,
            }
        ]
    }
    issues = ai_check_agent_risk.validate_agent_risks(
        contract, summary, expected_contract_hash="expected"
    )
    assert any("contractHash is stale" in issue for issue in issues)
    assert any("acceptanceCount is stale" in issue for issue in issues)
    assert any("unknownCount is stale" in issue for issue in issues)
    assert any("requiredChecks is stale" in issue for issue in issues)


def test_checkpoint_binding_validation_rejects_stale_contract_before_finish():
    contract = {
        "verification": [{"check": "quality", "required": True}],
        "acceptance": ["done"],
        "unknowns": [],
        "checkpointPolicy": {
            "requiredBeforeFinish": True,
            "requiredStages": ["before_edit", "before_finish"],
        },
    }
    summary = {
        "checkpointEvidence": [
            {
                "stage": "before_edit",
                "recorded": True,
                "contractHash": "old-contract",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": 2,
                "requiredChecksPassed": 0,
            },
            {
                "stage": "before_finish",
                "recorded": True,
                "contractHash": "new-contract",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": 1,
                "requiredChecksPassed": 0,
            },
        ]
    }

    issues = ai_check_agent_risk.validate_checkpoint_bindings(
        contract, summary, expected_contract_hash="new-contract"
    )

    assert issues == [
        "missing contract_amendment_revalidation for stale before_edit Contract",
        "checkpointEvidence[before_edit] contractHash is stale",
        "checkpointEvidence[before_edit].requiredChecks is stale",
    ]


def test_agent_risk_rejects_missing_checkpoint_and_invalid_counts():
    contract = {
        "verification": [{"check": "quality", "required": True}],
        "acceptance": ["done"],
        "unknowns": ["open"],
        "notCodable": True,
        "executionDecision": {"status": "continue"},
        "agentCapability": {"canImplement": True},
        "checkpointPolicy": {
            "requiredBeforeFinish": True,
            "requiredStages": ["before_edit", "before_finish"],
        },
    }
    summary = {
        "checkpointEvidence": [
            {
                "stage": "before_finish",
                "recorded": True,
                "contractHash": "hash",
                "acceptanceCount": "one",
                "unknownCount": 1,
                "requiredChecks": 1,
                "requiredChecksPassed": 1,
            }
        ]
    }
    issues = ai_check_agent_risk.validate_agent_risks(contract, summary)
    assert any("executionDecision.status" in issue for issue in issues)
    assert any("canImplement false" in issue for issue in issues)
    assert any("missing checkpointEvidence" in issue for issue in issues)
    assert any("acceptanceCount must be integer" in issue for issue in issues)


def test_agent_risk_accepts_non_coding_blocked_contract_without_capability():
    gates = ["aiWorkItem", "aiScope", "aiAgentRisk", "aiSummary", "aiStatus", "aiStatusCheck"]
    contract = {
        "mode": "investigate",
        "unknowns": ["open"],
        "notCodable": False,
        "executionDecision": {"status": "defer"},
        "agentCapability": {},
        "verification": [{"check": gate, "required": True} for gate in gates],
    }
    summary = {"verification": [{"check": gate, "result": "passed"} for gate in gates]}
    assert ai_check_agent_risk.validate_agent_risks(contract, summary) == []


def test_agent_risk_main_handles_skip_and_success(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ai_check_agent_risk"])
    assert ai_check_agent_risk.main() == 0

    gates = ["aiWorkItem", "aiScope", "aiAgentRisk", "aiSummary", "aiStatus", "aiStatusCheck"]
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(
        json.dumps(
            {
                "workItemId": "coverage",
                "verification": [{"check": gate, "required": True} for gate in gates],
            }
        ),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps({"verification": [{"check": gate, "result": "passed"} for gate in gates]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_check_agent_risk", "--contract", str(contract_path), "--summary", str(summary_path)],
    )
    assert ai_check_agent_risk.main() == 0
