from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from ai_check_registry import CheckerRegistry, CheckResult
from ai_verification_runtime import create_receipt, plan_verification
from ai_verify import consume_runtime_plan, load_runtime_receipts, runtime_nodes


def test_ai_verify_exposes_required_runtime_nodes_and_protected_gates():
    nodes = runtime_nodes("pr", ["src/a.py", "docs/b.md"])

    assert [node.node_id for node in nodes] == ["scope", "tests", "trust"]
    assert nodes[0].protected is True
    assert nodes[0].reuse_allowed is False
    assert nodes[1].reuse_class == "content-bound"
    assert nodes[1].reuse_allowed is True
    assert nodes[2].gate_class == "security"


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
    assert [result.status for result in results] == ["passed", "passed"]
    assert execution["passed"] is True
    assert execution["metrics"]["nodesExecuted"] == 1
    assert execution["metrics"]["nodesSkippedReused"] == 1
    assert execution["metrics"]["protectedNodesExecuted"] == 1
    assert execution["metrics"]["protectedNodesSkipped"] == 0
