from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import scripts.ai_external_handoff as external_handoff
from scripts.ai_external_handoff import (
    HandoffError,
    build_handoff,
    ingest_and_record,
    ingest_receipt,
    project_handoff,
    record_handoff,
)
from scripts.ai_task_event_log import read_events


def bindings() -> dict[str, str]:
    return {
        "workItemId": "external-handoff-test",
        "branch": "codex/external-handoff-test",
        "headCommit": "a" * 40,
        "tree": "b" * 40,
        "contractDigest": "c" * 64,
        "summaryDigest": "d" * 64,
    }


def test_bound_handoff_projects_yellow_awaiting_state() -> None:
    handoff = build_handoff(
        bindings(),
        action="hosted_ci.run",
        fulfiller="hosted_ci",
        receipt_kind="hosted_ci_receipt",
        deadline="2026-08-10T00:00:00Z",
    )
    projected = project_handoff(handoff, now="2026-08-09T00:00:00Z")
    assert projected["state"] == "awaiting_external_receipt"
    assert projected["humanStatusColor"] == "yellow"
    assert projected["action"] == "hosted_ci.run"
    assert projected["fulfiller"] == "hosted_ci"
    assert projected["receiptKind"] == "hosted_ci_receipt"


@pytest.mark.parametrize(
    "field", ["workItemId", "branch", "headCommit", "tree", "contractDigest", "summaryDigest"]
)
def test_receipt_identity_mismatch_fails_closed(field: str) -> None:
    handoff = build_handoff(
        bindings(),
        action="human.confirm",
        fulfiller="human",
        receipt_kind="human_confirmation",
        deadline="2026-08-10T00:00:00Z",
    )
    receipt = {
        "receiptVersion": 1,
        "kind": "human_confirmation",
        "fulfilledBy": "human",
        "bindings": bindings(),
    }
    receipt["bindings"][field] = "wrong"  # type: ignore[index]
    with pytest.raises(HandoffError, match="binding"):
        ingest_receipt(handoff, receipt, now="2026-08-09T00:00:00Z")


def test_timeout_blocks_and_never_resumes_without_receipt() -> None:
    handoff = build_handoff(
        bindings(),
        action="adopter.execute",
        fulfiller="adopter",
        receipt_kind="adopter_execution",
        deadline="2026-08-09T00:00:00Z",
    )
    projected = project_handoff(handoff, now="2026-08-09T00:00:01Z")
    assert projected["state"] == "blocked"
    assert projected["humanStatusColor"] == "red"
    assert "receipt" in projected["recoveryCondition"]
    with pytest.raises(HandoffError, match="expired"):
        ingest_receipt(handoff, {"receiptVersion": 1}, now="2026-08-09T00:00:01Z")


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"handoffVersion": 2}, "unsupported handoff version"),
        ({"action": "free text action"}, "bounded identifier"),
        ({"fulfiller": "unknown"}, "not authorized"),
        ({"receiptKind": "invalid receipt"}, "bounded identifier"),
        ({"bindings": {**bindings(), "headCommit": "not-a-digest"}}, "hexadecimal digest"),
        (
            {"bindings": {key: value for key, value in bindings().items() if key != "tree"}},
            "required",
        ),
        ({"deadline": "2026-08-10"}, "UTC Z timestamp"),
        ({"deadline": "not-a-timeZ"}, "ISO-8601"),
    ],
)
def test_handoff_validation_rejects_unbounded_or_malformed_facts(
    update: dict[str, object], message: str
) -> None:
    handoff = build_handoff(
        bindings(),
        action="hosted_ci.run",
        fulfiller="hosted_ci",
        receipt_kind="hosted_ci_receipt",
        deadline="2026-08-10T00:00:00Z",
    )
    handoff.update(update)
    with pytest.raises(HandoffError, match=message):
        project_handoff(handoff, now="2026-08-09T00:00:00Z")


@pytest.mark.parametrize(
    ("receipt_update", "message"),
    [
        ({"receiptVersion": 2}, "shape or kind"),
        ({"kind": "foreign_receipt"}, "shape or kind"),
        ({"fulfilledBy": "adopter"}, "not authorized"),
    ],
)
def test_receipt_rejects_wrong_shape_kind_or_fulfiller(
    receipt_update: dict[str, object], message: str
) -> None:
    handoff = build_handoff(
        bindings(),
        action="human.confirm",
        fulfiller="human",
        receipt_kind="human_confirmation",
        deadline="2026-08-10T00:00:00Z",
    )
    receipt: dict[str, object] = {
        "receiptVersion": 1,
        "kind": "human_confirmation",
        "fulfilledBy": "human",
        "bindings": bindings(),
    }
    receipt.update(receipt_update)
    with pytest.raises(HandoffError, match=message):
        ingest_receipt(handoff, receipt, now="2026-08-09T00:00:00Z")


def test_only_valid_handoff_and_receipt_append_durable_events(tmp_path: Path) -> None:
    handoff = build_handoff(
        bindings(),
        action="provider_release.publish",
        fulfiller="provider_release",
        receipt_kind="provider_release_receipt",
        deadline="2026-08-10T00:00:00Z",
    )
    events = tmp_path / "events.jsonl"
    record_handoff(events, handoff)
    receipt = {
        "receiptVersion": 1,
        "kind": "provider_release_receipt",
        "fulfilledBy": "provider_release",
        "bindings": bindings(),
    }
    ingest_and_record(events, handoff, receipt, now="2026-08-09T00:00:00Z")
    assert [item["eventType"] for item in read_events(events)] == [
        "external_handoff",
        "external_receipt_ingested",
    ]


def test_cli_projects_then_records_bound_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    handoff_file = tmp_path / "handoff.json"
    handoff_file.write_text(
        json.dumps(
            build_handoff(
                bindings(),
                action="hosted_ci.run",
                fulfiller="hosted_ci",
                receipt_kind="hosted_ci_receipt",
                deadline="2026-08-10T00:00:00Z",
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_external_handoff.py", str(handoff_file), "--now", "2026-08-09T00:00:00Z"],
    )
    assert external_handoff.main() == 0
    assert json.loads(capsys.readouterr().out)["state"] == "awaiting_external_receipt"

    events = tmp_path / "events.jsonl"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai_external_handoff.py",
            str(handoff_file),
            "--events",
            str(events),
            "--now",
            "2026-08-09T00:00:00Z",
        ],
    )
    assert external_handoff.main() == 0
    assert json.loads(capsys.readouterr().out)["eventType"] == "external_handoff"


def test_cli_fails_closed_for_invalid_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    handoff_file = tmp_path / "invalid.json"
    handoff_file.write_text("not-json", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_external_handoff.py", str(handoff_file), "--now", "2026-08-09T00:00:00Z"],
    )
    with pytest.raises(SystemExit, match="2"):
        external_handoff.main()
