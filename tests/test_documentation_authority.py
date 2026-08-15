"""Focused tests for the documentation authority read boundary."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ai_documentation_authority import load_registry, query_records, validate_registry


def v1_registry() -> dict[str, object]:
    return {
        "schema": "ai-cockpit-documentation-authority",
        "schemaVersion": 1,
        "documents": [
            {
                "topic": "agent-reading",
                "path": "docs/current/README.md",
                "authority": "canonical",
                "instructional": True,
                "status": "current",
                "supersededBy": None,
            },
            {
                "topic": "agent-reading-reference",
                "path": "docs/reference/documentation-authority-boundary.md",
                "authority": "reference",
                "instructional": False,
                "status": "current",
                "supersededBy": None,
            },
            {
                "topic": "old-plan",
                "path": "docs/archive/plans/README.md",
                "authority": "historical",
                "instructional": False,
                "status": "archived",
                "supersededBy": "docs/current/README.md",
            },
        ],
    }


def test_default_read_set_returns_only_current_canonical_instruction() -> None:
    result = query_records(v1_registry())

    assert [item["path"] for item in result] == ["docs/current/README.md"]
    assert query_records(v1_registry(), include_reference=True) == v1_registry()["documents"][:2]


def test_validator_rejects_duplicate_canonical_topic_and_historical_instruction() -> None:
    candidate = v1_registry()
    duplicate = dict(candidate["documents"][0])
    candidate["documents"].append(duplicate)
    candidate["documents"][2]["instructional"] = True

    errors = validate_registry(candidate)

    assert "topic agent-reading has multiple canonical documents" in errors
    assert "docs/archive/plans/README.md: historical documents cannot be instructional" in errors


def test_query_is_pure_and_never_exposes_archived_documents() -> None:
    candidate = v1_registry()
    before = json.dumps(candidate, sort_keys=True)

    assert all("docs/archive/" not in item["path"] for item in query_records(candidate))
    assert json.dumps(candidate, sort_keys=True) == before


def test_v2_registry_preserves_the_v1_agent_read_set() -> None:
    candidate = v1_registry()
    candidate["schemaVersion"] = 2
    candidate["topics"] = [
        {
            "topic": "agent-reading",
            "criticality": "P0",
            "canonicalPath": "docs/current/README.md",
            "localizedPaths": {
                "en": "docs/current/README.md",
                "ja": "docs/current/README.ja.md",
                "zh-CN": "docs/current/README.zh-CN.md",
            },
            "audiences": ["adopter"],
            "journeys": ["understand"],
            "nextTopics": [],
            "enforcementStatus": "planned",
            "plainLanguageRequired": True,
            "semanticInvariants": [],
        }
    ]

    assert validate_registry(candidate) == []
    assert query_records(candidate) == query_records(v1_registry())


def test_authority_cli_checks_and_queries_v2_registry() -> None:
    root = Path(__file__).resolve().parents[1]
    checked = subprocess.run(
        [sys.executable, "scripts/ai_documentation_authority.py", "--check"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    queried = subprocess.run(
        [sys.executable, "scripts/ai_documentation_authority.py", "--include-reference"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert checked.returncode == 0
    assert "documentation authority registry check passed" in checked.stdout
    assert queried.returncode == 0
    assert json.loads(queried.stdout)["ok"] is True


def test_load_registry_fails_closed_for_missing_and_invalid_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot load registry"):
        load_registry(tmp_path / "missing.json")
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot load registry"):
        load_registry(invalid)
