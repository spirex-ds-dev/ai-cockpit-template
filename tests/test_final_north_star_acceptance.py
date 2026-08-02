from __future__ import annotations

import json
from pathlib import Path

import ai_final_north_star_acceptance as acceptance
import pytest


def record(decision: str = "CONDITIONAL_GO") -> dict[str, object]:
    return {
        "decision": decision,
        "dimensions": {
            name: {"status": "verified", "evidence": ["receipt"]}
            for name in acceptance.REQUIRED_DIMENSIONS
        },
        "limitations": [],
    }


def test_go_requires_real_adopter_and_provider_evidence() -> None:
    value = record("GO")
    value["dimensions"]["real_adopter"]["status"] = "not_verified"  # type: ignore[index]
    with pytest.raises(acceptance.FinalAcceptanceError, match="GO requires"):
        acceptance.evaluate(value)


def test_every_dimension_is_required() -> None:
    value = record()
    value["dimensions"].pop("recovery")  # type: ignore[index]
    with pytest.raises(acceptance.FinalAcceptanceError, match="missing dimensions"):
        acceptance.evaluate(value)


def test_conditional_go_retains_explicit_limitations() -> None:
    value = record()
    value["dimensions"]["provider_evidence"]["status"] = "not_verified"  # type: ignore[index]
    value["limitations"] = ["Provider evidence remains external."]
    assert acceptance.evaluate(value)["decision"] == "CONDITIONAL_GO"


def test_published_decision_is_complete_and_preserves_external_limitations() -> None:
    published = json.loads(Path("docs/reference/final-north-star-acceptance.json").read_text())
    result = acceptance.evaluate(published)

    assert result["decision"] == "CONDITIONAL_GO"
    assert result["dimensions"]["real_adopter"]["status"] == "limited"
    assert result["dimensions"]["provider_evidence"]["status"] == "limited"
