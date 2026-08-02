"""Focused tests for the documentation authority read boundary."""

import json

from scripts.ai_documentation_authority import query_records, validate_registry


def registry() -> dict[str, object]:
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
    result = query_records(registry())

    assert [item["path"] for item in result] == ["docs/current/README.md"]
    assert query_records(registry(), include_reference=True) == registry()["documents"][:2]


def test_validator_rejects_duplicate_canonical_topic_and_historical_instruction() -> None:
    candidate = registry()
    duplicate = dict(candidate["documents"][0])
    candidate["documents"].append(duplicate)
    candidate["documents"][2]["instructional"] = True

    errors = validate_registry(candidate)

    assert "topic agent-reading has multiple canonical documents" in errors
    assert "docs/archive/plans/README.md: historical documents cannot be instructional" in errors


def test_query_is_pure_and_never_exposes_archived_documents() -> None:
    candidate = registry()
    before = json.dumps(candidate, sort_keys=True)

    assert all("docs/archive/" not in item["path"] for item in query_records(candidate))
    assert json.dumps(candidate, sort_keys=True) == before
