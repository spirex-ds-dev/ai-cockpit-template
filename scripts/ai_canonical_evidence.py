"""Validate and render the canonical evidence/event document."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1
EVIDENCE_STATUSES = {"observed", "verified", "blocked", "superseded"}
CLAIM_STATUSES = {"supported", "blocked"}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_digest(payload: dict[str, Any]) -> str:
    """Return the stable digest format used by evidence records."""

    return f"sha256:{hashlib.sha256(_canonical_json(payload).encode('utf-8')).hexdigest()}"


def validate_document(document: dict[str, Any], *, now: datetime | None = None) -> list[str]:
    """Return deterministic validation errors; any error blocks evidence claims."""

    errors: list[str] = []
    if document.get("schemaVersion") != SCHEMA_VERSION:
        errors.append("schemaVersion must be 1")
    if not isinstance(document.get("documentId"), str) or not document["documentId"]:
        errors.append("documentId is required")
    evidence = document.get("evidence")
    events = document.get("events")
    claims = document.get("claims")
    if (
        not isinstance(evidence, list)
        or not isinstance(events, list)
        or not isinstance(claims, list)
    ):
        return [*errors, "evidence, events and claims must be arrays"]

    now = now or datetime.now(timezone.utc)
    ids: set[str] = set()
    fact_keys: dict[tuple[str, str], str] = {}
    for item in evidence:
        if not isinstance(item, dict):
            errors.append("evidence entries must be objects")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            errors.append("evidence id is required")
            continue
        if item_id in ids:
            errors.append(f"duplicate evidence id: {item_id}")
        ids.add(item_id)
        source = item.get("source")
        digest = item.get("digest")
        payload = item.get("payload")
        if not isinstance(source, str) or not source:
            errors.append(f"{item_id}: source is required")
        if not isinstance(payload, dict):
            errors.append(f"{item_id}: payload must be an object")
        elif digest != payload_digest(payload):
            errors.append(f"{item_id}: digest mismatch")
        if item.get("status") not in EVIDENCE_STATUSES:
            errors.append(f"{item_id}: invalid status")
        if isinstance(item.get("expiresAt"), str):
            try:
                expiry = datetime.fromisoformat(item["expiresAt"].replace("Z", "+00:00"))
                if expiry <= now:
                    errors.append(f"{item_id}: evidence is stale")
            except ValueError:
                errors.append(f"{item_id}: invalid expiresAt")
        subject, fact_key = item.get("subject"), item.get("factKey")
        if (
            not isinstance(subject, str)
            or not subject
            or not isinstance(fact_key, str)
            or not fact_key
        ):
            errors.append(f"{item_id}: subject and factKey are required")
        else:
            key = (subject, fact_key)
            prior = fact_keys.get(key)
            if prior is not None:
                errors.append(
                    f"conflicting or duplicate fact: {subject}/{fact_key} ({prior}, {item_id})"
                )
            fact_keys[key] = item_id

    for event in events:
        if not isinstance(event, dict):
            errors.append("event entries must be objects")
            continue
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id:
            errors.append("event id is required")
            continue
        if event_id in ids:
            errors.append(f"duplicate record id: {event_id}")
        ids.add(event_id)
        refs = event.get("evidenceIds")
        if (
            not isinstance(refs, list)
            or not refs
            or any(
                ref not in {item.get("id") for item in evidence if isinstance(item, dict)}
                for ref in refs
            )
        ):
            errors.append(f"{event_id}: event references unknown evidence")

    evidence_ids = {item.get("id") for item in evidence if isinstance(item, dict)}
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("claim entries must be objects")
            continue
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not claim_id:
            errors.append("claim id is required")
            continue
        if claim_id in ids:
            errors.append(f"duplicate record id: {claim_id}")
        ids.add(claim_id)
        if claim.get("status") not in CLAIM_STATUSES:
            errors.append(f"{claim_id}: invalid claim status")
        refs = claim.get("evidenceIds")
        if not isinstance(refs, list) or not refs or any(ref not in evidence_ids for ref in refs):
            errors.append(f"{claim_id}: claim has missing evidence")
        if claim.get("status") == "supported" and not refs:
            errors.append(f"{claim_id}: unsupported claim without evidence")
    return sorted(set(errors))


def render_markdown(document: dict[str, Any]) -> str:
    """Render only canonical facts, in stable order, for human consumers."""

    errors = validate_document(document)
    if errors:
        raise ValueError("cannot render invalid canonical evidence: " + "; ".join(errors))
    lines = [
        f"# Evidence {document['documentId']}",
        "",
        f"Captured: {document['capturedAt']}",
        "",
        "## Claims",
        "",
    ]
    for claim in sorted(document["claims"], key=lambda item: item["id"]):
        refs = ", ".join(sorted(claim["evidenceIds"]))
        lines.append(f"- `{claim['status']}` {claim['statement']} (evidence: {refs})")
    lines.extend(["", "## Events", ""])
    for event in sorted(document["events"], key=lambda item: (item["sequence"], item["id"])):
        lines.append(
            f"- `{event['sequence']}` `{event['kind']}` (evidence: {', '.join(sorted(event['evidenceIds']))})"
        )
    return "\n".join(lines) + "\n"
