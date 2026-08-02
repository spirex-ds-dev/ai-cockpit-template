from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ai_derived_artifacts import RegistryError, canonical_digest, validate_registry

ROOT = Path(__file__).resolve().parents[1]


def registry() -> dict:
    return json.loads((ROOT / ".ai/cockpit/derived_artifacts.json").read_text())


def by_path(value: dict) -> dict[str, dict]:
    return {item["path"]: item for item in value["artifacts"]}


def test_repository_registry_declares_non_authoritative_generated_views() -> None:
    value = registry()
    validate_registry(value)
    artifacts = by_path(value)
    assert artifacts[".ai/cockpit/current_status.md"]["authority"] == "derived"
    assert artifacts[".ai/cockpit/task_report.json"]["authority"] == "derived"
    assert artifacts[".ai/cockpit/task_report.md"]["artifactInputs"] == [
        ".ai/cockpit/task_report.json"
    ]


def test_registry_rejects_derived_as_fact_and_cycles() -> None:
    value = registry()
    value["facts"].append({"id": "incorrect_status_fact", "path": ".ai/cockpit/current_status.md"})
    with pytest.raises(RegistryError, match="derived artifact cannot be a fact"):
        validate_registry(value)

    value = registry()
    artifacts = by_path(value)
    artifacts[".ai/cockpit/task_report.json"]["artifactInputs"] = [".ai/cockpit/task_report.md"]
    with pytest.raises(RegistryError, match="cycle"):
        validate_registry(value)


def test_canonical_registry_digest_is_deterministic() -> None:
    value = registry()
    assert canonical_digest(value) == canonical_digest(json.loads(json.dumps(value)))
