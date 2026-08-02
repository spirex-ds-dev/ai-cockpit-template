"""Fail-closed parity checks for controlled multilingual governance semantics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

CONTROLLED_FIELDS = (
    "status",
    "prohibitedClaims",
    "safetyBoundaries",
    "humanDecisions",
    "risks",
    "limitations",
    "commands",
    "paths",
    "capabilityClaims",
)


class SemanticParityError(ValueError):
    """A localized view changes a controlled governance fact."""


@dataclass(frozen=True)
class SemanticProjection:
    """Language-neutral, controlled facts extracted before localized rendering."""

    values: tuple[tuple[str, tuple[str, ...]], ...]


def _normalized_values(value: Any, field: str) -> tuple[str, ...]:
    if field == "status":
        if not isinstance(value, str) or not value.strip():
            raise SemanticParityError("status must be a non-empty string")
        return (value.strip(),)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise SemanticParityError(f"{field} must be a list of non-empty strings")
    values = tuple(
        sorted({item.strip() for item in value if isinstance(item, str) and item.strip()})
    )
    if len(values) != len(value):
        raise SemanticParityError(f"{field} must be a list of unique non-empty strings")
    return values


def build_projection(facts: Mapping[str, Any]) -> SemanticProjection:
    """Normalize exactly the governance facts that must survive localization."""
    unknown = set(facts) - set(CONTROLLED_FIELDS)
    missing = set(CONTROLLED_FIELDS) - set(facts)
    if unknown:
        raise SemanticParityError(f"unknown controlled semantic fields: {sorted(unknown)}")
    if missing:
        raise SemanticParityError(f"missing controlled semantic fields: {sorted(missing)}")
    return SemanticProjection(
        tuple((field, _normalized_values(facts[field], field)) for field in CONTROLLED_FIELDS)
    )


def validate_parity(localized: Mapping[str, Mapping[str, Any]]) -> SemanticProjection:
    """Require English, Japanese, and Chinese views to expose identical facts."""
    required = {"en", "ja", "zh-CN"}
    if set(localized) != required:
        raise SemanticParityError(f"localized views must be exactly {sorted(required)}")
    projections = {locale: build_projection(facts) for locale, facts in localized.items()}
    baseline = projections["en"]
    for locale, projection in projections.items():
        if projection != baseline:
            raise SemanticParityError(f"controlled semantic mismatch: en != {locale}")
    return baseline
