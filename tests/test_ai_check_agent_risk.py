import ai_check_agent_risk


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
                "requiredChecksPassed": len(gates),
            }
            for stage in ("before_edit", "before_finish")
        ],
    }
    assert (
        ai_check_agent_risk.validate_agent_risks(contract, summary, expected_contract_hash="hash")
        == []
    )
