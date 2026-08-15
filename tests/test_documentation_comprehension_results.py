import json
import re
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
RESULTS_PATH = ROOT / "docs/reference/comprehension-validation-results.json"
RESPONSE_SCHEMA_PATH = ROOT / "docs/reference/comprehension-validation-response.schema.json"
BOUND_REVISION = "fde3380f81fea5fd2e288f7a8849f737dc074060"
BOUND_TREE = "d752493863afc8c5f7749d067cd80d60ee72a495"
CURRENT_REVISION = "1c12d3065312f11d4416cb8bd890630e06ca32c3"
CURRENT_TREE = "cd165896e8d2622e97edce5a62ff47440c0cc4a1"


def validate_response_schema(value, schema, path="$"):
    if "const" in schema:
        assert value == schema["const"], f"{path}: const mismatch"
    if "enum" in schema:
        assert value in schema["enum"], f"{path}: invalid enum"
    if schema.get("type") == "object":
        assert isinstance(value, dict), f"{path}: expected object"
        for key in schema.get("required", []):
            assert key in value, f"{path}: missing {key}"
        if schema.get("additionalProperties") is False:
            assert set(value) <= set(schema["properties"]), f"{path}: unsupported key"
        for key, child in schema.get("properties", {}).items():
            if key in value:
                validate_response_schema(value[key], child, f"{path}.{key}")
    elif schema.get("type") == "array":
        assert isinstance(value, list), f"{path}: expected array"
        assert len(value) >= schema.get("minItems", 0), f"{path}: too few items"
        assert len(value) <= schema.get("maxItems", len(value)), f"{path}: too many items"
        for index, child in enumerate(value):
            validate_response_schema(child, schema["items"], f"{path}[{index}]")
    elif schema.get("type") == "string":
        assert isinstance(value, str), f"{path}: expected string"
        assert len(value) >= schema.get("minLength", 0), f"{path}: too short"
        if "pattern" in schema:
            assert re.fullmatch(schema["pattern"], value), f"{path}: invalid pattern"
        if schema.get("format") == "date-time":
            assert datetime.fromisoformat(value).tzinfo is not None, f"{path}: timezone required"


def assert_response_revision_matches(results, response):
    assert response["documentRevision"] == results["documentRevision"]


def test_bounded_results_have_one_schema_valid_receipt_per_required_locale():
    assert RESULTS_PATH.exists(), "the study must publish an explicit result"

    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    schema = json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert results["status"] == "comprehension_verified_bounded"
    assert results["reviewState"] == "three_locale_current_revision_receipts_ingested"
    assert results["currentRevisionStatus"] == "comprehension_verified_bounded"
    assert results["currentDocumentRevision"] == CURRENT_REVISION
    assert results["currentDocumentTree"] == CURRENT_TREE
    assert results["documentRevision"] == BOUND_REVISION
    assert results["documentTree"] == BOUND_TREE
    assert results["requiredLanguages"] == ["en", "zh-CN", "ja"]
    assert results["claimAuthorized"] is True
    assert BOUND_REVISION in results["authorizedClaim"]
    assert "a3cf1deda0d9577817b2ffeb8078068f77f48340" not in results["authorizedClaim"]
    assert "later revisions" in results["authorizedClaim"]
    assert results["missingEvidence"] == []
    assert [item["language"] for item in results["responses"]] == ["en", "zh-CN", "ja"]

    for item in results["responses"]:
        response = json.loads((ROOT / item["path"]).read_text(encoding="utf-8"))
        validate_response_schema(response, schema)
        assert response["participantPseudonym"] == item["participantPseudonym"]
        assert response["language"] == item["language"]
        assert_response_revision_matches(results, response)
        assert response["answeredAt"] == "2026-08-15T19:02:00+09:00"
        assert response["consentConfirmed"] is True
        assert response["identifyingData"] is None
        assert [answer["questionId"] for answer in response["answers"]] == [
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "Q5",
            "Q6",
        ]
        assert {answer["score"] for answer in response["answers"]} == {"correct"}


def test_bounded_results_fail_closed_when_a_response_revision_drifts():
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    response = json.loads(
        (ROOT / "docs/reference/comprehension-validation-responses/peter_01.en.json").read_text(
            encoding="utf-8"
        )
    )
    response["documentRevision"] = "a3cf1deda0d9577817b2ffeb8078068f77f48340"

    with pytest.raises(AssertionError):
        assert_response_revision_matches(results, response)


def test_bounded_results_keep_the_non_population_limitations():
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    assert results["minimumSample"] == {"en": 1, "zh-CN": 1, "ja": 1}
    assert results["limitations"] == [
        "Agent or author answers are not participant evidence.",
        "This one-reader-per-locale sample is revision-bound and cannot establish general-population comprehension.",
        "The current-main result is bounded to one independent reader per required locale and cannot establish general-population comprehension.",
        "The result does not authorize merge, release, safety, security, or enterprise-compliance claims.",
    ]


def test_current_revision_boundary_requires_three_fresh_routes():
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    boundary = results["currentRevisionBoundary"]

    assert boundary["claimAuthorized"] is True
    assert boundary["requiredLanguages"] == ["en", "zh-CN", "ja"]
    assert boundary["minimumSample"] == {"en": 1, "zh-CN": 1, "ja": 1}
    assert boundary["missingEvidence"] == []
    assert [item["language"] for item in boundary["responses"]] == ["en", "zh-CN", "ja"]
    assert CURRENT_REVISION in boundary["authorizedClaim"]

    for item in boundary["responses"]:
        response = json.loads((ROOT / item["path"]).read_text(encoding="utf-8"))
        validate_response_schema(
            response, json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))
        )
        assert response["documentRevision"] == CURRENT_REVISION
        assert response["answeredAt"] == "2026-08-16T07:44:00+09:00"
        assert [answer["questionId"] for answer in response["answers"]] == [
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "Q5",
            "Q6",
        ]
        assert {answer["score"] for answer in response["answers"]} == {"correct"}


def test_bounded_results_are_explicitly_historical_not_current_main_claims():
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    report = (ROOT / "docs/reference/comprehension-validation-results.md").read_text(
        encoding="utf-8"
    )

    assert "historical document revision" in results["authorizedClaim"]
    assert "current-main revision" not in results["authorizedClaim"]
    assert "current `main` revision is later" in report
    assert "fresh independent nontechnical reader" in report
    assert "Current revision evidence" in report
