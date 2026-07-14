import ai_check_scenario_coverage


def test_required_verified_scenario_with_evidence_passes():
    contract = {"riskAssessment": {"level": "high", "riskTypes": ["security"]}}
    summary = {
        "scenarioCoverage": [
            {
                "scenario": "secret redaction",
                "required": True,
                "status": "verified",
                "evidence": ["pytest"],
            }
        ]
    }
    assert ai_check_scenario_coverage.detect(contract, summary) == []


def test_required_unverified_hard_risk_fails_without_ack():
    contract = {"riskAssessment": {"level": "high", "riskTypes": ["security"]}}
    summary = {
        "scenarioCoverage": [
            {
                "scenario": "installer boundary",
                "required": True,
                "status": "unverified",
                "evidence": ["planned"],
            }
        ]
    }
    findings = ai_check_scenario_coverage.detect(contract, summary)
    assert any(
        item.kind == "required_scenario_unverified" and item.severity == "error"
        for item in findings
    )


def test_missing_summary_is_reported():
    findings = ai_check_scenario_coverage.detect(
        {"riskAssessment": {"level": "high", "riskTypes": ["security"]}}, None
    )
    assert any(item.kind == "missing_summary" for item in findings)


def test_not_applicable_requires_reason():
    findings = ai_check_scenario_coverage.detect(
        {"riskAssessment": {"level": "high", "riskTypes": ["security"]}},
        {
            "scenarioCoverage": [
                {"scenario": "external auth", "required": True, "status": "not_applicable"}
            ]
        },
    )
    assert any(item.kind == "missing_reason" for item in findings)


def test_invalid_scenario_shape_is_reported():
    findings = ai_check_scenario_coverage.detect(
        {"riskAssessment": {"level": "high", "riskTypes": ["security"]}},
        {
            "scenarioCoverage": [
                {"scenario": "bad", "required": "yes", "status": "verified", "evidence": []}
            ]
        },
    )
    assert any(item.kind == "invalid_scenario_coverage" for item in findings)


def test_verified_scenario_without_evidence_fails_closed():
    findings = ai_check_scenario_coverage.detect(
        {"riskAssessment": {"level": "low", "riskTypes": []}},
        {"scenarioCoverage": [{"scenario": "x", "required": True, "status": "verified"}]},
    )
    assert any(item.kind == "missing_evidence" for item in findings)


def test_not_applicable_with_reason_is_accepted():
    assert (
        ai_check_scenario_coverage.detect(
            {"riskAssessment": {"level": "high", "riskTypes": ["security"]}},
            {
                "scenarioCoverage": [
                    {
                        "scenario": "auth",
                        "required": True,
                        "status": "not_applicable",
                        "evidence": [],
                        "reason": "out of scope",
                    }
                ]
            },
        )
        == []
    )


def test_unknown_status_is_rejected():
    findings = ai_check_scenario_coverage.detect(
        {"riskAssessment": {"level": "low", "riskTypes": []}},
        {
            "scenarioCoverage": [
                {"scenario": "x", "required": True, "status": "planned", "evidence": []}
            ]
        },
    )
    assert any(item.kind == "invalid_status" for item in findings)


def test_high_risk_without_required_scenarios_is_reported():
    findings = ai_check_scenario_coverage.detect(
        {"riskAssessment": {"level": "high", "riskTypes": ["security"]}},
        {"scenarioCoverage": [{"scenario": "optional", "required": False}]},
    )
    assert any(item.kind == "missing_required_scenarios" for item in findings)


def test_unverified_low_risk_scenario_is_warning():
    findings = ai_check_scenario_coverage.detect(
        {"riskAssessment": {"level": "low", "riskTypes": []}},
        {
            "scenarioCoverage": [
                {"scenario": "x", "required": True, "status": "unverified", "evidence": []}
            ]
        },
    )
    assert findings[0].severity == "warning"


def test_scenario_helper_defaults_and_acknowledgement():
    assert ai_check_scenario_coverage.scenario_items(None) == []
    assert ai_check_scenario_coverage.risk_level({}) == "unknown"
    assert ai_check_scenario_coverage.hard_risk({}) is False
    assert ai_check_scenario_coverage.hard_risk_types()
    summary = {
        "reviewReadiness": {"status": "ready_with_risks"},
        "residualRisks": [{"detail": "accepted"}],
        "followUps": ["verify later"],
    }
    assert ai_check_scenario_coverage.explicit_risk_ack(summary) is True
