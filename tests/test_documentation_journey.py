"""Tests for reader-criticality and localized documentation journeys."""

import json
import subprocess
import sys
from pathlib import Path

from scripts.ai_documentation_journey import planned_gaps, validate_journeys, validate_topics


def topic_registry(*, status: str = "active", root: Path | None = None) -> dict[str, object]:
    return {
        "schema": "ai-cockpit-documentation-authority",
        "schemaVersion": 2,
        "documents": [],
        "topics": [
            {
                "topic": "product-architecture",
                "criticality": "P0",
                "canonicalPath": "docs/architecture.md",
                "localizedPaths": {
                    "en": "docs/architecture.md",
                    "ja": "docs/architecture.ja.md",
                    "zh-CN": "docs/architecture.zh-CN.md",
                },
                "audiences": ["adopter"],
                "journeys": ["understand"],
                "nextTopics": [],
                "enforcementStatus": status,
                "plainLanguageRequired": True,
                "semanticInvariants": ["external-controls-remain-external"],
            }
        ],
    }


def test_active_p0_requires_existing_localized_files(tmp_path: Path) -> None:
    errors = validate_topics(topic_registry(), tmp_path)
    assert "product-architecture: en path does not exist: docs/architecture.md" in errors


def test_planned_p0_exposes_missing_locales_without_blocking(tmp_path: Path) -> None:
    registry = topic_registry(status="planned")
    assert validate_topics(registry, tmp_path) == []
    assert planned_gaps(registry, tmp_path)[0] == {
        "topic": "product-architecture",
        "locale": "en",
        "path": "docs/architecture.md",
        "reason": "path does not exist",
    }


def test_journey_rejects_archived_route_and_requires_same_language(tmp_path: Path) -> None:
    registry = topic_registry(status="active")
    for path in registry["topics"][0]["localizedPaths"].values():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Architecture\n", encoding="utf-8")
    registry["topics"][0]["nextTopics"] = ["missing-topic"]
    errors = validate_journeys(registry, tmp_path)
    assert "product-architecture: next topic does not exist: missing-topic" in errors


def test_active_topic_cannot_be_downgraded_to_planned(tmp_path: Path) -> None:
    registry = topic_registry(status="planned")
    registry["topics"][0]["previousEnforcementStatus"] = "active"
    errors = validate_topics(registry, tmp_path)
    assert "product-architecture: active topics cannot be downgraded to planned" in errors


def test_topic_validator_reports_malformed_topic_fields(tmp_path: Path) -> None:
    registry = topic_registry(status="planned")
    topic = registry["topics"][0]
    topic["criticality"] = "P3"
    topic["canonicalPath"] = ""
    topic["localizedPaths"] = {"xx": "docs/architecture.xx.md"}
    topic["enforcementStatus"] = "paused"
    errors = validate_topics(registry, tmp_path)
    assert any("invalid criticality" in error for error in errors)
    assert any("canonicalPath is required" in error for error in errors)
    assert any("invalid locale: xx" in error for error in errors)
    assert any("invalid enforcementStatus" in error for error in errors)


def test_journey_validator_rejects_non_list_next_topics(tmp_path: Path) -> None:
    registry = topic_registry(status="planned")
    registry["topics"][0]["nextTopics"] = "not-a-list"
    assert validate_journeys(registry, tmp_path) == [
        "product-architecture: nextTopics must be a list"
    ]


def test_journey_cli_accepts_valid_registry(tmp_path: Path) -> None:
    registry = topic_registry(status="planned")
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ai_documentation_journey.py",
            "--registry",
            str(registry_path),
            "--root",
            str(tmp_path),
            "--check",
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "documentation journey check passed" in result.stdout
