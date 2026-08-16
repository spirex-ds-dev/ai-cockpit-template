from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.ai_environment_reuse import (
    EnvironmentReuseError,
    build_environment_binding,
    build_environment_snapshot,
    current_environment,
    decide_environment_reuse,
    environment_dependency,
    environment_fingerprint,
)

NOW = datetime(2026, 8, 16, 4, 30, tzinfo=UTC)
SCOPE = "sha256:" + "a" * 64
GOVERNANCE = "sha256:" + "b" * 64


def snapshot(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "runtime": "python-3.14.4",
        "toolchain": {"python": "3.14.4", "runner": "pytest-9.1.1"},
        "environment": {"os": "darwin", "architecture": "arm64"},
    }
    values.update(overrides)
    return build_environment_snapshot(**values)  # type: ignore[arg-type]


def binding_for(
    value: dict[str, object],
    *,
    created_at: datetime = NOW,
    expires_at: datetime | None = None,
) -> dict[str, object]:
    return build_environment_binding(
        subject={"workItemId": "wi-10-environment-bound-reuse-successor", "evidenceId": "quality"},
        environment=value,
        scope_digest=SCOPE,
        governance_digest=GOVERNANCE,
        producer={"command": "pytest -q", "version": "runner-1"},
        created_at=created_at,
        expires_at=expires_at or NOW + timedelta(hours=1),
    )


def test_fingerprint_is_canonical_and_snapshot_does_not_mutate_inputs() -> None:
    toolchain = {"runner": "pytest-9.1.1", "python": "3.14.4"}
    environment = {"architecture": "arm64", "os": "darwin"}
    original_toolchain = deepcopy(toolchain)
    original_environment = deepcopy(environment)
    first = build_environment_snapshot(
        runtime="python-3.14.4", toolchain=toolchain, environment=environment
    )
    second = build_environment_snapshot(
        runtime="python-3.14.4",
        toolchain={"python": "3.14.4", "runner": "pytest-9.1.1"},
        environment={"os": "darwin", "architecture": "arm64"},
    )
    assert first["fingerprint"] == second["fingerprint"]
    assert first["fingerprint"] == environment_fingerprint(
        runtime="python-3.14.4", toolchain=toolchain, environment=environment
    )
    assert toolchain == original_toolchain
    assert environment == original_environment


def test_environment_binding_reuses_an_exact_current_snapshot() -> None:
    value = snapshot()
    binding = binding_for(value)
    assert decide_environment_reuse(
        binding, value, scope_digest=SCOPE, governance_digest=GOVERNANCE, now=NOW
    ) == {"state": "fresh", "action": "reuse", "reasons": []}
    assert environment_dependency(value)["environment"]["digest"] == value["fingerprint"]  # type: ignore[index]


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("runtime", "python-3.13.0"),
        ("toolchain", {"python": "3.14.4", "runner": "pytest-9.2.0"}),
        ("environment", {"os": "linux", "architecture": "x86_64"}),
    ],
)
def test_environment_identity_mismatch_requires_rerun(field: str, changed: object) -> None:
    original = snapshot()
    binding = binding_for(original)
    current = snapshot(**{field: changed})
    result = decide_environment_reuse(
        binding, current, scope_digest=SCOPE, governance_digest=GOVERNANCE, now=NOW
    )
    assert result == {
        "state": "stale",
        "action": "rerun",
        "reasons": ["environment_dependency_mismatch"],
    }


def test_unknown_malformed_expired_and_policy_mismatch_fail_closed() -> None:
    value = snapshot()
    binding = binding_for(
        value,
        created_at=NOW - timedelta(hours=1),
        expires_at=NOW - timedelta(seconds=1),
    )
    assert decide_environment_reuse(
        binding, None, scope_digest=SCOPE, governance_digest=GOVERNANCE, now=NOW
    ) == {
        "state": "unknown",
        "action": "rerun",
        "reasons": ["environment_snapshot_unknown"],
    }
    assert decide_environment_reuse(
        binding, {}, scope_digest=SCOPE, governance_digest=GOVERNANCE, now=NOW
    ) == {
        "state": "unknown",
        "action": "rerun",
        "reasons": ["environment_snapshot_invalid"],
    }
    assert decide_environment_reuse(
        binding_for(value), value, scope_digest=None, governance_digest=GOVERNANCE, now=NOW
    ) == {
        "state": "unknown",
        "action": "rerun",
        "reasons": ["security_scope_unknown"],
    }
    expired = decide_environment_reuse(
        binding_for(
            value,
            created_at=NOW - timedelta(hours=1),
            expires_at=NOW - timedelta(seconds=1),
        ),
        value,
        scope_digest=SCOPE,
        governance_digest=GOVERNANCE,
        now=NOW,
    )
    assert expired == {"state": "stale", "action": "rerun", "reasons": ["binding_expired"]}


def test_secret_like_metadata_is_rejected_and_schema_dependency_shape_is_reused() -> None:
    with pytest.raises(EnvironmentReuseError, match="secret-like"):
        build_environment_snapshot(
            runtime="python-3.14.4",
            toolchain={"runner": "pytest", "api_token": "do-not-read"},
            environment={"os": "darwin"},
        )
    schema = json.loads(
        Path(".ai/schemas/evidence-binding.schema.json").read_text(encoding="utf-8")
    )
    assert schema["properties"]["classification"]["enum"] == [
        "content-bound",
        "diff-bound",
        "environment-bound",
    ]
    assert set(schema["$defs"]["environmentDependency"]["required"]) == {
        "digest",
        "runtime",
        "toolchain",
    }


def test_current_environment_uses_an_allowlist() -> None:
    value = current_environment(toolchain={"runner": "pytest-9.1.1"})
    assert set(value) == {"runtime", "toolchain", "environment", "fingerprint"}
    assert "token" not in json.dumps(value).lower()
