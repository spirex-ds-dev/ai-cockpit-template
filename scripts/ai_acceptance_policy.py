"""Pure acceptance signal policy."""
# mypy: ignore-errors

from __future__ import annotations
from typing import Any

SOURCES = ["contract.acceptance", "summary.verification", "summary.reviewReadiness"]


def acceptance_signal(
    contract: dict[str, Any], summary: dict[str, Any] | None, verification: dict[str, Any]
) -> dict[str, Any]:
    if summary is None:
        return {"value": "unknown", "evidence": ["summary is missing"], "sources": SOURCES}
    acceptance = contract.get("acceptance")
    if not isinstance(acceptance, list) or not acceptance:
        return {
            "value": "unknown",
            "evidence": ["contract.acceptance is missing"],
            "sources": SOURCES,
        }
    review = (
        summary.get("reviewReadiness") if isinstance(summary.get("reviewReadiness"), dict) else {}
    )
    status = (
        review.get("status")
        if review.get("status") in {"ready", "ready_with_risks", "not_ready", "blocked"}
        else "unknown"
    )
    if verification.get("value") != "passed":
        return {
            "value": "incomplete",
            "evidence": [f"required verification is {verification.get('value')}"],
            "sources": SOURCES,
        }
    if summary.get("unknownsRemaining"):
        return {
            "value": "incomplete",
            "evidence": ["summary.unknownsRemaining is not empty"],
            "sources": SOURCES,
        }
    if status == "unknown":
        return {
            "value": "unknown",
            "evidence": ["summary.reviewReadiness is missing"],
            "sources": SOURCES,
        }
    if status in {"not_ready", "blocked"}:
        return {
            "value": "incomplete",
            "evidence": [f"reviewReadiness.status is {status}"],
            "sources": SOURCES,
        }
    return {
        "value": "complete",
        "evidence": [f"reviewReadiness.status is {status}"],
        "sources": SOURCES,
    }
