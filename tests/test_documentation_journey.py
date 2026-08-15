"""Tests for reader-criticality and localized documentation journeys."""

import json
import subprocess
import sys
from pathlib import Path

from scripts.ai_documentation_journey import (
    planned_gaps,
    topic_index,
    validate_journeys,
    validate_topics,
)


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


def test_entry_pages_state_current_p1_p2_fallback_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    english = (root / "docs/README.md").read_text(encoding="utf-8")
    chinese = (root / "docs/README.zh-CN.md").read_text(encoding="utf-8")
    japanese = (root / "docs/README.ja.md").read_text(encoding="utf-8")

    assert "active P1 technical references for commands" in english
    assert "active P2 documentation" in english
    assert "not evidence that all documentation has complete multilingual" in english
    assert "P1 的 commands 和 schemas 技术参考目前只有英文" in chinese
    assert "P2 的文档权威边界参考默认不要求翻译" in chinese
    assert "不能据此宣称全部文档已经完成多语言覆盖" in chinese
    assert "P1 の" in japanese and "schemas" in japanese
    assert "P2 の" in japanese and "既定では翻訳対象外" in japanese
    assert "すべてのドキュメントの多言語対応が完了したことを意味しません" in japanese


def test_topic_index_ignores_malformed_entries() -> None:
    assert topic_index({"topics": [None, {"topic": "valid"}, {"topic": 3}]}) == {
        "valid": {"topic": "valid"}
    }


def test_planned_non_p0_topic_reports_only_declared_locale_gap(tmp_path: Path) -> None:
    registry = {
        "topics": [
            {
                "topic": "reference",
                "criticality": "P1",
                "enforcementStatus": "planned",
                "localizedPaths": {"en": "docs/reference.md"},
            }
        ]
    }
    assert planned_gaps(registry, tmp_path) == [
        {
            "topic": "reference",
            "locale": "en",
            "path": "docs/reference.md",
            "reason": "path does not exist",
        }
    ]


def test_active_p1_english_fallback_requires_explicit_label(tmp_path: Path) -> None:
    registry = {
        "topics": [
            {
                "topic": "commands",
                "criticality": "P1",
                "canonicalPath": "docs/reference/commands.md",
                "localizedPaths": {"en": "docs/reference/commands.md"},
                "enforcementStatus": "active",
                "localizationPolicy": "english-fallback-labelled",
            }
        ]
    }
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / "docs/reference/commands.md").write_text("# Commands\n", encoding="utf-8")
    assert validate_topics(registry, tmp_path) == [
        "commands: P1 English fallback requires fallbackLabel"
    ]


def test_active_p1_fallback_label_and_p2_default_policy_pass(tmp_path: Path) -> None:
    registry = {
        "topics": [
            {
                "topic": "commands",
                "criticality": "P1",
                "canonicalPath": "docs/reference/commands.md",
                "localizedPaths": {"en": "docs/reference/commands.md"},
                "enforcementStatus": "active",
                "localizationPolicy": "english-fallback-labelled",
                "fallbackLabel": "Detailed technical reference — English",
            },
            {
                "topic": "audit-reference",
                "criticality": "P2",
                "canonicalPath": "docs/reference/audit.md",
                "localizedPaths": {"en": "docs/reference/audit.md"},
                "enforcementStatus": "active",
                "localizationPolicy": "not-required-by-default",
            },
        ]
    }
    for path in ("docs/reference/commands.md", "docs/reference/audit.md"):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Reference\n", encoding="utf-8")
    assert validate_topics(registry, tmp_path) == []


def test_p2_cannot_claim_p1_fallback_policy(tmp_path: Path) -> None:
    registry = {
        "topics": [
            {
                "topic": "audit-reference",
                "criticality": "P2",
                "canonicalPath": "docs/reference/audit.md",
                "localizedPaths": {"en": "docs/reference/audit.md"},
                "enforcementStatus": "active",
                "localizationPolicy": "english-fallback-labelled",
                "fallbackLabel": "Detailed technical reference — English",
            }
        ]
    }
    target = tmp_path / "docs/reference/audit.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Audit\n", encoding="utf-8")
    assert validate_topics(registry, tmp_path) == [
        "audit-reference: P2 cannot use the P1 English fallback policy"
    ]


def test_topic_validator_reports_duplicate_and_missing_p0_locale(tmp_path: Path) -> None:
    registry = topic_registry(status="planned")
    duplicate = dict(registry["topics"][0])
    duplicate["topic"] = "second"
    duplicate["canonicalPath"] = registry["topics"][0]["canonicalPath"]
    duplicate["localizedPaths"] = {"en": "docs/architecture.md"}
    registry["topics"].extend([duplicate, "malformed"])
    errors = validate_topics(registry, tmp_path)
    assert "second: canonicalPath already owned by product-architecture" in errors
    assert "second: missing P0 locale: ja" in errors
    assert "second: missing P0 locale: zh-CN" in errors
    assert "topic 2 must be an object" in errors
