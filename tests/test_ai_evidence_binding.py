from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.ai_evidence_binding import (
    BindingError,
    build_binding,
    build_content_dependency,
    canonical_digest,
    decide_content_reuse,
    decide_reuse,
    validate_binding,
)

NOW = datetime(2026, 8, 16, 4, 0, tzinfo=UTC)


def dependency_set(classification: str) -> dict[str, object]:
    dependencies: dict[str, object] = {}
    if classification == "content-bound":
        dependencies["content"] = {"digest": "sha256:" + "a" * 64, "paths": ["src/a.py"]}
    elif classification == "diff-bound":
        dependencies["diff"] = {
            "baseCommit": "a" * 40,
            "headCommit": "b" * 40,
            "changedPathsDigest": "sha256:" + "c" * 64,
        }
    else:
        dependencies["environment"] = {
            "digest": "sha256:" + "d" * 64,
            "runtime": "python-3.13",
            "toolchain": "ruff-0.12",
        }
    return dependencies


def binding_for(classification: str) -> dict[str, object]:
    return build_binding(
        subject={"workItemId": "wi-07-evidence-binding-foundation", "evidenceId": "check-quality"},
        classification=classification,
        dependencies=dependency_set(classification),
        scope_digest="sha256:" + "e" * 64,
        governance_digest="sha256:" + "f" * 64,
        producer={"command": "pytest -q", "version": "runner-1"},
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


@pytest.mark.parametrize("classification", ["content-bound", "diff-bound", "environment-bound"])
def test_each_binding_classification_reuses_only_exact_dependencies(classification: str) -> None:
    binding = binding_for(classification)
    current = {
        "dependencies": dependency_set(classification),
        "scopeDigest": "sha256:" + "e" * 64,
        "governanceDigest": "sha256:" + "f" * 64,
    }
    assert decide_reuse(binding, current, now=NOW) == {
        "state": "fresh",
        "action": "reuse",
        "reasons": [],
    }


def test_dependency_mismatch_is_deterministic_rerun_and_does_not_mutate_inputs() -> None:
    binding = binding_for("content-bound")
    current = {
        "dependencies": dependency_set("content-bound"),
        "scopeDigest": "sha256:" + "e" * 64,
        "governanceDigest": "sha256:" + "f" * 64,
    }
    original = deepcopy(current)
    current["dependencies"]["content"]["digest"] = "sha256:" + "1" * 64  # type: ignore[index]
    expected = {"state": "stale", "action": "rerun", "reasons": ["content_dependency_mismatch"]}
    assert decide_reuse(binding, current, now=NOW) == expected
    assert decide_reuse(binding, original, now=NOW) == {
        "state": "fresh",
        "action": "reuse",
        "reasons": [],
    }


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("scopeDigest", "security_scope_mismatch"),
        ("governanceDigest", "governance_policy_mismatch"),
    ],
)
def test_security_and_governance_mismatch_can_never_reuse(field: str, reason: str) -> None:
    binding = binding_for("content-bound")
    current = {
        "dependencies": dependency_set("content-bound"),
        "scopeDigest": "sha256:" + "e" * 64,
        "governanceDigest": "sha256:" + "f" * 64,
    }
    current[field] = "sha256:" + "0" * 64
    result = decide_reuse(binding, current, now=NOW)
    assert result["action"] == "rerun"
    assert result["state"] == "stale"
    assert result["reasons"] == [reason]


def test_unknown_missing_and_expired_inputs_fail_closed() -> None:
    binding = binding_for("environment-bound")
    current = {
        "dependencies": {},
        "scopeDigest": "sha256:" + "e" * 64,
        "governanceDigest": "sha256:" + "f" * 64,
    }
    assert decide_reuse(binding, current, now=NOW) == {
        "state": "unknown",
        "action": "rerun",
        "reasons": ["environment_dependency_unknown"],
    }
    assert decide_reuse(binding, {"dependencies": dependency_set("environment")}, now=NOW) == {
        "state": "unknown",
        "action": "rerun",
        "reasons": ["security_scope_unknown", "governance_policy_unknown"],
    }
    assert decide_reuse(
        binding_for("content-bound"),
        {
            "dependencies": dependency_set("content-bound"),
            "scopeDigest": "sha256:" + "e" * 64,
            "governanceDigest": "sha256:" + "f" * 64,
        },
        now=NOW + timedelta(hours=2),
    ) == {
        "state": "stale",
        "action": "rerun",
        "reasons": ["binding_expired"],
    }


def test_malformed_binding_raises_and_digest_is_canonical() -> None:
    binding = binding_for("content-bound")
    validate_binding(binding)
    malformed = deepcopy(binding)
    malformed["classification"] = "unknown"
    with pytest.raises(BindingError, match="classification"):
        validate_binding(malformed)
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})


def test_schema_declares_version_and_security_dependencies() -> None:
    schema = json.loads(
        Path(".ai/schemas/evidence-binding.schema.json").read_text(encoding="utf-8")
    )
    assert schema["$id"].endswith("evidence-binding.schema.json")
    assert schema["properties"]["schemaVersion"] == {"const": 1}
    assert set(schema["properties"]["classification"]["enum"]) == {
        "content-bound",
        "diff-bound",
        "environment-bound",
    }
    assert {"scopeDigest", "governanceDigest"} <= set(schema["required"])


def test_content_dependency_hashes_exact_bytes_and_is_order_independent() -> None:
    first = build_content_dependency({"src/b.txt": b"b", "src/a.txt": b"a\x00"})
    second = build_content_dependency({"src/a.txt": b"a\x00", "src/b.txt": b"b"})
    assert first == second
    assert first["paths"] == ["src/a.txt", "src/b.txt"]
    assert first["digest"].startswith("sha256:")
    assert build_content_dependency({"src/a.txt": b"a"}) != first


def test_content_policy_reuses_same_bytes_after_unrelated_base_update() -> None:
    dependency = build_content_dependency({"src/a.py": b"return 1\n"})
    binding = build_binding(
        subject={"workItemId": "wi-08-content-bound-reuse-successor", "evidenceId": "quality"},
        classification="content-bound",
        dependencies={"content": dependency},
        scope_digest="sha256:" + "e" * 64,
        governance_digest="sha256:" + "f" * 64,
        producer={"command": "pytest -q", "version": "runner-1"},
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )
    current = {"content": dependency, "baseCommit": "b" * 40}
    assert decide_content_reuse(
        binding,
        current,
        scope_digest=binding["scopeDigest"],
        governance_digest=binding["governanceDigest"],
        now=NOW,
    ) == {"state": "fresh", "action": "reuse", "reasons": []}


def test_content_policy_rejects_changed_or_incomplete_inputs_without_mutation() -> None:
    dependency = build_content_dependency({"src/a.py": b"return 1\n"})
    binding = build_binding(
        subject={"workItemId": "wi-08-content-bound-reuse-successor", "evidenceId": "quality"},
        classification="content-bound",
        dependencies={"content": dependency},
        scope_digest="sha256:" + "e" * 64,
        governance_digest="sha256:" + "f" * 64,
        producer={"command": "pytest -q", "version": "runner-1"},
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )
    current = {"content": {"digest": dependency["digest"], "paths": ["src/a.py", "src/missing.py"]}}
    original = deepcopy(current)
    assert decide_content_reuse(
        binding,
        current,
        scope_digest=binding["scopeDigest"],
        governance_digest=binding["governanceDigest"],
        now=NOW,
    ) == {
        "state": "stale",
        "action": "rerun",
        "reasons": ["content_dependency_mismatch"],
    }
    assert current == original
    assert decide_content_reuse(
        binding,
        {},
        scope_digest=binding["scopeDigest"],
        governance_digest=binding["governanceDigest"],
        now=NOW,
    ) == {"state": "unknown", "action": "rerun", "reasons": ["content_input_unknown"]}


@pytest.mark.parametrize(
    "files",
    [
        {},
        {"/absolute.py": b"x"},
        {"../escape.py": b"x"},
        {"src\\windows.py": b"x"},
        {"src/a.py": "text"},
    ],
)
def test_content_identity_rejects_unsafe_or_non_byte_inputs(files: object) -> None:
    with pytest.raises(BindingError):
        build_content_dependency(files)  # type: ignore[arg-type]


def test_content_policy_rejects_non_content_binding() -> None:
    binding = binding_for("diff-bound")
    assert decide_content_reuse(
        binding,
        {"content": {"digest": "sha256:" + "a" * 64, "paths": ["src/a.py"]}},
        scope_digest=binding["scopeDigest"],
        governance_digest=binding["governanceDigest"],
        now=NOW,
    ) == {
        "state": "unknown",
        "action": "rerun",
        "reasons": ["content_policy_classification_mismatch"],
    }
