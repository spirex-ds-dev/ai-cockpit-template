"""Validate and query the bounded documentation authority registry.

The registry is an explicit routing policy for agents. It is not a document
scanner and never changes governance or documentation state while queried.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = PROJECT_ROOT / "docs/reference/documentation-authority-registry.json"
AUTHORITIES = {"canonical", "reference", "historical"}
STATUSES = {"current", "deprecated", "archived"}


def validate_registry(registry: object) -> list[str]:
    """Return stable validation errors for one authority registry mapping."""

    if not isinstance(registry, Mapping):
        return ["registry must be an object"]
    errors: list[str] = []
    if registry.get("schema") != "ai-cockpit-documentation-authority":
        errors.append("registry schema must be ai-cockpit-documentation-authority")
    schema_version = registry.get("schemaVersion")
    if schema_version not in {1, 2}:
        errors.append("registry schemaVersion must be 1 or 2")
    documents = registry.get("documents")
    if not isinstance(documents, list):
        return [*errors, "registry documents must be a list"]
    topics = registry.get("topics")
    if schema_version == 2 and not isinstance(topics, list):
        errors.append("registry topics must be a list for schemaVersion 2")
    if schema_version == 1 and "topics" in registry:
        errors.append("registry topics is only valid for schemaVersion 2")

    canonical_topics: dict[str, int] = {}
    paths: set[str] = set()
    for index, item in enumerate(documents):
        if not isinstance(item, Mapping):
            errors.append(f"document {index} must be an object")
            continue
        topic = item.get("topic")
        path = item.get("path")
        authority = item.get("authority")
        instructional = item.get("instructional")
        status = item.get("status")
        superseded_by = item.get("supersededBy")
        if not isinstance(topic, str) or not topic:
            errors.append(f"document {index} requires topic")
        if not isinstance(path, str) or not path:
            errors.append(f"document {index} requires path")
            continue
        if path in paths:
            errors.append(f"documentation path is duplicated: {path}")
        paths.add(path)
        if authority not in AUTHORITIES:
            errors.append(f"{path}: invalid authority")
        if not isinstance(instructional, bool):
            errors.append(f"{path}: instructional must be boolean")
        if status not in STATUSES:
            errors.append(f"{path}: invalid status")
        if superseded_by is not None and (not isinstance(superseded_by, str) or not superseded_by):
            errors.append(f"{path}: supersededBy must be null or a non-empty path")
        if authority == "canonical":
            if not path.startswith("docs/current/"):
                errors.append(f"{path}: canonical documents must be under docs/current")
            if instructional is not True or status != "current":
                errors.append(
                    f"{path}: canonical documents must be current instructional documents"
                )
            if isinstance(topic, str) and topic:
                canonical_topics[topic] = canonical_topics.get(topic, 0) + 1
        elif authority == "reference" and not path.startswith("docs/reference/"):
            errors.append(f"{path}: reference documents must be under docs/reference")
        elif authority == "historical":
            if not path.startswith("docs/archive/"):
                errors.append(f"{path}: historical documents must be under docs/archive")
            if instructional is True:
                errors.append(f"{path}: historical documents cannot be instructional")
            if status == "current":
                errors.append(f"{path}: historical documents cannot have current status")
    for topic, count in sorted(canonical_topics.items()):
        if count > 1:
            errors.append(f"topic {topic} has multiple canonical documents")
    return errors


def query_records(
    registry: Mapping[str, Any], *, include_reference: bool = False
) -> list[dict[str, Any]]:
    """Return the explicit default or opt-in read set without mutating input."""

    documents = registry.get("documents")
    if not isinstance(documents, list):
        raise TypeError("registry documents must be a list")
    selected: list[dict[str, Any]] = []
    for item in documents:
        if not isinstance(item, Mapping):
            continue
        authority = item.get("authority")
        if authority == "canonical" or (include_reference and authority == "reference"):
            selected.append(dict(item))
    return selected


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    """Load a registry and fail before returning invalid policy data."""

    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load registry: {exc}") from exc
    errors = validate_registry(registry)
    if errors:
        raise ValueError("; ".join(errors))
    return dict(registry)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--include-reference", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args()
    try:
        registry = load_registry(args.registry)
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": {"code": "invalid_registry", "message": str(exc)}}))
        return 2
    if args.check:
        print(f"documentation authority registry check passed: {args.registry}")
        return 0
    print(
        json.dumps(
            {
                "ok": True,
                "data": query_records(registry, include_reference=args.include_reference),
                "error": None,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
