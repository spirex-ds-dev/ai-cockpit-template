from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

import pytest

import scripts.ai_work_item_intelligence as intelligence
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


def test_audit_rebuild_rejects_a_fact_with_a_mismatched_digest(tmp_path: Path) -> None:
    append_fact("digest-item", "preflight_ready", {}, root=tmp_path)
    facts = tmp_path / ".ai/work-items/runtime/digest-item/facts.jsonl"
    record = json.loads(facts.read_text(encoding="utf-8"))
    record["digest"] = "sha256:" + "0" * 64
    facts.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(IntelligenceError, match="fact digest mismatch"):
        rebuild("digest-item", root=tmp_path)


def test_expired_writer_lease_is_recovered_before_append(tmp_path: Path) -> None:
    lock = tmp_path / ".ai/work-items/runtime/recovery-item/status.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": 999_999_999, "leaseExpiresAt": time.time() - 1}), encoding="utf-8"
    )

    append_fact("recovery-item", "preflight_ready", {}, root=tmp_path)

    assert read_snapshot("recovery-item", root=tmp_path)["factSequence"] == 1
    assert not lock.exists()


def test_unexpired_writer_lease_is_not_removed(tmp_path: Path) -> None:
    lock = tmp_path / ".ai/work-items/runtime/live-item/status.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": os.getpid(), "leaseExpiresAt": time.time() + 60}), encoding="utf-8"
    )

    with pytest.raises(IntelligenceError, match="lock is unavailable"):
        append_fact("live-item", "preflight_ready", {}, root=tmp_path)

    assert lock.exists()


def test_malformed_writer_lease_is_preserved_and_fails_closed(tmp_path: Path) -> None:
    lock = tmp_path / ".ai/work-items/runtime/malformed-item/status.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("not-json", encoding="utf-8")

    with (
        pytest.raises(IntelligenceError, match="lock is unavailable"),
        intelligence._exclusive_lock(lock, timeout_seconds=0),
    ):
        pass

    assert lock.exists()


def test_expired_live_writer_lease_is_not_removed(tmp_path: Path) -> None:
    lock = tmp_path / ".ai/work-items/runtime/live-expired-item/status.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": os.getpid(), "leaseExpiresAt": time.time() - 1}), encoding="utf-8"
    )

    with pytest.raises(IntelligenceError, match="lock is unavailable"):
        append_fact("live-expired-item", "preflight_ready", {}, root=tmp_path)

    assert lock.exists()


def test_audit_rebuild_rejects_a_non_contiguous_fact_sequence(tmp_path: Path) -> None:
    append_fact("sequence-item", "preflight_ready", {}, root=tmp_path)
    facts = tmp_path / ".ai/work-items/runtime/sequence-item/facts.jsonl"
    record = json.loads(facts.read_text(encoding="utf-8"))
    record["sequence"] = 2
    record["digest"] = intelligence._digest(
        {key: value for key, value in record.items() if key != "digest"}
    )
    facts.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(IntelligenceError, match="non-contiguous fact sequence"):
        rebuild("sequence-item", root=tmp_path)


def test_append_reuses_reducer_metadata_without_reparsing_the_fact_log(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    append_fact("incremental-item", "preflight_ready", {}, root=tmp_path)
    original_read_facts = intelligence.read_facts

    def fail_if_log_is_read(*args: object, **kwargs: object) -> list[dict[str, object]]:
        raise AssertionError("ordinary append must use reducer metadata")

    monkeypatch.setattr(intelligence, "read_facts", fail_if_log_is_read)
    append_fact("incremental-item", "implementation_started", {}, root=tmp_path)

    monkeypatch.setattr(intelligence, "read_facts", original_read_facts)
    assert read_snapshot("incremental-item", root=tmp_path)["factSequence"] == 2


def test_index_tampering_is_detected_rebuilt_and_measured(tmp_path: Path) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    (active / "index-item.contract.json").write_text("{}", encoding="utf-8")
    append_fact("index-item", "preflight_ready", {}, root=tmp_path)
    index = tmp_path / ".ai/work-items/runtime/index.json"
    value = json.loads(index.read_text(encoding="utf-8"))
    value["entries"][0]["governanceState"] = "closed"
    index.write_text(json.dumps(value), encoding="utf-8")
    assert [item["identity"]["workItemId"] for item in query(root=tmp_path)["entries"]] == [
        "index-item"
    ]
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


def test_keyed_entities_resolve_only_their_matching_open_blocker(tmp_path: Path) -> None:
    append_fact(
        "reducer-item",
        "verification_failed",
        {"verificationId": "unit", "subject": {"kind": "verification", "id": "unit"}},
        root=tmp_path,
    )
    append_fact(
        "reducer-item",
        "verification_passed",
        {
            "verificationId": "unit",
            "resolves": "verification:unit",
            "subject": {"kind": "verification", "id": "unit"},
        },
        root=tmp_path,
    )
    append_fact(
        "reducer-item",
        "human_decision_requested",
        {"decisionId": "approve-a", "subject": {"kind": "decision", "id": "approve-a"}},
        root=tmp_path,
    )
    append_fact(
        "reducer-item",
        "human_decision_requested",
        {"decisionId": "approve-b", "subject": {"kind": "decision", "id": "approve-b"}},
        root=tmp_path,
    )
    append_fact(
        "reducer-item",
        "human_decision_recorded",
        {
            "decisionId": "approve-a",
            "resolves": "decision:approve-a",
            "subject": {"kind": "decision", "id": "approve-a"},
        },
        root=tmp_path,
    )
    snapshot = read_snapshot("reducer-item", schema_version=2, root=tmp_path)
    assert snapshot["status"]["governanceState"] == "needs_human_confirmation"
    assert snapshot["openEntities"] == [{"kind": "decision", "id": "approve-b"}]


def test_keyed_dependency_resolution_and_closed_require_no_open_entities(tmp_path: Path) -> None:
    append_fact(
        "closed-item",
        "dependency_missing",
        {"workItemId": "upstream", "subject": {"kind": "dependency", "id": "upstream"}},
        root=tmp_path,
    )
    append_fact("closed-item", "closed", {}, root=tmp_path)
    assert (
        read_snapshot("closed-item", schema_version=2, root=tmp_path)["status"]["governanceState"]
        == "waiting_for_dependency"
    )
    append_fact(
        "closed-item",
        "dependency_satisfied",
        {
            "workItemId": "upstream",
            "resolves": "dependency:upstream",
            "subject": {"kind": "dependency", "id": "upstream"},
        },
        root=tmp_path,
    )
    assert (
        read_snapshot("closed-item", schema_version=2, root=tmp_path)["status"]["governanceState"]
        == "closed"
    )


def test_cross_subject_or_unknown_resolution_cannot_clear_a_blocker(tmp_path: Path) -> None:
    append_fact(
        "invalid-reducer-item",
        "human_decision_requested",
        {"decisionId": "approve", "subject": {"kind": "decision", "id": "approve"}},
        root=tmp_path,
    )
    append_fact(
        "invalid-reducer-item",
        "human_decision_recorded",
        {
            "decisionId": "approve",
            "resolves": "decision:missing",
            "subject": {"kind": "decision", "id": "approve"},
        },
        root=tmp_path,
    )
    snapshot = read_snapshot("invalid-reducer-item", schema_version=2, root=tmp_path)
    assert snapshot["status"]["governanceState"] == "inconsistent"
    assert snapshot["openEntities"] == [{"kind": "decision", "id": "approve"}]


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
                "path": receipt.name,
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
        "path": evidence.name,
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
                "path": evidence.name,
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
                "path": "missing",
                "digest": "sha256:" + "0" * 64,
            },
        },
        root=tmp_path,
    )
    snapshot = read_snapshot("runtime-item", schema_version=2, root=tmp_path)
    assert snapshot["sourceValidation"]["valid"] is True
    assert snapshot["status"]["governanceState"] == "ready"


def test_v2_rejects_missing_or_digest_mismatched_authoritative_source(tmp_path: Path) -> None:
    append_fact(
        "source-item",
        "preflight_ready",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": "missing.json",
                "digest": "sha256:" + "0" * 64,
            },
        },
        root=tmp_path,
    )
    snapshot = read_snapshot("source-item", schema_version=2, root=tmp_path)
    assert snapshot["status"]["governanceState"] == "inconsistent"
    assert snapshot["sourceValidation"]["valid"] is False


def test_v2_rejects_an_absolute_source_ref_outside_the_repository_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.json"
    outside.write_text('{"external":true}', encoding="utf-8")
    append_fact(
        "absolute-source-item",
        "preflight_ready",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": str(outside),
                "digest": "sha256:" + sha256(outside.read_bytes()).hexdigest(),
            },
        },
        root=tmp_path,
    )

    validation = read_snapshot("absolute-source-item", schema_version=2, root=tmp_path)[
        "sourceValidation"
    ]

    assert validation == {
        "valid": False,
        "records": [
            {
                "factId": "absolute-source-item:1",
                "valid": False,
                "reason": "source_path_outside_repository",
            }
        ],
    }


def test_v2_rejects_parent_traversal_source_ref(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-traversal.json"
    outside.write_text('{"external":true}', encoding="utf-8")
    append_fact(
        "traversal-source-item",
        "preflight_ready",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": f"../{outside.name}",
                "digest": "sha256:" + sha256(outside.read_bytes()).hexdigest(),
            },
        },
        root=tmp_path,
    )

    record = read_snapshot("traversal-source-item", schema_version=2, root=tmp_path)[
        "sourceValidation"
    ]["records"][0]

    assert record == {
        "factId": "traversal-source-item:1",
        "valid": False,
        "reason": "source_path_outside_repository",
    }


def test_v2_rejects_source_ref_symlink_resolving_outside_the_repository_root(
    tmp_path: Path,
) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-symlink-target.json"
    outside.write_text('{"external":true}', encoding="utf-8")
    (tmp_path / "outside-link.json").symlink_to(outside)
    append_fact(
        "symlink-source-item",
        "preflight_ready",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": "outside-link.json",
                "digest": "sha256:" + sha256(outside.read_bytes()).hexdigest(),
            },
        },
        root=tmp_path,
    )

    record = read_snapshot("symlink-source-item", schema_version=2, root=tmp_path)[
        "sourceValidation"
    ]["records"][0]

    assert record == {
        "factId": "symlink-source-item:1",
        "valid": False,
        "reason": "source_path_outside_repository",
    }


def test_v2_accepts_source_ref_symlink_resolving_inside_the_repository_root(tmp_path: Path) -> None:
    source = tmp_path / "inside-target.json"
    source.write_text('{"local":true}', encoding="utf-8")
    (tmp_path / "inside-link.json").symlink_to(source)
    append_fact(
        "inside-symlink-source-item",
        "preflight_ready",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": "inside-link.json",
                "digest": "sha256:" + sha256(source.read_bytes()).hexdigest(),
            },
        },
        root=tmp_path,
    )

    assert (
        read_snapshot("inside-symlink-source-item", schema_version=2, root=tmp_path)[
            "sourceValidation"
        ]["valid"]
        is True
    )


def test_v2_separates_governance_runtime_completion_and_permissions(tmp_path: Path) -> None:
    append_fact("boundary-item", "preflight_ready", {}, root=tmp_path)
    append_fact("boundary-item", "implementation_started", {}, root=tmp_path)
    append_fact("boundary-item", "verification_passed", {}, root=tmp_path)
    append_fact("boundary-item", "finish_passed", {}, root=tmp_path)
    append_fact("boundary-item", "closed", {}, root=tmp_path)
    before = read_snapshot("boundary-item", schema_version=2, root=tmp_path)
    activity = tmp_path / ".ai/work-items/runtime/boundary-item/activity.json"
    activity.write_text('{"health":"stale"}', encoding="utf-8")
    after = rebuild("boundary-item", schema_version=2, root=tmp_path)
    assert after["governance"] == before["governance"]
    assert after["runtimeObservation"]["activityHealth"] == "stale"
    assert after["completion"] == {
        "implementation": {"state": "in_progress", "lastFactId": "boundary-item:2"},
        "verification": {
            "state": "completed",
            "lastPassedFactId": "boundary-item:3",
        },
        "review": {"state": "completed", "lastFactId": "boundary-item:4"},
        "integration": {"state": "not_started"},
        "closure": {"state": "completed", "lastFactId": "boundary-item:5"},
    }
    permissions = after["governancePermissions"]
    assert permissions["statusVersion"] == after["statusVersion"]
    assert permissions["basis"] == {
        "governanceState": "closed",
        "governanceVersion": after["governance"]["version"],
    }
    assert permissions["verification"] == {
        "allowed": False,
        "reasonCodes": ["governance_state_not_eligible"],
        "conditions": {"requiredGovernanceStates": ["active"]},
        "evidenceBasis": ["status.governanceState", "actionEligibility.run_verification"],
    }
    assert permissions["finish"]["allowed"] is False
    assert permissions["closure"]["reasonCodes"] == ["governance_state_not_eligible"]
    assert "retry" not in permissions
    assert "cancel" not in permissions


def test_v2_governance_permissions_explain_allowed_and_denied_phases(
    tmp_path: Path,
) -> None:
    append_fact("permission-item", "implementation_started", {}, root=tmp_path)

    permissions = read_snapshot("permission-item", schema_version=2, root=tmp_path)[
        "governancePermissions"
    ]

    assert permissions["implementation"] == {
        "allowed": True,
        "reasonCodes": [],
        "conditions": {"requiredGovernanceStates": ["ready", "active"]},
        "evidenceBasis": ["status.governanceState", "actionEligibility.continue"],
    }
    assert permissions["verification"] == {
        "allowed": True,
        "reasonCodes": [],
        "conditions": {"requiredGovernanceStates": ["active"]},
        "evidenceBasis": ["status.governanceState", "actionEligibility.run_verification"],
    }
    assert permissions["finish"]["allowed"] is False
    assert permissions["closure"]["allowed"] is False


def test_v2_completion_invalidates_a_historical_verification_pass(tmp_path: Path) -> None:
    append_fact("completion-item", "implementation_started", {}, root=tmp_path)
    append_fact("completion-item", "verification_passed", {}, root=tmp_path)
    append_fact("completion-item", "verification_failed", {}, root=tmp_path)

    completion = read_snapshot("completion-item", schema_version=2, root=tmp_path)["completion"]

    assert completion["verification"] == {
        "state": "invalidated",
        "lastPassedFactId": "completion-item:2",
        "invalidatedBy": "completion-item:3",
    }


def test_v2_completion_replaces_invalidated_verification_with_a_fresh_pass(tmp_path: Path) -> None:
    append_fact("reverified-item", "verification_passed", {}, root=tmp_path)
    append_fact("reverified-item", "verification_failed", {}, root=tmp_path)
    append_fact("reverified-item", "verification_passed", {}, root=tmp_path)

    completion = read_snapshot("reverified-item", schema_version=2, root=tmp_path)["completion"]

    assert completion["verification"] == {
        "state": "completed",
        "lastPassedFactId": "reverified-item:3",
    }


def test_distinct_work_items_publish_independent_entries_without_a_shared_index_lock(
    tmp_path: Path,
) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    for number in range(64):
        (active / f"publish-{number:02d}.contract.json").write_text("{}", encoding="utf-8")

    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [
            pool.submit(append_fact, f"publish-{number:02d}", "preflight_ready", {}, root=tmp_path)
            for number in range(64)
        ]
        for future in futures:
            future.result()

    result = query(schema_version=2, root=tmp_path)
    assert len(result["entries"]) == 64
    cursors = []
    for number in range(64):
        entry = json.loads(
            (tmp_path / f".ai/work-items/runtime/publish-{number:02d}/index-entry.json").read_text()
        )
        snapshot = read_snapshot(f"publish-{number:02d}", schema_version=2, root=tmp_path)
        assert entry["publicationId"] == snapshot["publicationId"]
        cursors.append(entry["cursor"])
    assert result["indexVersion"] == max(cursors)


def test_rebuild_recovers_a_malformed_cache_from_item_local_publications(tmp_path: Path) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    for item in ("cache-left", "cache-right"):
        (active / f"{item}.contract.json").write_text("{}", encoding="utf-8")
        append_fact(item, "preflight_ready", {}, root=tmp_path)

    cache = tmp_path / ".ai/work-items/runtime/index-cache.json"
    cache.write_text("not-json", encoding="utf-8")
    rebuild("cache-left", schema_version=2, root=tmp_path)

    rebuilt = json.loads(cache.read_text(encoding="utf-8"))
    assert [entry["workItemId"] for entry in rebuilt["entries"]] == ["cache-left", "cache-right"]
    assert [
        entry["identity"]["workItemId"]
        for entry in query(schema_version=2, root=tmp_path)["entries"]
    ] == [
        "cache-left",
        "cache-right",
    ]


def test_reader_returns_inconsistent_when_a_complete_snapshot_lacks_its_entry(
    tmp_path: Path,
) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    (active / "partial-item.contract.json").write_text("{}", encoding="utf-8")
    append_fact("partial-item", "preflight_ready", {}, root=tmp_path)
    (tmp_path / ".ai/work-items/runtime/partial-item/index-entry.json").unlink()

    with pytest.raises(IntelligenceError, match="publication is missing"):
        query(schema_version=2, root=tmp_path)


def test_reader_observes_explicit_inconsistency_during_entry_publication(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    (active / "inflight-item.contract.json").write_text("{}", encoding="utf-8")
    original_atomic_json = intelligence._atomic_json
    observed: list[str] = []

    def observe_after_status(path: Path, value: dict[str, object]) -> None:
        original_atomic_json(path, value)
        if path.name == "status.json":
            with pytest.raises(IntelligenceError, match="publication is missing"):
                query(schema_version=2, root=tmp_path)
            observed.append("inconsistent")

    monkeypatch.setattr(intelligence, "_atomic_json", observe_after_status)
    append_fact("inflight-item", "preflight_ready", {}, root=tmp_path)

    assert observed == ["inconsistent"]
    assert [item["identity"]["workItemId"] for item in query(root=tmp_path)["entries"]] == [
        "inflight-item"
    ]


def test_publication_cursor_advances_only_when_facts_change(tmp_path: Path) -> None:
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    (active / "cursor-item.contract.json").write_text("{}", encoding="utf-8")
    append_fact("cursor-item", "preflight_ready", {}, root=tmp_path)
    first = read_snapshot("cursor-item", schema_version=2, root=tmp_path)

    rebuilt = rebuild("cursor-item", schema_version=2, root=tmp_path)
    assert rebuilt["publicationId"] == first["publicationId"]
    assert rebuilt["publicationCursor"] == first["publicationCursor"]

    append_fact("cursor-item", "implementation_started", {}, root=tmp_path)
    advanced = read_snapshot("cursor-item", schema_version=2, root=tmp_path)
    assert advanced["publicationCursor"] > first["publicationCursor"]


def test_malformed_writer_lease_is_preserved_and_fails_closed(tmp_path: Path) -> None:
    lock = tmp_path / ".ai/work-items/runtime/malformed-item/status.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("not-json", encoding="utf-8")

    with (
        pytest.raises(IntelligenceError, match="lock is unavailable"),
        intelligence._exclusive_lock(lock, timeout_seconds=0),
    ):
        pass

    assert lock.exists()
