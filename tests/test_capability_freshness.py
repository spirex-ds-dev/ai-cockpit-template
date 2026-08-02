"""Regression coverage for time- and environment-bound capability evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ai_capability_freshness import current_environment, evaluate_freshness, make_record


def test_current_environment_omits_host_os_for_portable_repository_evidence() -> None:
    environment = current_environment()
    record = make_record(
        environment=environment, scope=["source.py"], now=datetime(2026, 8, 2, tzinfo=UTC)
    )

    assert "os" not in environment
    assert evaluate_freshness(
        record, environment=current_environment(), now=datetime(2026, 8, 3, tzinfo=UTC)
    ) == {"state": "fresh", "reasons": []}


def test_matching_unexpired_record_is_fresh() -> None:
    environment = {
        "os": "test-os",
        "runtime": "python-3",
        "toolVersions": ["ruff-1"],
        "provider": "not_configured",
    }
    record = make_record(
        environment=environment, scope=["source.py"], now=datetime(2026, 8, 2, tzinfo=UTC)
    )

    assert evaluate_freshness(
        record, environment=environment, now=datetime(2026, 8, 3, tzinfo=UTC)
    ) == {"state": "fresh", "reasons": []}


def test_expired_or_environment_mismatch_is_stale() -> None:
    environment = {
        "os": "test-os",
        "runtime": "python-3",
        "toolVersions": ["ruff-1"],
        "provider": "not_configured",
    }
    record = make_record(
        environment=environment,
        scope=["source.py"],
        now=datetime(2026, 8, 2, tzinfo=UTC),
        ttl=timedelta(days=1),
    )

    expired = evaluate_freshness(
        record, environment=environment, now=datetime(2026, 8, 4, tzinfo=UTC)
    )
    changed = evaluate_freshness(
        record,
        environment={**environment, "runtime": "python-4"},
        now=datetime(2026, 8, 2, tzinfo=UTC),
    )

    assert expired == {"state": "stale", "reasons": ["valid_until_expired"]}
    assert changed == {"state": "stale", "reasons": ["environment_mismatch"]}


def test_reverification_restores_stale_record_to_fresh() -> None:
    environment = {
        "os": "test-os",
        "runtime": "python-3",
        "toolVersions": ["ruff-1"],
        "provider": "not_configured",
    }
    stale = make_record(
        environment=environment,
        scope=["source.py"],
        now=datetime(2026, 8, 1, tzinfo=UTC),
        ttl=timedelta(days=1),
    )
    refreshed = make_record(
        environment=environment, scope=["source.py"], now=datetime(2026, 8, 3, tzinfo=UTC)
    )

    assert (
        evaluate_freshness(stale, environment=environment, now=datetime(2026, 8, 3, tzinfo=UTC))[
            "state"
        ]
        == "stale"
    )
    assert (
        evaluate_freshness(
            refreshed, environment=environment, now=datetime(2026, 8, 3, tzinfo=UTC)
        )["state"]
        == "fresh"
    )
