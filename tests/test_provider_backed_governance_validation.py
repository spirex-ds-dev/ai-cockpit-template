"""Regression coverage for the removed Provider-validation boundary."""

from pathlib import Path


def test_provider_validation_is_explicitly_an_external_evidence_boundary() -> None:
    document = Path("docs/reference/provider-backed-governance-validation.md").read_text(
        encoding="utf-8"
    )

    assert "does not include a local collector" in document
    assert "`not_run`, `not_claimed`, or `external_dependency`" in document
    assert "must not claim" in document
