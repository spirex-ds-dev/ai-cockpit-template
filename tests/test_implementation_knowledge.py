"""TDD contract tests for the evidence-bound Implementation Knowledge projection."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import ai_archive_work_item
import ai_generate_knowledge_record
import pytest
from ai_check_knowledge_index import check_index, check_record
from ai_generate_knowledge_record import (
    build_dependency_index,
    build_record,
    rebuild_existing_projections,
    rebuild_index,
)

ROOT = Path(__file__).resolve().parents[1]
RECORD_SCHEMA = ROOT / ".ai/schemas/implementation-knowledge-record.schema.json"
INDEX_SCHEMA = ROOT / ".ai/schemas/implementation-knowledge-index.schema.json"
DEPENDENCY_INDEX_SCHEMA = ROOT / ".ai/schemas/implementation-knowledge-dependency-index.schema.json"


def approach() -> dict:
    return {
        "approachType": "implementation",
        "status": "complete",
        "summary": {
            "text": "在服务入口验证状态后决定是否继续处理。",
            "status": "verified",
            "evidence": [{"source": "src/order_service.py", "subject": "入口状态验证"}],
        },
        "mechanism": {
            "text": "不满足条件时提前终止，正常路径保持原有流程。",
            "status": "verified",
            "evidence": [{"source": "src/order_service.py", "subject": "提前终止"}],
        },
        "affectedComponents": [
            {
                "component": "OrderService",
                "detail": "业务服务入口",
                "status": "verified",
                "evidence": [{"source": "src/order_service.py", "subject": "服务入口"}],
            }
        ],
        "designDecisions": [
            {
                "decision": "不修改数据库结构",
                "reason": "现有状态字段已能表达控制条件。",
                "status": "verified",
                "evidence": [{"source": "src/order_service.py", "subject": "复用现有状态"}],
            }
        ],
        "technicalDetails": [],
        "evidence": [
            {
                "claim": "入口状态验证存在。",
                "source": "src/order_service.py",
                "subject": "implementation",
                "status": "verified",
            }
        ],
    }


def write_fixture(
    tmp_path: Path,
    *,
    work_item_id: str = "order-cancel-validation",
    include_approach: bool = True,
) -> tuple[Path, Path, Path]:
    (tmp_path / "src").mkdir()
    (tmp_path / "src/order_service.py").write_text(
        "def validate(order):\n    return order.status\n", encoding="utf-8"
    )
    contract = {
        "contractVersion": 2,
        "workItemId": work_item_id,
        "title": "Prevent updates after cancellation",
        "mode": "code",
    }
    summary = {
        "summaryVersion": 2,
        "workItemId": work_item_id,
        "changedFiles": [{"path": "src/order_service.py"}],
        "implementationApproach": approach() if include_approach else None,
        "topics": ["order", "cancellation"],
        "components": ["OrderService"],
        "designDecisions": approach()["designDecisions"] if include_approach else [],
        "effects": ["已取消订单停止更新", "正常路径保持不变"],
    }
    if not include_approach:
        summary.pop("implementationApproach")
    outcome = {
        "format": "ai-cockpit-task-outcome",
        "schemaVersion": 1,
        "workItemId": work_item_id,
        "status": "completed",
        "bindings": {
            "taskId": work_item_id,
            "headCommit": "a" * 40,
            "lifecycleStage": "pre_merge",
        },
        "sections": {
            "outcomeSummary": "验证通过。",
            "taskOverview": "订单状态验证。",
            "implementationApproach": approach() if include_approach else None,
        },
    }
    if not include_approach:
        outcome["sections"].pop("implementationApproach")
    contract_path = tmp_path / f"{work_item_id}.contract.json"
    summary_path = tmp_path / f"{work_item_id}.summary.json"
    outcome_path = tmp_path / f"{work_item_id}.outcome.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    outcome_path.write_text(json.dumps(outcome), encoding="utf-8")
    return contract_path, summary_path, outcome_path


def test_verified_work_item_projects_approach_decisions_evidence_and_digests(tmp_path) -> None:
    contract, summary, outcome = write_fixture(tmp_path)

    record = build_record(contract, summary, outcome, repo_root=tmp_path)

    assert record["knowledgeState"] == "verified"
    assert record["implementation"]["status"] == "verified"
    assert record["implementation"]["summary"] == "在服务入口验证状态后决定是否继续处理。"
    assert record["designDecisions"][0]["decision"] == "不修改数据库结构"
    assert record["evidence"][0]["path"] == "src/order_service.py"
    assert len(record["generatedFrom"]["summaryDigest"]) == 64
    assert len(record["generatedFrom"]["outcomeDigest"]) == 64
    assert record["mergedCommit"] is None


def test_projection_preserves_only_explicit_date_and_effective_state(tmp_path) -> None:
    contract, summary, outcome = write_fixture(tmp_path)
    summary_payload = json.loads(summary.read_text(encoding="utf-8"))
    summary_payload["date"] = "2026-08-18"
    summary_payload["effectiveState"] = "unknown"
    summary.write_text(json.dumps(summary_payload), encoding="utf-8")

    record = build_record(contract, summary, outcome, repo_root=tmp_path)

    assert record["date"] == "2026-08-18"
    assert record["effectiveState"] == "unknown"
    assert record["currentValidity"] == "unknown"


def test_projection_does_not_infer_date_or_current_validity(tmp_path) -> None:
    contract, summary, outcome = write_fixture(tmp_path)

    record = build_record(contract, summary, outcome, repo_root=tmp_path)

    assert "date" not in record
    assert record["effectiveState"] == "historical_or_current_unknown"
    assert record["currentValidity"] == "unknown"


def test_legacy_work_item_remains_partial_and_does_not_infer_approach(tmp_path) -> None:
    contract, summary, outcome = write_fixture(tmp_path, include_approach=False)

    record = build_record(contract, summary, outcome, repo_root=tmp_path)

    assert record["knowledgeState"] == "partial"
    assert record["implementation"] == {"summary": "unknown", "status": "unknown"}
    assert record["designDecisions"] == []
    assert record["unknowns"]


@pytest.mark.parametrize("mutation", ["missing_evidence", "identity_mismatch", "outcome_mismatch"])
def test_invalid_or_conflicting_sources_never_remain_verified(tmp_path, mutation) -> None:
    contract, summary, outcome = write_fixture(tmp_path)
    if mutation == "missing_evidence":
        payload = json.loads(summary.read_text(encoding="utf-8"))
        payload["implementationApproach"]["evidence"][0]["source"] = "src/missing.py"
        summary.write_text(json.dumps(payload), encoding="utf-8")
    elif mutation == "identity_mismatch":
        payload = json.loads(outcome.read_text(encoding="utf-8"))
        payload["workItemId"] = "different-work-item"
        outcome.write_text(json.dumps(payload), encoding="utf-8")
    else:
        payload = json.loads(outcome.read_text(encoding="utf-8"))
        payload["sections"]["implementationApproach"]["summary"]["text"] = "不一致的实现方式。"
        outcome.write_text(json.dumps(payload), encoding="utf-8")

    record = build_record(contract, summary, outcome, repo_root=tmp_path)

    assert record["knowledgeState"] in {"partial", "unknown"}
    assert record["implementation"]["status"] != "verified"


def test_index_rebuild_is_sorted_lightweight_and_deterministic(tmp_path) -> None:
    records_dir = tmp_path / "work-items"
    records_dir.mkdir()
    first = {
        "schemaVersion": 1,
        "workItemId": "z-work-item",
        "title": "Z",
        "topics": ["z"],
        "components": ["ZService"],
        "knowledgeState": "partial",
        "generatedFrom": {"summaryDigest": "a" * 64, "outcomeDigest": "b" * 64},
    }
    second = copy.deepcopy(first)
    second.update({"workItemId": "a-work-item", "title": "A", "topics": ["a"]})
    (records_dir / "z-work-item.json").write_text(json.dumps(first), encoding="utf-8")
    (records_dir / "a-work-item.json").write_text(json.dumps(second), encoding="utf-8")
    index_path = tmp_path / "index.json"

    first_index = rebuild_index(records_dir, index_path)
    first_bytes = index_path.read_bytes()
    second_index = rebuild_index(records_dir, index_path)

    assert first_index == second_index
    assert [item["workItemId"] for item in first_index["workItems"]] == [
        "a-work-item",
        "z-work-item",
    ]
    assert set(first_index["workItems"][0]) == {
        "workItemId",
        "title",
        "topics",
        "components",
        "state",
        "knowledgePath",
    }
    assert index_path.read_bytes() == first_bytes


def test_schema_documents_are_present_and_versioned() -> None:
    record_schema = json.loads(RECORD_SCHEMA.read_text(encoding="utf-8"))
    index_schema = json.loads(INDEX_SCHEMA.read_text(encoding="utf-8"))
    dependency_schema = json.loads(DEPENDENCY_INDEX_SCHEMA.read_text(encoding="utf-8"))
    assert record_schema["$schema"].endswith("draft/2020-12/schema")
    assert index_schema["$schema"].endswith("draft/2020-12/schema")
    assert set(record_schema["properties"]["knowledgeState"]["enum"]) == {
        "verified",
        "partial",
        "unknown",
        "superseded",
    }
    assert "semanticScore" not in index_schema["properties"]
    assert dependency_schema["properties"]["schemaVersion"]["const"] == 1
    assert set(dependency_schema["required"]) == {"schemaVersion", "records", "byPath"}


def test_checker_detects_stale_source_and_evidence_digests(tmp_path) -> None:
    contract, summary, outcome = write_fixture(tmp_path)
    record_path = tmp_path / "work-items" / "order-cancel-validation.json"
    index_path = tmp_path / "index.json"
    record_path.parent.mkdir()
    record = build_record(contract, summary, outcome, repo_root=tmp_path)
    record_path.write_text(json.dumps(record), encoding="utf-8")
    rebuild_index(record_path.parent, index_path)

    assert check_record(record_path, repo_root=tmp_path) == []
    (tmp_path / "src/order_service.py").write_text(
        "def changed():\n    return False\n", encoding="utf-8"
    )
    issues = check_record(record_path, repo_root=tmp_path)
    assert any("digest" in issue for issue in issues)


def test_checker_detects_index_drift_and_missing_record(tmp_path) -> None:
    records_dir = tmp_path / "work-items"
    records_dir.mkdir()
    record = {
        "schemaVersion": 1,
        "workItemId": "one-work-item",
        "title": "One",
        "topics": [],
        "components": [],
        "knowledgeState": "partial",
        "generatedFrom": {"summaryDigest": "a" * 64, "outcomeDigest": "b" * 64},
    }
    record_path = records_dir / "one-work-item.json"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    index_path = tmp_path / "index.json"
    rebuild_index(records_dir, index_path)

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["workItems"][0]["title"] = "drifted"
    index_path.write_text(json.dumps(payload), encoding="utf-8")
    issues = check_index(index_path, records_dir=records_dir, repo_root=tmp_path)
    assert any("index" in issue for issue in issues)

    record_path.unlink()
    issues = check_index(index_path, records_dir=records_dir, repo_root=tmp_path)
    assert any("missing" in issue for issue in issues)


def test_checker_detects_dependency_index_drift(tmp_path) -> None:
    contract, summary, outcome = write_fixture(tmp_path, work_item_id="dependency-drift")
    records_dir = tmp_path / ".ai" / "knowledge" / "work-items"
    records_dir.mkdir(parents=True)
    record = build_record(contract, summary, outcome, repo_root=tmp_path)
    (records_dir / "dependency-drift.json").write_text(json.dumps(record), encoding="utf-8")
    index_path = tmp_path / ".ai" / "knowledge" / "index.json"
    rebuild_index(records_dir, index_path)

    dependency_path = index_path.with_name("dependencies.json")
    payload = json.loads(dependency_path.read_text(encoding="utf-8"))
    payload["byPath"] = {}
    dependency_path.write_text(json.dumps(payload), encoding="utf-8")

    issues = check_index(index_path, records_dir=records_dir, repo_root=tmp_path)

    assert any("dependency index" in issue for issue in issues)


def test_archive_projection_generates_record_from_final_archive_paths(
    tmp_path, monkeypatch
) -> None:
    contract, summary, outcome = write_fixture(tmp_path, work_item_id="archived-knowledge")
    archive_dir = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive_dir.mkdir(parents=True)
    archived_contract = archive_dir / contract.name
    archived_summary = archive_dir / summary.name
    archived_outcome = archive_dir / outcome.name
    for source, target in (
        (contract, archived_contract),
        (summary, archived_summary),
        (outcome, archived_outcome),
    ):
        shutil.copyfile(source, target)

    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)
    record_path = ai_archive_work_item._generate_knowledge_projection(archived_contract)

    assert record_path == tmp_path / ".ai/knowledge/work-items/archived-knowledge.json"
    assert record_path.is_file()
    assert check_record(record_path, repo_root=tmp_path) == []
    index = json.loads((tmp_path / ".ai/knowledge/index.json").read_text(encoding="utf-8"))
    assert index["workItems"][0]["workItemId"] == "archived-knowledge"


def test_archive_projection_fails_closed_when_generated_record_has_stale_evidence(
    tmp_path, monkeypatch
):
    contract, summary, outcome = write_fixture(tmp_path, work_item_id="stale-archive")
    archive_dir = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive_dir.mkdir(parents=True)
    archived_contract = archive_dir / contract.name
    for source, target in (
        (contract, archived_contract),
        (summary, archive_dir / summary.name),
        (outcome, archive_dir / outcome.name),
    ):
        shutil.copyfile(source, target)

    original_build_record = ai_generate_knowledge_record.build_record

    def build_stale_record(*args, **kwargs):
        record = original_build_record(*args, **kwargs)
        record["evidence"][0]["digest"] = "0" * 64
        return record

    monkeypatch.setattr(ai_generate_knowledge_record, "build_record", build_stale_record)
    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)

    with pytest.raises(ValueError, match="stale or invalid"):
        ai_archive_work_item._generate_knowledge_projection(archived_contract)


def test_rebuild_existing_projections_refreshes_records_after_bound_source_changes(tmp_path):
    contract, summary, outcome = write_fixture(tmp_path, work_item_id="historical-knowledge")
    archive_dir = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive_dir.mkdir(parents=True)
    archived_contract = archive_dir / contract.name
    for source, target in (
        (contract, archived_contract),
        (summary, archive_dir / summary.name),
        (outcome, archive_dir / outcome.name),
    ):
        shutil.copyfile(source, target)

    records_dir = tmp_path / ".ai" / "knowledge" / "work-items"
    records_dir.mkdir(parents=True)
    record_path = records_dir / "historical-knowledge.json"
    record_path.write_text(
        json.dumps(
            build_record(
                archived_contract,
                archive_dir / summary.name,
                archive_dir / outcome.name,
                repo_root=tmp_path,
            )
        ),
        encoding="utf-8",
    )
    rebuild_index(records_dir, tmp_path / ".ai" / "knowledge" / "index.json")

    (tmp_path / "src/order_service.py").write_text(
        "def validate(order):\n    return order.status\n\n# refreshed source\n",
        encoding="utf-8",
    )

    changed = rebuild_existing_projections(repo_root=tmp_path)

    assert ".ai/knowledge/work-items/historical-knowledge.json" in changed
    assert (
        check_index(
            tmp_path / ".ai" / "knowledge" / "index.json",
            records_dir=records_dir,
            repo_root=tmp_path,
        )
        == []
    )
    refreshed = json.loads(record_path.read_text(encoding="utf-8"))
    assert refreshed["evidence"][0]["digest"] != "0" * 64


def test_missing_dependency_projection_falls_back_to_explicit_full_rebuild(tmp_path):
    contract, summary, outcome = write_fixture(tmp_path, work_item_id="fallback-knowledge")
    archive_dir = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive_dir.mkdir(parents=True)
    archived_contract = archive_dir / contract.name
    archived_summary = archive_dir / summary.name
    archived_outcome = archive_dir / outcome.name
    for source, target in (
        (contract, archived_contract),
        (summary, archived_summary),
        (outcome, archived_outcome),
    ):
        shutil.copyfile(source, target)

    records_dir = tmp_path / ".ai" / "knowledge" / "work-items"
    records_dir.mkdir(parents=True)
    record_path = records_dir / "fallback-knowledge.json"
    record_path.write_text(
        json.dumps(
            build_record(archived_contract, archived_summary, archived_outcome, repo_root=tmp_path)
        ),
        encoding="utf-8",
    )
    index_path = tmp_path / ".ai" / "knowledge" / "index.json"
    rebuild_index(records_dir, index_path)
    dependency_path = index_path.with_name("dependencies.json")
    dependency_path.unlink()
    (tmp_path / "src/order_service.py").write_text(
        "def changed():\n    return False\n", encoding="utf-8"
    )

    changed = rebuild_existing_projections(
        repo_root=tmp_path,
        changed_paths=["src/not-routed-yet.py"],
    )

    assert ".ai/knowledge/work-items/fallback-knowledge.json" in changed
    assert dependency_path.is_file()
    assert build_dependency_index(records_dir) == json.loads(
        dependency_path.read_text(encoding="utf-8")
    )
    assert check_index(index_path, records_dir=records_dir, repo_root=tmp_path) == []


def test_selective_refresh_rebuilds_only_records_bound_to_changed_path(tmp_path, monkeypatch):
    contract, summary, outcome = write_fixture(tmp_path, work_item_id="affected-knowledge")
    (tmp_path / "src/unrelated.py").write_text(
        "def unrelated():\n    return True\n", encoding="utf-8"
    )
    archive_dir = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive_dir.mkdir(parents=True)

    def archive(
        contract_source: Path,
        summary_source: Path,
        outcome_source: Path,
        work_item_id: str,
    ) -> tuple[Path, Path, Path]:
        archived_contract = archive_dir / f"{work_item_id}.contract.json"
        archived_summary = archive_dir / f"{work_item_id}.summary.json"
        archived_outcome = archive_dir / f"{work_item_id}.outcome.json"
        for source_path, target in (
            (contract_source, archived_contract),
            (summary_source, archived_summary),
            (outcome_source, archived_outcome),
        ):
            shutil.copyfile(source_path, target)
        return archived_contract, archived_summary, archived_outcome

    first_paths = archive(contract, summary, outcome, "affected-knowledge")
    second_contract = tmp_path / "unrelated-knowledge.contract.json"
    second_summary = tmp_path / "unrelated-knowledge.summary.json"
    second_outcome = tmp_path / "unrelated-knowledge.outcome.json"
    second_contract.write_text(
        json.dumps(
            {
                **json.loads(contract.read_text(encoding="utf-8")),
                "workItemId": "unrelated-knowledge",
                "title": "Unrelated knowledge",
            }
        ),
        encoding="utf-8",
    )

    def replace_path(value):
        if isinstance(value, dict):
            return {key: replace_path(child) for key, child in value.items()}
        if isinstance(value, list):
            return [replace_path(child) for child in value]
        if value == "src/order_service.py":
            return "src/unrelated.py"
        if value == "affected-knowledge":
            return "unrelated-knowledge"
        return value

    second_summary.write_text(
        json.dumps(replace_path(json.loads(summary.read_text(encoding="utf-8")))),
        encoding="utf-8",
    )
    second_outcome.write_text(
        json.dumps(replace_path(json.loads(outcome.read_text(encoding="utf-8")))),
        encoding="utf-8",
    )
    second_paths = archive(second_contract, second_summary, second_outcome, "unrelated-knowledge")

    records_dir = tmp_path / ".ai" / "knowledge" / "work-items"
    records_dir.mkdir(parents=True)
    for paths in (first_paths, second_paths):
        record = build_record(*paths, repo_root=tmp_path)
        (records_dir / f"{record['workItemId']}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )
    rebuild_index(records_dir, tmp_path / ".ai" / "knowledge" / "index.json")
    (tmp_path / "src/order_service.py").write_text(
        "def validate(order):\n    return order.status\n\n# refreshed source\n",
        encoding="utf-8",
    )

    calls: list[str] = []
    original_build_record = ai_generate_knowledge_record.build_record

    def counted_build_record(*args, **kwargs):
        calls.append(Path(args[0]).name)
        return original_build_record(*args, **kwargs)

    monkeypatch.setattr(ai_generate_knowledge_record, "build_record", counted_build_record)
    changed = rebuild_existing_projections(
        repo_root=tmp_path,
        changed_paths=["src/order_service.py"],
    )

    assert calls == ["affected-knowledge.contract.json"]
    assert ".ai/knowledge/work-items/affected-knowledge.json" in changed
    assert ".ai/knowledge/work-items/unrelated-knowledge.json" not in changed
