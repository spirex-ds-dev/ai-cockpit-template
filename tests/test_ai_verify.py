from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from ai_check_registry import CheckerRegistry, CheckResult
from ai_generate_task_outcome import generate_outcome
from ai_verification_runtime import create_receipt, plan_verification
from ai_verify import (
    consume_runtime_plan,
    load_runtime_receipts,
    runtime_nodes,
    verify_stage,
)

NOW = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)


def runtime_inputs(*, diff=None, environment=None, stage="task"):
    return {
        "scope": ["src/a.py"],
        "governance": {"level": "standard", "stage": stage},
        "environment": environment or {"platform": "test", "release": "1"},
        "toolchain": {"python": "3.13"},
        "policy": {"level": "standard"},
        "stage": stage,
        "runner": "local",
        "content": {"src/a.py": "source"},
        "diff": diff
        or {
            "baseCommit": "a" * 40,
            "headCommit": "b" * 40,
            "changedPaths": ["src/a.py"],
        },
    }


def passed_registry(called: list[str], *checker_ids: str) -> CheckerRegistry:
    registry = CheckerRegistry()
    for checker_id in checker_ids:
        registry.register(
            checker_id,
            lambda checker_id=checker_id: (
                called.append(checker_id) or CheckResult.passed(checker_id)
            ),
        )
    return registry


def test_ai_verify_exposes_required_runtime_nodes_and_protected_gates():
    nodes = runtime_nodes("pr", ["src/a.py", "docs/b.md"])

    assert [node.node_id for node in nodes] == ["scope", "tests", "trust"]
    assert nodes[0].protected is True
    assert nodes[0].reuse_allowed is False
    assert nodes[1].reuse_class == "content-bound"
    assert nodes[1].reuse_allowed is True
    assert nodes[1].binding_classes == ("diff-bound", "environment-bound")
    assert nodes[2].gate_class == "security"


@pytest.mark.parametrize(
    ("stage", "expected_ids"),
    (
        ("task", ("scope", "tests")),
        ("pr", ("scope", "tests", "trust")),
        ("release", ("scope", "tests", "trust", "identity", "supply_chain")),
    ),
)
def test_ai_verify_keeps_existing_verify_stage_registry_mapping(stage, expected_ids):
    registry = passed_registry([], *expected_ids)

    results = verify_stage(object(), stage, registry)

    assert tuple(result.checker_id for result in results) == expected_ids
    assert all(result.status == "passed" for result in results)


def test_ai_verify_changed_diff_executes_the_mapped_concrete_tests_checker():
    nodes = {node.node_id: node for node in runtime_nodes("task", ["src/a.py"])}
    before = runtime_inputs()
    after = runtime_inputs(
        diff={
            "baseCommit": "a" * 40,
            "headCommit": "c" * 40,
            "changedPaths": ["src/a.py"],
        }
    )
    receipt = create_receipt(
        nodes["tests"],
        before,
        output_digest="a" * 64,
        created_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
    )
    assert set(receipt["binding"]) >= {
        "contentDigest",
        "diffDigest",
        "environmentDigest",
    }
    plan = plan_verification(
        (nodes["tests"],),
        current_inputs=after,
        receipts={"tests": receipt},
        now=NOW,
    )
    called: list[str] = []
    registry = passed_registry(called, "tests")

    results, execution = consume_runtime_plan(plan, registry)

    assert called == ["tests"]
    assert execution["results"][0]["action"] == "execute"
    assert execution["results"][0]["decision_state"] == "stale"
    assert results[0].checker_id == "tests"
    assert results[0].status == "passed"


def test_ai_verify_changed_environment_executes_the_mapped_concrete_tests_checker():
    nodes = {node.node_id: node for node in runtime_nodes("task", ["src/a.py"])}
    before = runtime_inputs()
    after = runtime_inputs(environment={"platform": "changed", "release": "1"})
    receipt = create_receipt(
        nodes["tests"],
        before,
        output_digest="b" * 64,
        created_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
    )
    plan = plan_verification(
        (nodes["tests"],),
        current_inputs=after,
        receipts={"tests": receipt},
        now=NOW,
    )
    called: list[str] = []
    registry = passed_registry(called, "tests")

    results, execution = consume_runtime_plan(plan, registry)

    assert called == ["tests"]
    assert execution["results"][0]["action"] == "execute"
    assert execution["results"][0]["decision_state"] == "stale"
    assert results[0].checker_id == "tests"
    assert results[0].status == "passed"


def test_ai_verify_unchanged_diff_receipt_reuses_the_mapped_checker():
    nodes = {node.node_id: node for node in runtime_nodes("task", ["src/a.py"])}
    current = runtime_inputs()
    receipt = create_receipt(
        nodes["tests"],
        current,
        output_digest="c" * 64,
        created_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
    )
    plan = plan_verification(
        (nodes["tests"],),
        current_inputs=current,
        receipts={"tests": receipt},
        now=NOW,
    )
    called: list[str] = []
    registry = passed_registry(called, "tests")

    results, execution = consume_runtime_plan(plan, registry)

    assert called == []
    assert execution["results"][0]["action"] == "skip_reused"
    assert execution["results"][0]["decision_state"] == "fresh"
    assert results[0].checker_id == "tests"
    assert results[0].status == "passed"


def test_ai_verify_release_protected_checkers_execute_even_with_reusable_receipts():
    nodes = {node.node_id: node for node in runtime_nodes("release", ["src/a.py"])}
    protected_ids = ("scope", "trust", "identity", "supply_chain")
    assert all(nodes[checker_id].protected for checker_id in protected_ids)
    assert all(not nodes[checker_id].reuse_allowed for checker_id in protected_ids)

    called: list[str] = []
    registry = passed_registry(called, *protected_ids)
    current = runtime_inputs(stage="release")
    fresh_receipts = {
        checker_id: create_receipt(
            replace(nodes[checker_id], reuse_class="content-bound", reuse_allowed=True),
            current,
            output_digest="d" * 64,
            created_at=NOW - timedelta(minutes=1),
            expires_at=NOW + timedelta(hours=1),
        )
        for checker_id in protected_ids
    }
    plan = plan_verification(
        tuple(nodes[checker_id] for checker_id in protected_ids),
        current_inputs=current,
        receipts=fresh_receipts,
        now=NOW,
    )
    results, execution = consume_runtime_plan(plan, registry)

    assert called == list(protected_ids)
    assert all(item["action"] == "execute" for item in execution["results"])
    assert execution["metrics"]["protectedNodesSkipped"] == 0
    assert [result.checker_id for result in results] == list(protected_ids)


def test_reuse_mapping_completion_keeps_registry_limitation_as_residual_risk():
    outcome = generate_outcome(
        "verification-reuse-checker-bindings",
        {"locale": "en"},
        evidence={
            "locale": "en",
            "warnings": [],
            "handoffRisks": [
                {
                    "severity": "medium",
                    "title": "registry availability",
                    "detail": "The template CLI has no host-specific default registry.",
                    "state": "unresolved",
                    "evidence": [
                        {
                            "source": "docs/reference/verification-evidence-reuse-runtime.md",
                            "subject": "empty-default-registry CLI limitation",
                        }
                    ],
                }
            ],
        },
    )

    assert outcome["status"] == "completed"
    assert outcome["humanStatusColor"] == "green"
    assert outcome["sections"]["warnings"] == []
    assert outcome["sections"]["residualRisks"][0]["title"] == "registry availability"


def test_ai_verify_treats_missing_or_malformed_receipt_files_as_unknown(tmp_path):
    assert load_runtime_receipts(tmp_path / "missing.json") == {}
    malformed = tmp_path / "malformed.json"
    malformed.write_text(json.dumps({"receipts": ["not-a-map"]}), encoding="utf-8")
    assert load_runtime_receipts(malformed) == {}


def test_ai_verify_loads_only_a_mapping_of_receipts(tmp_path):
    receipt_file = tmp_path / "receipts.json"
    receipt_file.write_text(
        json.dumps({"receipts": {"tests": {"result": "passed"}, "bad": "ignore"}}),
        encoding="utf-8",
    )

    assert load_runtime_receipts(receipt_file) == {"tests": {"result": "passed"}}


def test_ai_verify_consumes_plan_and_does_not_call_reused_checker():
    now = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)
    nodes = runtime_nodes("task", ["src/a.py", "docs/b.md"])
    current = {
        "scope": ["src/a.py", "docs/b.md"],
        "governance": {"level": "standard", "stage": "task"},
        "environment": {"platform": "test", "release": "1"},
        "toolchain": {"python": "3.13"},
        "policy": {"level": "standard"},
        "stage": "task",
        "runner": "local",
        "content": {"src/a.py": "source", "docs/b.md": "docs"},
        "diff": {"changedPaths": ["src/a.py", "docs/b.md"]},
    }
    receipt = create_receipt(
        nodes[1],
        current,
        output_digest="a" * 64,
        created_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(hours=1),
    )
    plan = plan_verification(
        nodes,
        current_inputs=current,
        receipts={"tests": receipt},
        now=now,
    )
    registry = CheckerRegistry()
    executed: list[str] = []
    registry.register("scope", lambda: executed.append("scope") or CheckResult.passed("scope"))
    registry.register("tests", lambda: executed.append("tests") or CheckResult.passed("tests"))

    results, execution = consume_runtime_plan(plan, registry)

    assert executed == ["scope"]
    assert [result.status for result in results] == ["passed"] * 2
    assert execution["passed"] is True
    assert execution["metrics"]["nodesExecuted"] == 1
    assert execution["metrics"]["nodesSkippedReused"] == 1
    assert execution["metrics"]["protectedNodesExecuted"] == 1
    assert execution["metrics"]["protectedNodesSkipped"] == 0
