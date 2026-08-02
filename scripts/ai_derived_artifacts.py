"""Validate the authority boundary for generated governance artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class RegistryError(ValueError):
    """The declared fact-to-view boundary is malformed or unsafe."""


def canonical_digest(value: Mapping[str, Any]) -> str:
    """Return a reproducible digest for a validated registry."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _records(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise RegistryError(f"{name} must be a non-empty list")
    if not all(isinstance(item, Mapping) for item in value):
        raise RegistryError(f"{name} entries must be objects")
    return [dict(item) for item in value]


def _strings(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise RegistryError(f"{name} must be a list of non-empty strings")
    return list(value)


def validate_registry(value: Mapping[str, Any]) -> None:
    """Fail closed when a generated view could be mistaken for a fact."""
    if value.get("schemaVersion") != 1:
        raise RegistryError("schemaVersion must be 1")
    facts = _records(value.get("facts"), "facts")
    artifacts = _records(value.get("artifacts"), "artifacts")

    fact_ids: set[str] = set()
    fact_paths: set[str] = set()
    for fact in facts:
        identifier, path = fact.get("id"), fact.get("path")
        if not isinstance(identifier, str) or not identifier:
            raise RegistryError("fact id must be a non-empty string")
        if not isinstance(path, str) or not path:
            raise RegistryError("fact path must be a non-empty string")
        if identifier in fact_ids or path in fact_paths:
            raise RegistryError("fact ids and paths must be unique")
        fact_ids.add(identifier)
        fact_paths.add(path)

    artifact_paths: set[str] = set()
    dependencies: dict[str, list[str]] = {}
    for artifact in artifacts:
        path = artifact.get("path")
        if not isinstance(path, str) or not path:
            raise RegistryError("artifact path must be a non-empty string")
        if path in artifact_paths:
            raise RegistryError("artifact paths must be unique")
        artifact_paths.add(path)
        if artifact.get("authority") != "derived":
            raise RegistryError(f"{path} must declare authority 'derived'")
        if not isinstance(artifact.get("generator"), str) or not artifact["generator"]:
            raise RegistryError(f"{path} must declare its generator")
        fact_inputs = _strings(artifact.get("factInputs", []), f"{path}.factInputs")
        if unknown := set(fact_inputs) - fact_ids:
            raise RegistryError(f"{path} references unknown fact inputs: {sorted(unknown)}")
        artifact_inputs = _strings(artifact.get("artifactInputs", []), f"{path}.artifactInputs")
        dependencies[path] = artifact_inputs
        fields = artifact.get("fields")
        if not isinstance(fields, Mapping) or not fields:
            raise RegistryError(f"{path} must map each output field to one authority")
        for field, authority in fields.items():
            if not isinstance(field, str) or not field or not isinstance(authority, str):
                raise RegistryError(f"{path} field authorities must be non-empty strings")
            source_kind, _, source = authority.partition(":")
            source_identifier, separator, _ = source.rpartition(".")
            if not separator:
                raise RegistryError(f"{path}.{field} authority must identify a source field")
            if source_kind == "fact" and source_identifier in fact_inputs:
                continue
            if source_kind == "artifact" and source_identifier in artifact_inputs:
                continue
            raise RegistryError(f"{path}.{field} lacks a declared unique authority")

    conflict = fact_paths & artifact_paths
    if conflict:
        raise RegistryError(f"derived artifact cannot be a fact: {sorted(conflict)}")
    for path, inputs in dependencies.items():
        if unknown := set(inputs) - artifact_paths:
            raise RegistryError(f"{path} references unknown artifact inputs: {sorted(unknown)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(path: str) -> None:
        if path in visiting:
            raise RegistryError(f"derived artifact dependency cycle at {path}")
        if path in visited:
            return
        visiting.add(path)
        for dependency in dependencies[path]:
            visit(dependency)
        visiting.remove(path)
        visited.add(path)

    for path in dependencies:
        visit(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.registry.read_text(encoding="utf-8"))
        if not isinstance(value, Mapping):
            raise RegistryError("registry root must be an object")
        validate_registry(value)
    except (OSError, json.JSONDecodeError, RegistryError) as exc:
        parser.error(str(exc))
    print(canonical_digest(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
