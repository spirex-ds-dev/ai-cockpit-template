"""Contract tests for the standalone Task Outcome JSON Schema."""

import json
import re
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / ".ai/schemas/task_outcome.schema.json"


def schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def resolve(schema_document: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    reference = node.get("$ref")
    if not reference:
        return node
    assert reference.startswith("#/$defs/")
    return schema_document["$defs"][reference.removeprefix("#/$defs/")]


def validate(
    schema_document: dict[str, Any], node: dict[str, Any], value: Any, path: str = "$"
) -> None:
    node = resolve(schema_document, node)
    if "const" in node:
        assert value == node["const"], f"{path}: expected {node['const']!r}"
    if "type" in node:
        expected = node["type"]
        type_ok = {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
        }[expected]
        assert type_ok, f"{path}: expected {expected}"
    if isinstance(value, dict):
        for required in node.get("required", []):
            assert required in value, f"{path}: missing {required}"
        if node.get("additionalProperties") is False:
            assert set(value) <= set(node.get("properties", {})), f"{path}: unsupported key"
        for key, child in node.get("properties", {}).items():
            if key in value:
                validate(schema_document, child, value[key], f"{path}.{key}")
    if isinstance(value, list) and "items" in node:
        for index, item in enumerate(value):
            validate(schema_document, node["items"], item, f"{path}[{index}]")
    if isinstance(value, str):
        if "enum" in node:
            assert value in node["enum"], f"{path}: invalid enum"
        if "pattern" in node:
            assert re.fullmatch(node["pattern"], value), f"{path}: invalid pattern"
        if "minLength" in node:
            assert len(value) >= node["minLength"], f"{path}: too short"
        if "maxLength" in node:
            assert len(value) <= node["maxLength"], f"{path}: too long"
    if isinstance(value, int) and "minimum" in node:
        assert value >= node["minimum"], f"{path}: below minimum"


def minimum_report() -> dict[str, Any]:
    return {
        "format": "ai-cockpit-task-outcome",
        "schemaVersion": 1,
        "workItemId": "task-outcome-schema",
        "status": "completed",
        "bindings": {
            "taskId": "task-outcome-schema",
            "contractDigest": "a" * 64,
            "summaryDigest": "b" * 64,
            "verificationDigest": "c" * 64,
            "baseCommit": "1" * 40,
            "headCommit": "2" * 40,
            "lifecycleStage": "post_pr",
            "pullRequest": {"number": 351, "url": "https://github.com/example/repo/pull/351"},
            "aiCockpitVersion": "0.1.0",
            "generatorVersion": "1",
        },
        "sections": {
            "outcomeSummary": "No findings were recorded.",
            "taskOverview": "Schema contract verification.",
            "deliveredChanges": [],
            "findings": [],
            "risks": [],
            "warnings": [],
            "interventions": [],
            "forcedStops": [],
            "resolutions": [],
            "recurrencePrevention": [],
            "avoidedImpact": [],
            "residualRisks": [],
            "humanDecisions": [],
            "evidence": [],
        },
    }


def test_schema_is_versioned_and_has_english_machine_keys() -> None:
    document = schema()
    assert document["$schema"].endswith("draft/2020-12/schema")
    assert document["properties"]["format"]["const"] == "ai-cockpit-task-outcome"
    assert "bindings" in document["required"]
    assert "sections" in document["required"]


def test_minimum_report_allows_empty_repeatable_sections() -> None:
    document = schema()
    validate(document, document, minimum_report())


def test_complete_report_covers_requested_categories() -> None:
    document = schema()
    report = minimum_report()
    evidence = {"subject": "pytest", "source": "tests/test_task_outcome_schema.py"}
    report["sections"]["findings"] = [
        {
            "findingFingerprint": "checker:reason:resource:subject",
            "category": "evidence",
            "severity": "low",
            "title": "A bounded observation",
            "state": "resolved",
            "evidence": [evidence],
        }
    ]
    report["sections"]["risks"] = [
        {
            "kind": "potential_risk",
            "severity": "medium",
            "title": "A residual risk",
            "state": "accepted",
            "evidence": [evidence],
        }
    ]
    report["sections"]["interventions"] = [
        {"kind": "warned", "title": "A warning", "evidence": [evidence]}
    ]
    report["sections"]["forcedStops"] = [
        {
            "stage": "verification",
            "reason": "A gate required review",
            "policyOrGuard": "example-guard",
            "attemptedAction": "Continue",
            "result": "accepted",
            "evidence": [evidence],
        }
    ]
    report["sections"]["resolutions"] = [
        {
            "problem": "Problem",
            "action": "Action",
            "verification": "Verification",
            "result": "resolved",
            "evidence": [evidence],
        }
    ]
    report["sections"]["recurrencePrevention"] = [
        {
            "kind": "Automated Check",
            "coverage": "The checker covers this boundary.",
            "humanDependency": "Review remains required for external state.",
        }
    ]
    report["sections"]["evidence"] = [evidence]
    validate(document, document, report)


@pytest.mark.parametrize(
    ("field", "value"),
    [("status", "green"), ("schemaVersion", 2)],
)
def test_invalid_report_status_or_version_is_rejected(field: str, value: Any) -> None:
    document = schema()
    report = minimum_report()
    report[field] = value
    with pytest.raises(AssertionError):
        validate(document, document, report)


@pytest.mark.parametrize(
    ("field", "value"),
    [("contractDigest", "not-a-digest"), ("baseCommit", "not-a-commit")],
)
def test_invalid_provenance_binding_is_rejected(field: str, value: str) -> None:
    document = schema()
    report = minimum_report()
    report["bindings"][field] = value
    with pytest.raises(AssertionError):
        validate(document, document, report)


def test_invalid_severity_and_unsupported_score_are_rejected() -> None:
    document = schema()
    report = minimum_report()
    report["sections"]["risks"] = [
        {
            "kind": "potential_risk",
            "severity": "urgent",
            "title": "Invalid",
            "state": "unresolved",
            "evidence": [],
        }
    ]
    with pytest.raises(AssertionError):
        validate(document, document, report)
    report = minimum_report()
    report["score"] = 100
    with pytest.raises(AssertionError):
        validate(document, document, report)
