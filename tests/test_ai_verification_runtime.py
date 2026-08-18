from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from ai_verification_runtime import (
    PROTECTED_GATE_CLASSES,
    VerificationNode,
    create_receipt,
    execute_verification_plan,
    plan_verification,
)

NOW = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)


def node(
    node_id: str = "project_test",
    *,
    gate_class: str = "project",
    reuse_class: str = "content-bound",
    binding_classes: tuple[str, ...] = (),
    reuse_allowed: bool = True,
    protected: bool = False,
    depends_on: tuple[str, ...] = (),
) -> VerificationNode:
    return VerificationNode(
        node_id=node_id,
        command=("make", node_id),
        gate_class=gate_class,
        required=True,
        scope=("src/a.py",),
        depends_on=depends_on,
        reuse_class=reuse_class,
        binding_classes=binding_classes,
        reuse_allowed=reuse_allowed,
        protected=protected,
    )


def inputs(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "scope": ["src/a.py"],
        "governance": {"profile": "standard"},
        "environment": {"python": "3.11"},
        "toolchain": {"ruff": "0.16.0"},
        "policy": {"version": 1},
        "stage": "task",
        "runner": "local",
        "content": {"src/a.py": "digest-a"},
        "diff": {"base": "base-a", "head": "head-a"},
    }
    value.update(overrides)
    return value


def receipt_for(check: VerificationNode, current: dict[str, object], **overrides: object):
    options: dict[str, object] = {
        "output_digest": "a" * 64,
        "created_at": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(hours=1),
    }
    options.update(overrides)
    return create_receipt(
        check,
        current,
        **options,
    )


def test_fresh_content_receipt_is_the_only_reusable_required_result():
    check = node()
    current = inputs()

    plan = plan_verification(
        (check,),
        current_inputs=current,
        receipts={"project_test": receipt_for(check, current)},
        now=NOW,
    )

    decision = plan.checks[0]
    assert decision.action == "skip_reused"
    assert decision.status == "skipped"
    assert decision.decision_state == "fresh"
    assert decision.reason_code == "evidence_reuse_fresh"
    assert decision.satisfied_by == "reused_receipt"
    assert plan.metrics["nodesPlanned"] == 1
    assert plan.metrics["nodesExecuted"] == 0
    assert plan.metrics["nodesSkippedReused"] == 1


def test_stale_diff_and_unknown_receipts_execute_again():
    check = node(reuse_class="diff-bound")
    current = inputs()
    previous = inputs(diff={"base": "base-before", "head": "head-before"})
    stale = receipt_for(check, previous)

    stale_plan = plan_verification(
        (check,), current_inputs=current, receipts={check.node_id: stale}, now=NOW
    )
    assert stale_plan.checks[0].action == "execute"
    assert stale_plan.checks[0].decision_state == "stale"
    assert stale_plan.metrics["rerunStale"] == 1

    unknown_plan = plan_verification((check,), current_inputs=current, receipts={}, now=NOW)
    assert unknown_plan.checks[0].action == "execute"
    assert unknown_plan.checks[0].decision_state == "unknown"
    assert unknown_plan.metrics["rerunUnknown"] == 1


def test_multi_binding_tests_node_reruns_on_any_binding_change_and_skips_when_all_match():
    check = node(
        "tests",
        binding_classes=("diff-bound", "environment-bound"),
    )
    current = inputs()
    receipt = receipt_for(check, current)

    assert set(receipt["binding"]) == {
        "contentDigest",
        "diffDigest",
        "environmentDigest",
    }

    for changed in (
        inputs(content={"src/a.py": "digest-b"}),
        inputs(diff={"base": "base-b", "head": "head-a"}),
        inputs(environment={"python": "3.12"}),
    ):
        plan = plan_verification(
            (check,),
            current_inputs=changed,
            receipts={check.node_id: receipt},
            now=NOW,
        )
        assert plan.checks[0].action == "execute"
        assert plan.checks[0].decision_state == "stale"

    fresh_plan = plan_verification(
        (check,),
        current_inputs=current,
        receipts={check.node_id: receipt},
        now=NOW,
    )
    assert fresh_plan.checks[0].action == "skip_reused"
    assert fresh_plan.checks[0].decision_state == "fresh"

    protected = node(
        "tests_protected",
        gate_class="security",
        binding_classes=("diff-bound", "environment-bound"),
        protected=True,
    )
    protected_receipt = receipt_for(protected, current)
    protected_plan = plan_verification(
        (protected,),
        current_inputs=current,
        receipts={protected.node_id: protected_receipt},
        now=NOW,
    )
    assert protected_plan.checks[0].action == "execute"
    assert protected_plan.metrics["protectedNodesSkipped"] == 0


def test_unrelated_documentation_change_reuses_content_bound_check_only():
    reusable = node("content_test")
    protected = node("scope_test", gate_class="scope", reuse_allowed=False, protected=True)
    before = inputs()
    after = inputs(diff={"base": "base-a", "head": "head-b", "changedPaths": ["docs/b.md"]})

    plan = plan_verification(
        (reusable, protected),
        current_inputs=after,
        receipts={reusable.node_id: receipt_for(reusable, before)},
        now=NOW,
    )

    assert plan.checks[0].action == "skip_reused"
    assert plan.checks[1].action == "execute"
    assert plan.metrics["nodesSkippedReused"] == 1
    assert plan.metrics["protectedNodesExecuted"] == 1


def test_protected_gate_never_reuses_even_with_fresh_receipt():
    check = node(gate_class="security", protected=True)
    assert check.gate_class in PROTECTED_GATE_CLASSES
    current = inputs()

    plan = plan_verification(
        (check,),
        current_inputs=current,
        receipts={check.node_id: receipt_for(check, current)},
        now=NOW,
    )

    decision = plan.checks[0]
    assert decision.action == "execute"
    assert decision.reason_code == "protected_gate_execution_required"
    assert plan.metrics["protectedNodesExecuted"] == 1
    assert plan.metrics["protectedNodesSkipped"] == 0


def test_invalid_receipt_and_dependency_rerun_fail_closed():
    upstream = node("content_test")
    downstream = node("aggregate_test", depends_on=(upstream.node_id,))
    current = inputs()
    invalid = receipt_for(upstream, current, result="failed")

    plan = plan_verification(
        (upstream, downstream),
        current_inputs=current,
        receipts={upstream.node_id: invalid, downstream.node_id: receipt_for(downstream, current)},
        now=NOW,
    )

    assert plan.checks[0].action == "execute"
    assert plan.checks[0].decision_state == "unknown"
    assert plan.checks[1].action == "execute"
    assert plan.checks[1].reason_code == "dependency_rerun_required"


def test_expired_receipt_is_stale_and_binding_mismatch_is_unknown():
    check = node()
    current = inputs()
    expired = receipt_for(check, current, expires_at=NOW - timedelta(seconds=1))
    expired_plan = plan_verification(
        (check,), current_inputs=current, receipts={check.node_id: expired}, now=NOW
    )
    assert expired_plan.checks[0].decision_state == "stale"
    assert expired_plan.checks[0].reason_code == "evidence_expired"

    stage_mismatch = receipt_for(check, current)
    stage_plan = plan_verification(
        (check,),
        current_inputs=inputs(stage="pr"),
        receipts={check.node_id: stage_mismatch},
        now=NOW,
    )
    assert stage_plan.checks[0].decision_state == "stale"
    assert stage_plan.checks[0].reason_code == "evidence_execution_context_mismatch"

    malformed = receipt_for(check, current)
    malformed.pop("policyDigest")
    malformed_plan = plan_verification(
        (check,), current_inputs=current, receipts={check.node_id: malformed}, now=NOW
    )
    assert malformed_plan.checks[0].decision_state == "unknown"
    assert malformed_plan.checks[0].reason_code == "evidence_receipt_invalid"


def test_execution_adapter_counts_reused_and_executed_nodes():
    reusable = node("reusable_test")
    protected = node("security_test", gate_class="security", protected=True)
    current = inputs()
    plan = plan_verification(
        (reusable, protected),
        current_inputs=current,
        receipts={reusable.node_id: receipt_for(reusable, current)},
        now=NOW,
    )

    executed: list[str] = []

    def executor(decision):
        executed.append(decision.node_id)
        return {"status": "passed", "outputDigest": "b" * 64}

    result = execute_verification_plan(plan, executor=executor)
    assert executed == [protected.node_id]
    assert result["passed"] is True
    assert result["metrics"]["nodesExecuted"] == 1
    assert result["metrics"]["nodesSkippedReused"] == 1
    assert result["metrics"]["protectedNodesSkipped"] == 0


def test_cycles_and_missing_dependencies_fail_closed():
    with pytest.raises(ValueError, match="missing dependency"):
        plan_verification(
            (node("a", depends_on=("missing",)),),
            current_inputs=inputs(),
            receipts={},
            now=NOW,
        )

    with pytest.raises(ValueError, match="cycle"):
        plan_verification(
            (node("a", depends_on=("b",)), node("b", depends_on=("a",))),
            current_inputs=inputs(),
            receipts={},
            now=NOW,
        )
