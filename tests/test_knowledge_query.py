"""TDD contract tests for the deterministic Implementation Knowledge query surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from ai_knowledge_query import KnowledgeQueryError, QueryFilters, query_knowledge


def write_fixture(
    root: Path,
    *,
    task: str,
    state: str,
    topic: str,
    component: str,
    date: str | None,
    commit: str | None,
    supersedes: list[str] | None = None,
) -> None:
    records = root / ".ai" / "knowledge" / "work-items"
    records.mkdir(parents=True, exist_ok=True)
    archive = root / ".ai" / "work-items" / "archive" / "2026"
    archive.mkdir(parents=True, exist_ok=True)
    source_paths = [
        archive / f"{task}.contract.json",
        archive / f"{task}.summary.json",
        archive / f"{task}.outcome.json",
    ]
    for source_path in source_paths:
        source_path.write_text(json.dumps({"workItemId": task}) + "\n", encoding="utf-8")
    record = {
        "schemaVersion": 1,
        "workItemId": task,
        "title": task.replace("-", " "),
        "topics": [topic],
        "components": [component],
        "implementation": {"summary": f"implementation for {task}", "status": "verified"},
        "configuration": None,
        "changes": [f"src/{task}.py"],
        "designDecisions": [],
        "effects": [],
        "evidence": [],
        "mergedCommit": commit,
        "currentValidity": "superseded" if state == "superseded" else "current",
        "supersedes": supersedes or [],
        "generatedFrom": {
            "contractPath": f".ai/work-items/archive/2026/{task}.contract.json",
            "contractDigest": hashlib.sha256(source_paths[0].read_bytes()).hexdigest(),
            "summaryPath": f".ai/work-items/archive/2026/{task}.summary.json",
            "summaryDigest": hashlib.sha256(source_paths[1].read_bytes()).hexdigest(),
            "outcomePath": f".ai/work-items/archive/2026/{task}.outcome.json",
            "outcomeDigest": hashlib.sha256(source_paths[2].read_bytes()).hexdigest(),
        },
        "knowledgeState": state,
        "unknowns": [] if state == "verified" else ["recorded evidence is incomplete"],
    }
    if state == "verified":
        evidence_path = root / "evidence" / f"{task}.py"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text("# fixture evidence\n", encoding="utf-8")
        record["evidence"] = [
            {
                "type": "test",
                "path": evidence_path.relative_to(root).as_posix(),
                "digest": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            }
        ]
    if date is not None:
        record["date"] = date
    (records / f"{task}.json").write_text(
        json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_index(root: Path, tasks: list[tuple[str, str, str, str]]) -> Path:
    index = root / ".ai" / "knowledge" / "index.json"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "workItems": [
                    {
                        "workItemId": task,
                        "title": task.replace("-", " "),
                        "topics": [topic],
                        "components": [component],
                        "state": state,
                        "knowledgePath": f".ai/knowledge/work-items/{task}.json",
                    }
                    for task, state, topic, component in sorted(tasks)
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return index


def test_query_combines_exact_filters_and_inclusive_date_range(tmp_path: Path) -> None:
    write_fixture(
        tmp_path,
        task="orders-2026-01-15",
        state="verified",
        topic="orders",
        component="OrderService",
        date="2026-01-15",
        commit="a" * 40,
    )
    write_fixture(
        tmp_path,
        task="orders-2026-02-01",
        state="partial",
        topic="orders",
        component="OrderService",
        date="2026-02-01",
        commit="b" * 40,
    )
    index = write_index(
        tmp_path,
        [
            ("orders-2026-01-15", "verified", "orders", "OrderService"),
            ("orders-2026-02-01", "partial", "orders", "OrderService"),
        ],
    )

    result = query_knowledge(
        repo_root=tmp_path,
        index_path=index,
        records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
        filters=QueryFilters(
            topic="orders",
            component="OrderService",
            status="verified",
            date_from="2026-01-01",
            date_to="2026-01-31",
        ),
    )

    assert result["matchedCount"] == 1
    assert result["matches"][0]["record"]["workItemId"] == "orders-2026-01-15"


def test_query_preserves_all_states_and_explicit_supersession(tmp_path: Path) -> None:
    tasks = [
        ("verified-item", "verified", "one", "One"),
        ("partial-item", "partial", "two", "Two"),
        ("unknown-item", "unknown", "three", "Three"),
        ("superseded-item", "superseded", "four", "Four"),
    ]
    for task, state, topic, component in tasks:
        write_fixture(
            tmp_path,
            task=task,
            state=state,
            topic=topic,
            component=component,
            date="2026-01-01",
            commit=None,
            supersedes=["verified-item"] if state == "superseded" else None,
        )
    index = write_index(tmp_path, tasks)

    result = query_knowledge(
        repo_root=tmp_path,
        index_path=index,
        records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
        filters=QueryFilters(),
    )

    assert [item["record"]["knowledgeState"] for item in result["matches"]] == [
        "partial",
        "superseded",
        "unknown",
        "verified",
    ]
    superseded = result["matches"][1]["record"]
    assert superseded["supersedes"] == ["verified-item"]


def test_query_exposes_design_results_and_latest_known_record(tmp_path: Path) -> None:
    write_fixture(
        tmp_path,
        task="old-validation",
        state="verified",
        topic="validation",
        component="ValidationService",
        date="2026-01-01",
        commit=None,
    )
    write_fixture(
        tmp_path,
        task="new-validation",
        state="verified",
        topic="validation",
        component="ValidationService",
        date="2026-02-01",
        commit=None,
        supersedes=["old-validation"],
    )
    index = write_index(
        tmp_path,
        [
            ("old-validation", "verified", "validation", "ValidationService"),
            ("new-validation", "verified", "validation", "ValidationService"),
        ],
    )

    result = query_knowledge(
        repo_root=tmp_path,
        index_path=index,
        records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
        filters=QueryFilters(component="ValidationService"),
    )

    assert result["results"] == result["matches"]
    by_id = {item["record"]["workItemId"]: item for item in result["results"]}
    assert by_id["old-validation"]["state"] == "verified"
    assert by_id["old-validation"]["latestKnownRecord"] == "new-validation"
    assert by_id["new-validation"]["latestKnownRecord"] == "new-validation"


def test_query_keeps_conflicting_explicit_supersession_unknown(tmp_path: Path) -> None:
    tasks = [
        ("old-validation", "verified", "validation", "ValidationService"),
        ("new-validation-a", "verified", "validation", "ValidationService"),
        ("new-validation-b", "verified", "validation", "ValidationService"),
    ]
    write_fixture(
        tmp_path,
        task="old-validation",
        state="verified",
        topic="validation",
        component="ValidationService",
        date="2026-01-01",
        commit=None,
    )
    for task in ("new-validation-a", "new-validation-b"):
        write_fixture(
            tmp_path,
            task=task,
            state="verified",
            topic="validation",
            component="ValidationService",
            date="2026-02-01",
            commit=None,
            supersedes=["old-validation"],
        )
    index = write_index(tmp_path, tasks)

    result = query_knowledge(
        repo_root=tmp_path,
        index_path=index,
        records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
        filters=QueryFilters(work_item_id="old-validation"),
    )

    item = result["results"][0]
    assert item["latestKnownRecord"] is None
    assert item["supersessionStatus"] == "conflict"


def test_query_is_stable_empty_and_read_only(tmp_path: Path) -> None:
    write_fixture(
        tmp_path,
        task="stable-item",
        state="verified",
        topic="stable",
        component="StableComponent",
        date="2026-01-01",
        commit="d" * 40,
    )
    index = write_index(tmp_path, [("stable-item", "verified", "stable", "StableComponent")])
    record_path = tmp_path / ".ai" / "knowledge" / "work-items" / "stable-item.json"
    before = {path: path.read_bytes() for path in (index, record_path)}
    filters = QueryFilters(work_item_id="missing-item")

    first = query_knowledge(
        repo_root=tmp_path,
        index_path=index,
        records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
        filters=filters,
    )
    second = query_knowledge(
        repo_root=tmp_path,
        index_path=index,
        records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
        filters=filters,
    )

    assert first == second
    assert first["matchedCount"] == 0
    assert first["matches"] == []
    assert {path: path.read_bytes() for path in before} == before


def test_query_fails_closed_for_missing_record(tmp_path: Path) -> None:
    index = write_index(tmp_path, [("missing-item", "unknown", "missing", "Missing")])

    with pytest.raises(KnowledgeQueryError, match="missing record"):
        query_knowledge(
            repo_root=tmp_path,
            index_path=index,
            records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
            filters=QueryFilters(),
        )


def test_query_fails_closed_for_missing_supersession_target(tmp_path: Path) -> None:
    write_fixture(
        tmp_path,
        task="new-validation",
        state="verified",
        topic="validation",
        component="ValidationService",
        date="2026-02-01",
        commit=None,
        supersedes=["missing-validation"],
    )
    index = write_index(
        tmp_path, [("new-validation", "verified", "validation", "ValidationService")]
    )

    with pytest.raises(KnowledgeQueryError, match="invalid|missing record"):
        query_knowledge(
            repo_root=tmp_path,
            index_path=index,
            records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
            filters=QueryFilters(),
        )


def test_query_fails_closed_for_supersession_cycle(tmp_path: Path) -> None:
    write_fixture(
        tmp_path,
        task="validation-a",
        state="verified",
        topic="validation",
        component="ValidationService",
        date="2026-01-01",
        commit=None,
        supersedes=["validation-b"],
    )
    write_fixture(
        tmp_path,
        task="validation-b",
        state="verified",
        topic="validation",
        component="ValidationService",
        date="2026-02-01",
        commit=None,
        supersedes=["validation-a"],
    )
    index = write_index(
        tmp_path,
        [
            ("validation-a", "verified", "validation", "ValidationService"),
            ("validation-b", "verified", "validation", "ValidationService"),
        ],
    )

    with pytest.raises(KnowledgeQueryError, match="invalid|cycle"):
        query_knowledge(
            repo_root=tmp_path,
            index_path=index,
            records_dir=tmp_path / ".ai" / "knowledge" / "work-items",
            filters=QueryFilters(),
        )
