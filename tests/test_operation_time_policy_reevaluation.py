import pytest
from ai_input_trust import (
    GovernanceDecision,
    OperationCategory,
    OperationTimeRequest,
    evaluate_operation_time_policy,
)


def operation_request(**overrides):
    values = {
        "requestedOperation": OperationCategory.EXECUTE_SCRIPT.value,
        "actualToolCall": OperationCategory.EXECUTE_SCRIPT.value,
        "targetResource": "scripts/cleanup.py",
        "declaredScope": ("scripts/cleanup.py",),
        "approvedOperation": OperationCategory.EXECUTE_SCRIPT.value,
        "approvedTargetResource": "scripts/cleanup.py",
        "approvedScope": ("scripts/cleanup.py",),
        "currentAuthority": "user",
        "evidenceFresh": True,
        "destructiveImpact": "high",
    }
    values.update(overrides)
    return OperationTimeRequest(**values)


def test_execution_of_a_dangerous_script_is_re_evaluated_after_creation():
    decision = evaluate_operation_time_policy(
        operation_request(
            requestedOperation="create_script",
            actualToolCall=OperationCategory.EXECUTE_SCRIPT.value,
        )
    )

    assert decision.decision == GovernanceDecision.BLOCK.value
    assert decision.reason == "actual tool call does not match the requested operation"
    assert decision.recoveryCondition == "create a new approval binding for the actual tool call"


def test_changed_target_invalidates_an_earlier_approval_binding():
    decision = evaluate_operation_time_policy(
        operation_request(targetResource="scripts/release.py")
    )

    assert decision.decision == GovernanceDecision.CONFIRM.value
    assert (
        decision.reason == "approval binding does not match the current operation target or scope"
    )
    assert decision.mayProceedAutomatically is False


def test_stale_evidence_requires_human_confirmation():
    decision = evaluate_operation_time_policy(operation_request(evidenceFresh=False))

    assert decision.decision == GovernanceDecision.CONFIRM.value
    assert decision.reason == "operation evidence is stale"


def test_non_authoritative_input_requires_human_confirmation():
    decision = evaluate_operation_time_policy(operation_request(inputTrust="untrusted_content"))

    assert decision.decision == GovernanceDecision.CONFIRM.value
    assert (
        decision.reason == "input trust is not authoritative for the requested high-risk operation"
    )


def test_unknown_destructive_impact_stops_the_operation():
    decision = evaluate_operation_time_policy(operation_request(destructiveImpact="unclassified"))

    assert decision.decision == GovernanceDecision.BLOCK.value
    assert decision.reason == "destructive impact is not classified"


def test_mismatched_actual_tool_call_stops_with_recovery_guidance():
    decision = evaluate_operation_time_policy(
        operation_request(
            requestedOperation=OperationCategory.PUSH.value,
            actualToolCall=OperationCategory.MERGE.value,
        )
    )

    assert decision.decision == GovernanceDecision.BLOCK.value
    assert decision.safeAlternative == "preserve the request and actual call for human review"


@pytest.mark.parametrize("operation", list(OperationCategory))
def test_each_required_high_risk_category_requires_a_current_authority_binding(operation):
    decision = evaluate_operation_time_policy(
        operation_request(
            requestedOperation=operation.value,
            actualToolCall=operation.value,
            approvedOperation="",
        )
    )

    assert decision.decision == GovernanceDecision.CONFIRM.value
    assert decision.reason == "current authority is missing for the requested high-risk operation"
