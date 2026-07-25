"""Tests for append-only Task Outcome event evidence."""

import json
from pathlib import Path

import pytest

from scripts.ai_task_event_log import (
    EventLogError,
    append_event,
    finding_fingerprint,
    read_events,
    validate_event,
)


def event(event_id: str = "event-1", event_type: str = "warning") -> dict[str, object]:
    return {
        "eventId": event_id,
        "eventType": event_type,
        "workItemId": "task-event-log",
        "occurredAt": "2026-07-25T00:00:00Z",
        "evidence": [{"source": "pytest", "subject": "test"}],
    }


def test_append_and_reconstruct_jsonl_without_rewriting_history(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    append_event(path, event())
    before = path.read_bytes()
    append_event(path, event("event-2", "completed"))
    after = path.read_bytes()
    assert after.startswith(before)
    assert [row["eventId"] for row in read_events(path)] == ["event-1", "event-2"]


def test_all_supported_event_types_are_appendable(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    event_types = [
        "finding",
        "risk",
        "warning",
        "confirmation",
        "stop",
        "resume",
        "resolution",
        "risk-accepted",
        "check-pass-after-fix",
        "prevention",
        "completed",
        "cancelled",
    ]
    for index, event_type in enumerate(event_types):
        candidate = event(f"event-{index}", event_type)
        if event_type == "finding":
            candidate.update(
                {
                    "findingFingerprint": finding_fingerprint(
                        "checker", "reason", "resource", "subject"
                    ),
                    "checkerId": "checker",
                    "reasonCode": "reason",
                    "affectedResource": "resource",
                    "evidenceSubject": "subject",
                }
            )
        append_event(path, candidate)
    assert len(read_events(path)) == len(event_types)


def test_fingerprint_is_stable_and_post_fix_recurrence_is_new(tmp_path: Path) -> None:
    fingerprint = finding_fingerprint("checker", "reason", "resource", "subject")
    assert fingerprint == finding_fingerprint("checker", "reason", "resource", "subject")
    path = tmp_path / "events.jsonl"
    first = event("finding-1", "finding")
    first.update(
        {
            "findingFingerprint": fingerprint,
            "checkerId": "checker",
            "reasonCode": "reason",
            "affectedResource": "resource",
            "evidenceSubject": "subject",
        }
    )
    append_event(path, first)
    recurrence = dict(first, eventId="finding-2", recurrence="post_fix")
    append_event(path, recurrence)
    assert len(read_events(path)) == 2


def test_correction_and_supersession_reference_existing_history(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    append_event(path, event())
    append_event(path, event("event-2", "resolution") | {"correctsEventId": "event-1"})
    append_event(path, event("event-3", "resolution") | {"supersedesEventId": "event-2"})
    assert len(read_events(path)) == 3


@pytest.mark.parametrize(
    "candidate",
    [
        event("event-1", "unknown"),
        event("event-1", "event_corrected"),
        event("event-1") | {"password": "secret"},
        event("event-1") | {"correctsEventId": "missing"},
    ],
)
def test_invalid_or_secret_events_are_rejected(
    tmp_path: Path, candidate: dict[str, object]
) -> None:
    with pytest.raises(EventLogError):
        append_event(tmp_path / "events.jsonl", candidate)


def test_duplicate_event_id_and_malformed_json_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    append_event(path, event())
    with pytest.raises(EventLogError, match="duplicate"):
        append_event(path, event())
    path.write_text(path.read_text(encoding="utf-8") + "not-json\n", encoding="utf-8")
    with pytest.raises(EventLogError, match="invalid JSON"):
        read_events(path)


def test_serialized_events_have_no_secret_literals(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    append_event(path, event())
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "password" not in payload


@pytest.mark.parametrize(
    "parts",
    [("", "reason", "resource", "subject"), ("checker", "", "resource", "subject")],
)
def test_fingerprint_rejects_empty_identity_parts(parts: tuple[str, str, str, str]) -> None:
    with pytest.raises(EventLogError, match="fingerprint inputs"):
        finding_fingerprint(*parts)


def test_event_validation_rejects_missing_fields_and_non_object_log_lines(tmp_path: Path) -> None:
    with pytest.raises(EventLogError, match="missing event fields"):
        validate_event({})
    path = tmp_path / "events.jsonl"
    path.write_text("\n", encoding="utf-8")
    with pytest.raises(EventLogError, match="blank event line"):
        read_events(path)
    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(EventLogError, match="must be an object"):
        read_events(path)
