from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest

from scripts.ai_diff_bound_reuse import (
    DiffReuseError,
    build_current_diff,
    canonicalize_changed_paths,
    changed_paths_digest,
    decide_diff_reuse,
)
from scripts.ai_evidence_binding import build_binding

NOW = datetime(2026, 8, 16, 5, 0, tzinfo=UTC)
BASE = "a" * 40
HEAD = "b" * 40
SCOPE = "sha256:" + "c" * 64
POLICY = "sha256:" + "d" * 64
PATHS = ["src/a.py", "tests/test_a.py"]


def diff_binding() -> dict[str, object]:
    return build_binding(
        subject={"workItemId": "wi-09-diff-bound-reuse", "evidenceId": "quality"},
        classification="diff-bound",
        dependencies={
            "diff": {
                "baseCommit": BASE,
                "headCommit": HEAD,
                "changedPathsDigest": changed_paths_digest(PATHS),
            }
        },
        scope_digest=SCOPE,
        governance_digest=POLICY,
        producer={"command": "pytest -q", "version": "runner-1"},
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


def current_diff(**overrides: object) -> dict[str, object]:
    current = build_current_diff(
        base_commit=BASE,
        head_commit=HEAD,
        changed_paths=PATHS,
        scope_digest=SCOPE,
        governance_digest=POLICY,
    )
    current.update(overrides)
    return current


def test_exact_diff_identity_reuses_deterministically() -> None:
    binding = diff_binding()
    current = current_diff()
    assert decide_diff_reuse(binding, current, now=NOW) == {
        "state": "fresh",
        "action": "reuse",
        "reasons": [],
    }
    assert decide_diff_reuse(binding, current, now=NOW) == decide_diff_reuse(
        binding, current, now=NOW
    )


def test_empty_changed_path_set_is_a_valid_clean_diff_identity() -> None:
    binding = build_binding(
        subject={"workItemId": "wi-09-diff-bound-reuse", "evidenceId": "clean"},
        classification="diff-bound",
        dependencies={
            "diff": {
                "baseCommit": BASE,
                "headCommit": HEAD,
                "changedPathsDigest": changed_paths_digest([]),
            }
        },
        scope_digest=SCOPE,
        governance_digest=POLICY,
        producer={"command": "pytest -q", "version": "runner-1"},
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )
    assert decide_diff_reuse(
        binding,
        build_current_diff(
            base_commit=BASE,
            head_commit=HEAD,
            changed_paths=[],
            scope_digest=SCOPE,
            governance_digest=POLICY,
        ),
        now=NOW,
    ) == {"state": "fresh", "action": "reuse", "reasons": []}


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("baseCommit", "e" * 40, "base_commit_mismatch"),
        ("headCommit", "f" * 40, "head_commit_mismatch"),
        ("changedPaths", ["src/added.py"], "changed_paths_mismatch"),
        ("changedPaths", ["src/a.py", "src/renamed.py"], "changed_paths_mismatch"),
        ("scopeDigest", "sha256:" + "e" * 64, "security_scope_mismatch"),
        ("governanceDigest", "sha256:" + "f" * 64, "governance_policy_mismatch"),
    ],
)
def test_any_diff_or_policy_mismatch_requires_rerun(field: str, value: object, reason: str) -> None:
    result = decide_diff_reuse(diff_binding(), current_diff(**{field: value}), now=NOW)
    assert result == {"state": "stale", "action": "rerun", "reasons": [reason]}


def test_changed_path_order_is_canonical_but_duplicates_are_rejected() -> None:
    assert canonicalize_changed_paths(["tests/test_a.py", "src/./a.py"]) == (
        "src/a.py",
        "tests/test_a.py",
    )
    with pytest.raises(DiffReuseError, match="duplicate"):
        canonicalize_changed_paths(["src/a.py", "src/./a.py"])
    with pytest.raises(DiffReuseError, match="repository-relative"):
        canonicalize_changed_paths(["../outside.py"])


@pytest.mark.parametrize(
    "current",
    [
        {},
        {"baseCommit": BASE, "headCommit": HEAD, "changedPaths": PATHS},
        {"baseCommit": "unknown", "headCommit": HEAD, "changedPaths": PATHS},
        {"baseCommit": BASE, "headCommit": HEAD, "changedPaths": ["../outside.py"]},
    ],
)
def test_missing_malformed_or_unknown_current_diff_fails_closed(current: dict[str, object]) -> None:
    result = decide_diff_reuse(diff_binding(), current, now=NOW)
    assert result["state"] == "unknown"
    assert result["action"] == "rerun"
    assert result["reasons"]


def test_expired_binding_requires_rerun() -> None:
    assert decide_diff_reuse(diff_binding(), current_diff(), now=NOW + timedelta(hours=2)) == {
        "state": "stale",
        "action": "rerun",
        "reasons": ["binding_expired"],
    }


@pytest.mark.parametrize("field", ["scopeDigest", "governanceDigest"])
def test_missing_scope_or_governance_is_unknown_not_reusable(field: str) -> None:
    current = current_diff()
    del current[field]
    result = decide_diff_reuse(diff_binding(), current, now=NOW)
    assert result == {
        "state": "unknown",
        "action": "rerun",
        "reasons": [
            "security_scope_unknown" if field == "scopeDigest" else "governance_policy_unknown"
        ],
    }


def test_decision_does_not_mutate_binding_or_current_inputs() -> None:
    binding = diff_binding()
    current = current_diff()
    binding_before = deepcopy(binding)
    current_before = deepcopy(current)
    decide_diff_reuse(binding, current, now=NOW)
    assert binding == binding_before
    assert current == current_before
