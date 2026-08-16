"""Versioned, fail-closed evidence binding primitives.

This module deliberately decides only whether a binding is fresh enough to be
considered by a later policy.  It does not run checks, manage a cache, or grant
permission to bypass security, scope, governance, or required-check gates.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

SCHEMA_VERSION = 1
CLASSIFICATIONS = ("content-bound", "diff-bound", "environment-bound")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_FIELDS = {
    "format",
    "schemaVersion",
    "bindingId",
    "subject",
    "classification",
    "dependencies",
    "scopeDigest",
    "governanceDigest",
    "producer",
    "createdAt",
    "expiresAt",
}
_DEPENDENCY_FIELD = {
    "content-bound": "content",
    "diff-bound": "diff",
    "environment-bound": "environment",
}


class BindingError(ValueError):
    """Raised when a binding cannot be trusted as a versioned evidence record."""


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as exc:
        raise BindingError("binding contains non-canonical data") from exc


def canonical_digest(value: object) -> str:
    """Return a stable ``sha256:`` digest for JSON-compatible data."""

    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise BindingError("timestamp must include a timezone")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise BindingError(f"{field} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise BindingError(f"{field} must be an ISO-8601 string") from exc
    if parsed.tzinfo is None:
        raise BindingError(f"{field} must include a timezone")
    return parsed.astimezone(UTC)


def _require_digest(value: object, field: str) -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise BindingError(f"{field} must be a sha256 digest")


def _require_string(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise BindingError(f"{field} must be a non-empty string")


def _validate_dependency(classification: str, dependencies: object) -> None:
    if not isinstance(dependencies, Mapping):
        raise BindingError("dependencies must be an object")
    expected = _DEPENDENCY_FIELD[classification]
    if set(dependencies) != {expected}:
        raise BindingError(f"dependencies must contain only {expected}")
    value = dependencies[expected]
    if not isinstance(value, Mapping):
        raise BindingError(f"{expected} dependency must be an object")
    if classification == "content-bound":
        if set(value) != {"digest", "paths"}:
            raise BindingError("content dependency requires digest and paths")
        _require_digest(value.get("digest"), "content.digest")
        paths = value.get("paths")
        if (
            not isinstance(paths, list)
            or not paths
            or any(not isinstance(path, str) or not path for path in paths)
            or paths != sorted(set(paths))
        ):
            raise BindingError("content.paths must be a sorted non-empty list")
    elif classification == "diff-bound":
        if set(value) != {"baseCommit", "headCommit", "changedPathsDigest"}:
            raise BindingError(
                "diff dependency requires baseCommit, headCommit, and changedPathsDigest"
            )
        for field in ("baseCommit", "headCommit"):
            if not isinstance(value.get(field), str) or not _COMMIT.fullmatch(value[field]):
                raise BindingError(f"diff.{field} must be a 40-character commit")
        _require_digest(value.get("changedPathsDigest"), "diff.changedPathsDigest")
    else:
        if set(value) != {"digest", "runtime", "toolchain"}:
            raise BindingError("environment dependency requires digest, runtime, and toolchain")
        _require_digest(value.get("digest"), "environment.digest")
        _require_string(value.get("runtime"), "environment.runtime")
        _require_string(value.get("toolchain"), "environment.toolchain")


def _binding_payload(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {key: binding[key] for key in sorted(binding) if key != "bindingId"}


def validate_binding(binding: Mapping[str, Any]) -> None:
    """Validate a binding and its content-addressed identity.

    ``BindingError`` is intentionally strict.  Callers deciding whether to
    reuse evidence should use :func:`decide_reuse`, which converts this error
    into an explicit Unknown-to-rerun decision.
    """

    if not isinstance(binding, Mapping):
        raise BindingError("binding must be an object")
    if set(binding) != _REQUIRED_FIELDS:
        missing = sorted(_REQUIRED_FIELDS - set(binding))
        extra = sorted(set(binding) - _REQUIRED_FIELDS)
        detail = f"missing {', '.join(missing)}" if missing else f"unsupported {', '.join(extra)}"
        raise BindingError(f"binding fields invalid: {detail}")
    if binding["format"] != "ai-cockpit-evidence-binding":
        raise BindingError("binding format is invalid")
    if binding["schemaVersion"] != SCHEMA_VERSION:
        raise BindingError("binding schemaVersion is unsupported")
    if not isinstance(binding["bindingId"], str) or not _DIGEST.fullmatch(binding["bindingId"]):
        raise BindingError("bindingId must be a sha256 digest")
    subject = binding["subject"]
    if not isinstance(subject, Mapping) or set(subject) != {"workItemId", "evidenceId"}:
        raise BindingError("subject requires workItemId and evidenceId")
    _require_string(subject.get("workItemId"), "subject.workItemId")
    _require_string(subject.get("evidenceId"), "subject.evidenceId")
    classification = binding["classification"]
    if classification not in CLASSIFICATIONS:
        raise BindingError("classification is invalid")
    _validate_dependency(classification, binding["dependencies"])
    _require_digest(binding["scopeDigest"], "scopeDigest")
    _require_digest(binding["governanceDigest"], "governanceDigest")
    producer = binding["producer"]
    if not isinstance(producer, Mapping) or set(producer) != {"command", "version"}:
        raise BindingError("producer requires command and version")
    _require_string(producer.get("command"), "producer.command")
    _require_string(producer.get("version"), "producer.version")
    created = _parse_timestamp(binding["createdAt"], "createdAt")
    expires = _parse_timestamp(binding["expiresAt"], "expiresAt")
    if expires < created:
        raise BindingError("expiresAt must not precede createdAt")
    if canonical_digest(_binding_payload(binding)) != binding["bindingId"]:
        raise BindingError("bindingId does not match binding content")


def build_binding(
    *,
    subject: Mapping[str, str],
    classification: str,
    dependencies: Mapping[str, Any],
    scope_digest: str,
    governance_digest: str,
    producer: Mapping[str, str],
    created_at: datetime,
    expires_at: datetime,
) -> dict[str, Any]:
    """Build and validate an immutable-in-practice binding record."""

    if classification not in CLASSIFICATIONS:
        raise BindingError("classification is invalid")
    normalized_subject = {key: subject[key] for key in sorted(subject)}
    normalized_dependencies = json.loads(json.dumps(dependencies, sort_keys=True))
    if classification == "content-bound":
        content = normalized_dependencies.get("content")
        if isinstance(content, dict) and isinstance(content.get("paths"), list):
            content["paths"] = sorted(set(content["paths"]))
    payload: dict[str, Any] = {
        "format": "ai-cockpit-evidence-binding",
        "schemaVersion": SCHEMA_VERSION,
        "subject": normalized_subject,
        "classification": classification,
        "dependencies": normalized_dependencies,
        "scopeDigest": scope_digest,
        "governanceDigest": governance_digest,
        "producer": {key: producer[key] for key in sorted(producer)},
        "createdAt": _iso(created_at),
        "expiresAt": _iso(expires_at),
    }
    payload["bindingId"] = canonical_digest(payload)
    result = {
        key: payload[key]
        for key in [
            "format",
            "schemaVersion",
            "bindingId",
            "subject",
            "classification",
            "dependencies",
            "scopeDigest",
            "governanceDigest",
            "producer",
            "createdAt",
            "expiresAt",
        ]
    }
    validate_binding(result)
    return result


def _known(value: object) -> bool:
    if value is None or value == "" or value == {} or value == []:
        return False
    return not (
        isinstance(value, str) and value.strip().lower() in {"unknown", "n/a", "not_configured"}
    )


def decide_reuse(
    binding: Mapping[str, Any], current: Mapping[str, Any], *, now: datetime
) -> dict[str, Any]:
    """Return a deterministic ``reuse`` or fail-closed ``rerun`` decision.

    The returned shape is intentionally data-only so later policy Work Items
    can record it without granting this module execution authority.
    """

    try:
        validate_binding(binding)
    except BindingError:
        return {"state": "unknown", "action": "rerun", "reasons": ["binding_invalid"]}
    if now.tzinfo is None:
        return {"state": "unknown", "action": "rerun", "reasons": ["current_time_unknown"]}
    reasons: list[str] = []
    unknown_reasons: list[str] = []
    classification = binding["classification"]
    dependency_name = _DEPENDENCY_FIELD[classification]
    if not isinstance(current, Mapping):
        return {"state": "unknown", "action": "rerun", "reasons": ["current_dependencies_unknown"]}
    current_dependencies = current.get("dependencies")
    bound_dependencies = binding["dependencies"]
    current_value = (
        current_dependencies.get(dependency_name)
        if isinstance(current_dependencies, Mapping)
        else None
    )
    if not _known(current_value):
        unknown_reasons.append(f"{dependency_name}_dependency_unknown")
    elif current_value != bound_dependencies[dependency_name]:
        reasons.append(f"{dependency_name}_dependency_mismatch")
    for field, reason in (
        ("scopeDigest", "security_scope"),
        ("governanceDigest", "governance_policy"),
    ):
        value = current.get(field)
        if not _known(value):
            unknown_reasons.append(f"{reason}_unknown")
        elif value != binding[field]:
            reasons.append(f"{reason}_mismatch")
    expires = _parse_timestamp(binding["expiresAt"], "expiresAt")
    if now.astimezone(UTC) > expires:
        reasons.append("binding_expired")
    if unknown_reasons:
        return {"state": "unknown", "action": "rerun", "reasons": unknown_reasons + reasons}
    if reasons:
        return {"state": "stale", "action": "rerun", "reasons": reasons}
    return {"state": "fresh", "action": "reuse", "reasons": []}
