import ai_check_reference_impact
import ai_classify_operation_impact


def contract(action="modify", scope=None):
    return {
        "requestedOperation": {
            "target": "repository_governance",
            "action": action,
            "environment": "repository",
            "effect": "enforce",
            "authorityRequired": False,
        },
        "scope": scope or ["scripts/example.py"],
    }


def test_observed_delete_conflicts_with_declared_modify():
    report = ai_classify_operation_impact.derive_operation_impact(
        contract(), [("D", "scripts/example.py")]
    )

    assert report["observedActions"] == ["delete"]
    assert report["riskProperties"]["destructive"] is True
    assert report["declarationConflict"] is True
    assert report["decision"] == "block"


def test_public_api_or_configuration_change_requires_reference_evidence():
    report = ai_classify_operation_impact.derive_operation_impact(
        contract(), [("M", "src/public_api.py"), ("M", "config/settings.yaml")]
    )

    assert report["impactClasses"] == [
        "compatibility_affecting",
        "configuration_affecting",
    ]
    assert ai_classify_operation_impact.impact_requires_reference_record(report) is True


def test_documentation_only_change_is_not_applicable():
    report = ai_classify_operation_impact.derive_operation_impact(
        contract(), [("M", "docs/reference/guide.md")]
    )

    assert report["impactClasses"] == []
    assert report["decision"] == "not_applicable"
    assert ai_classify_operation_impact.impact_requires_reference_record(report) is False


def test_impact_bearing_targets_without_covered_records_stop_for_human_decision():
    report = ai_classify_operation_impact.derive_operation_impact(
        contract(), [("D", "openapi/sej-api-common/pom.xml")]
    )

    result = ai_check_reference_impact.coverage_decision(report, [])

    assert result["decision"] == "needs_human_confirmation"
    assert result["missingTargets"] == ["openapi/sej-api-common/pom.xml"]
    assert "resumeCondition" in result["humanDecisionRequest"]


def test_record_for_parent_target_covers_changed_child_path():
    report = ai_classify_operation_impact.derive_operation_impact(
        contract(), [("D", "openapi/sej-api-common/pom.xml")]
    )
    records = [{"target": {"path": "openapi/sej-api-common"}}]

    result = ai_check_reference_impact.coverage_decision(report, records)

    assert result["decision"] == "continue"


def test_no_impact_change_needs_no_record():
    report = ai_classify_operation_impact.derive_operation_impact(
        contract(), [("M", "docs/reference/guide.md")]
    )

    assert ai_check_reference_impact.coverage_decision(report, [])["decision"] == "not_applicable"


def test_report_keeps_authority_safety_and_scope_decisions_separate():
    report = ai_classify_operation_impact.derive_operation_impact(
        contract(), [("D", "openapi/sej-api-common/pom.xml")]
    )

    assert report["decisionStates"] == {
        "requestTrustDecision": "not_assessed",
        "authorityBindingDecision": "not_assessed",
        "safetyEvidenceDecision": "evidence_required",
        "scopeConsistencyDecision": "inconsistent",
        "effectiveDecision": "block",
    }
