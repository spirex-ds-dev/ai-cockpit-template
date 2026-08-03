from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

import pytest

from scripts.ai_work_item_intelligence import (
    IntelligenceError,
    append_fact,
    measure_query_baseline,
    query,
    read_snapshot,
    rebuild,
)


def test_facts_derive_state_and_block_agent_terminal_claim(tmp_path: Path) -> None:
    append_fact("example-item", "preflight_ready", {}, root=tmp_path)
    append_fact("example-item", "implementation_started", {}, root=tmp_path)
    assert read_snapshot("example-item", root=tmp_path)["status"]["governanceState"] == "active"
    append_fact("example-item", "claim", {"claim": "completed"}, root=tmp_path)
    snapshot = read_snapshot("example-item", root=tmp_path)
    assert snapshot["status"]["governanceState"] == "blocked"
    assert snapshot["missingEvidence"][0]["code"] == "required_evidence_missing"


def test_query_is_read_only_and_supports_filters_and_delta(tmp_path: Path) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    for work_item in ("alpha-item", "beta-item"):
        (active / f"{work_item}.contract.json").write_text("{}", encoding="utf-8")
    append_fact("alpha-item", "preflight_ready", {}, root=tmp_path)
    append_fact("beta-item", "human_decision_requested", {}, root=tmp_path)
    before = (tmp_path / ".ai/work-items/runtime/alpha-item/status.json").read_bytes()
    result = query(state="ready", root=tmp_path)
    assert [row["identity"]["workItemId"] for row in result["entries"]] == ["alpha-item"]
    assert (
        query(pending_human_decisions=True, root=tmp_path)["entries"][0]["identity"]["workItemId"]
        == "beta-item"
    )
    assert (tmp_path / ".ai/work-items/runtime/alpha-item/status.json").read_bytes() == before
    assert query(after_index_version=result["indexVersion"], root=tmp_path)["entries"] == []


def test_active_listing_excludes_orphaned_runtime_facts(tmp_path: Path) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    (active / "active-item.contract.json").write_text("{}", encoding="utf-8")
    append_fact("active-item", "preflight_ready", {}, root=tmp_path)
    append_fact("archived-item", "preflight_ready", {}, root=tmp_path)
    assert [item["identity"]["workItemId"] for item in query(root=tmp_path)["entries"]] == [
        "active-item"
    ]


def test_tamper_is_detected_and_rebuild_is_deterministic(tmp_path: Path) -> None:
    append_fact("tamper-item", "preflight_ready", {}, root=tmp_path)
    path = tmp_path / ".ai/work-items/runtime/tamper-item/status.json"
    value = json.loads(path.read_text())
    value["status"]["governanceState"] = "closed"
    path.write_text(json.dumps(value))
    with pytest.raises(IntelligenceError, match="digest mismatch"):
        read_snapshot("tamper-item", root=tmp_path)
    assert rebuild("tamper-item", root=tmp_path)["status"]["governanceState"] == "ready"


def test_index_tampering_is_detected_rebuilt_and_measured(tmp_path: Path) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    (active / "index-item.contract.json").write_text("{}", encoding="utf-8")
    append_fact("index-item", "preflight_ready", {}, root=tmp_path)
    index = tmp_path / ".ai/work-items/runtime/index.json"
    value = json.loads(index.read_text(encoding="utf-8"))
    value["entries"][0]["governanceState"] = "closed"
    index.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(IntelligenceError, match="index digest mismatch"):
        query(root=tmp_path)
    rebuild("index-item", root=tmp_path)
    baseline = measure_query_baseline(root=tmp_path, rounds=3)
    assert baseline["rounds"] == 3
    assert baseline["listActiveQueryMs"]["p95"] >= 0


def test_secret_like_payload_and_cross_item_leakage_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(IntelligenceError, match="secret-like"):
        append_fact("safe-item", "note", {"token": "no"}, root=tmp_path)
    append_fact("left-item", "preflight_ready", {}, root=tmp_path)
    append_fact("right-item", "implementation_started", {}, root=tmp_path)
    assert read_snapshot("left-item", root=tmp_path)["factSequence"] == 1
    assert read_snapshot("right-item", root=tmp_path)["factSequence"] == 1


def test_dependencies_decisions_and_activity_remain_independent(tmp_path: Path) -> None:
    append_fact("state-item", "dependency_missing", {"workItemId": "upstream"}, root=tmp_path)
    waiting = read_snapshot("state-item", root=tmp_path)
    assert waiting["status"]["governanceState"] == "waiting_for_dependency"
    assert waiting["dependencies"] == [{"workItemId": "upstream"}]
    append_fact(
        "decision-item", "human_decision_requested", {"decisionId": "approve"}, root=tmp_path
    )
    pending = read_snapshot("decision-item", root=tmp_path)
    assert pending["status"]["governanceState"] == "needs_human_confirmation"
    assert pending["actionEligibility"]["request_human_decision"]["eligible"] is True
    activity = tmp_path / ".ai/work-items/runtime/decision-item/activity.json"
    activity.write_text('{"health":"stale"}', encoding="utf-8")
    stale = rebuild("decision-item", root=tmp_path)
    assert stale["status"]["activityHealth"] == "stale"
    assert stale["status"]["governanceState"] == "needs_human_confirmation"


def test_concurrent_fact_writers_preserve_every_sequence_and_index_entry(tmp_path: Path) -> None:
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [
            pool.submit(
                append_fact, "parallel-item", "observation", {"number": number}, root=tmp_path
            )
            for number in range(12)
        ]
        for future in futures:
            future.result()
    snapshot = read_snapshot("parallel-item", root=tmp_path)
    assert snapshot["factSequence"] == 12
    facts = (tmp_path / ".ai/work-items/runtime/parallel-item/facts.jsonl").read_text().splitlines()
    assert [json.loads(row)["sequence"] for row in facts] == list(range(1, 13))


def test_v2_rebuild_preserves_versions_for_unchanged_source_bound_projection(
    tmp_path: Path,
) -> None:
    receipt = tmp_path / "preflight.json"
    receipt.write_text('{"status":"ready"}', encoding="utf-8")
    append_fact(
        "version-item",
        "preflight_ready",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": str(receipt),
                "digest": "sha256:" + sha256(receipt.read_bytes()).hexdigest(),
            },
        },
        root=tmp_path,
    )
    before = read_snapshot("version-item", schema_version=2, root=tmp_path)["versions"]
    rebuild("version-item", root=tmp_path)
    after = read_snapshot("version-item", schema_version=2, root=tmp_path)["versions"]
    assert after == before
    assert after == {"governance": 1, "sourceSequence": 1, "runtimeObservation": 0}


def test_v2_versions_split_governance_and_runtime_observations(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"ready":true}', encoding="utf-8")
    source_ref = {
        "kind": "test_receipt",
        "path": str(evidence),
        "digest": "sha256:" + sha256(evidence.read_bytes()).hexdigest(),
    }
    append_fact(
        "version-item",
        "preflight_ready",
        {"subject": {"kind": "preflight", "id": "current"}, "sourceRef": source_ref},
        root=tmp_path,
    )
    append_fact(
        "version-item",
        "observation",
        {"subject": {"kind": "runtime", "id": "worker"}, "health": "active"},
        root=tmp_path,
    )
    snapshot = read_snapshot("version-item", schema_version=2, root=tmp_path)
    assert snapshot["versions"] == {"governance": 1, "sourceSequence": 1, "runtimeObservation": 1}
    assert snapshot["status"]["governanceState"] == "ready"


def test_v2_runtime_observation_source_never_invalidates_governance(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"ready":true}', encoding="utf-8")
    append_fact(
        "runtime-item",
        "preflight_ready",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": str(evidence),
                "digest": "sha256:" + sha256(evidence.read_bytes()).hexdigest(),
            },
        },
        root=tmp_path,
    )
    append_fact(
        "runtime-item",
        "observation",
        {
            "subject": {"kind": "runtime", "id": "worker"},
            "sourceRef": {
                "kind": "observation",
                "path": str(tmp_path / "missing"),
                "digest": "sha256:" + "0" * 64,
            },
        },
        root=tmp_path,
    )
    snapshot = read_snapshot("runtime-item", schema_version=2, root=tmp_path)
    assert snapshot["sourceValidation"]["valid"] is True
    assert snapshot["status"]["governanceState"] == "ready"


def test_v2_rejects_missing_or_digest_mismatched_authoritative_source(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    append_fact(
        "source-item",
        "preflight_ready",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": str(missing),
                "digest": "sha256:" + "0" * 64,
            },
        },
        root=tmp_path,
    )
    snapshot = read_snapshot("source-item", schema_version=2, root=tmp_path)
    assert snapshot["status"]["governanceState"] == "inconsistent"
    assert snapshot["sourceValidation"]["valid"] is False
