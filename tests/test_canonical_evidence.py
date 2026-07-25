from datetime import datetime, timezone

import pytest

from ai_canonical_evidence import payload_digest, render_markdown, validate_document


def evidence(*, item_id="ev-1", subject="work-item", fact_key="tests", payload=None, **extra):
    payload = payload or {"result": "passed"}
    return {
        "id": item_id,
        "source": "ci://run/1",
        "capturedAt": "2026-07-25T10:00:00Z",
        "digest": payload_digest(payload),
        "subject": subject,
        "factKey": fact_key,
        "payload": payload,
        "status": "verified",
        **extra,
    }


def document(*, records=None, claims=None, events=None):
    records = records or [evidence()]
    return {
        "schemaVersion": 1,
        "documentId": "doc-1",
        "capturedAt": "2026-07-25T10:00:00Z",
        "evidence": records,
        "events": events
        or [
            {
                "id": "event-1",
                "sequence": 1,
                "kind": "check-pass",
                "evidenceIds": [records[0]["id"]],
            }
        ],
        "claims": claims
        or [
            {
                "id": "claim-1",
                "statement": "The check passed",
                "status": "supported",
                "evidenceIds": [records[0]["id"]],
            }
        ],
    }


def test_valid_document_and_render_are_deterministic():
    doc = document()
    assert validate_document(doc) == []
    assert render_markdown(doc) == render_markdown(doc)
    assert "supported" in render_markdown(doc)


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (lambda doc: doc["evidence"][0].update(digest="sha256:" + "0" * 64), "digest mismatch"),
        (lambda doc: doc["claims"][0].update(evidenceIds=["missing"]), "missing evidence"),
        (lambda doc: doc["evidence"][0].update(expiresAt="2020-01-01T00:00:00Z"), "stale"),
    ],
)
def test_invalid_evidence_fails_closed(mutation, expected):
    doc = document()
    mutation(doc)
    assert any(
        expected in error
        for error in validate_document(doc, now=datetime(2026, 7, 25, tzinfo=timezone.utc))
    )


def test_duplicate_facts_and_event_references_are_rejected():
    first = evidence()
    second = evidence(item_id="ev-2")
    doc = document(records=[first, second])
    doc["events"][0]["evidenceIds"] = ["missing"]
    errors = validate_document(doc)
    assert any("duplicate fact" in error for error in errors)
    assert any("unknown evidence" in error for error in errors)


def test_supported_claim_without_evidence_is_rejected():
    doc = document(
        claims=[
            {"id": "claim-1", "statement": "unsupported", "status": "supported", "evidenceIds": []}
        ]
    )
    assert any("missing evidence" in error for error in validate_document(doc))


def test_missing_source_invalid_status_and_malformed_records_are_rejected():
    doc = document()
    doc["evidence"][0].pop("source")
    doc["evidence"][0]["status"] = "unknown"
    doc["events"] = [
        None,
        {"id": "event-1", "sequence": 1, "kind": "check", "evidenceIds": ["ev-1"]},
    ]
    doc["claims"] = [
        {"id": "event-1", "statement": "duplicate id", "status": "blocked", "evidenceIds": ["ev-1"]}
    ]
    errors = validate_document(doc)
    assert any("source is required" in error for error in errors)
    assert any("invalid status" in error for error in errors)
    assert any("entries must be objects" in error for error in errors)
    assert any("duplicate record id" in error for error in errors)


def test_invalid_schema_version_and_missing_document_id_are_rejected():
    doc = document()
    doc["schemaVersion"] = 2
    doc["documentId"] = ""
    errors = validate_document(doc)
    assert "schemaVersion must be 1" in errors
    assert "documentId is required" in errors
