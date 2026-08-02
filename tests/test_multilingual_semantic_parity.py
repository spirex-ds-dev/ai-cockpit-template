from __future__ import annotations

import copy

import pytest

from scripts.ai_multilingual_semantic_parity import (
    SemanticParityError,
    build_projection,
    validate_parity,
)


def facts() -> dict[str, object]:
    return {
        "status": "completed_with_warnings",
        "prohibitedClaims": ["enterprise_ready"],
        "safetyBoundaries": ["provider evidence required"],
        "humanDecisions": ["repository_administrator"],
        "risks": ["local evidence cannot prove provider controls"],
        "limitations": ["arbitrary evidence prose remains source text"],
        "commands": ["make ai-finish TASK=example"],
        "paths": [".ai/cockpit/current_status.md"],
        "capabilityClaims": ["governance_status_verified"],
    }


def views() -> dict[str, dict[str, object]]:
    return {locale: facts() for locale in ("en", "ja", "zh-CN")}


def test_equivalent_controlled_facts_validate_across_three_languages() -> None:
    projection = validate_parity(views())
    assert dict(projection.values)["status"] == ("completed_with_warnings",)


@pytest.mark.parametrize("field", ["capabilityClaims", "safetyBoundaries", "limitations"])
def test_overclaim_or_missing_restriction_fails_closed(field: str) -> None:
    localized = views()
    localized["ja"] = copy.deepcopy(localized["ja"])
    localized["ja"][field] = []
    with pytest.raises(SemanticParityError, match="mismatch"):
        validate_parity(localized)


@pytest.mark.parametrize("field", ["commands", "paths"])
def test_command_and_path_tokens_must_match_byte_for_byte(field: str) -> None:
    localized = views()
    localized["zh-CN"] = copy.deepcopy(localized["zh-CN"])
    localized["zh-CN"][field] = ["changed"]
    with pytest.raises(SemanticParityError, match="mismatch"):
        validate_parity(localized)


def test_unknown_or_missing_controlled_fields_are_rejected() -> None:
    value = facts()
    value["uncontrolledProse"] = "not comparable"
    with pytest.raises(SemanticParityError, match="unknown"):
        build_projection(value)
    value = facts()
    del value["risks"]
    with pytest.raises(SemanticParityError, match="missing"):
        build_projection(value)
