import json
from pathlib import Path

import pytest

from scripts.ai_enterprise_control_evidence import evaluate_control, validate_control_record

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/reference/enterprise-control-matrix.json"
REQUIRED_IDS = {
    "identity",
    "authorization",
    "branch_protection",
    "review_policy",
    "separation_of_duties",
    "artifact_signing",
    "sbom",
    "provenance",
    "secret_management",
    "audit_log",
    "retention",
    "production_isolation",
}


def load_matrix():
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def test_enterprise_matrix_has_required_controls_and_complete_not_verified_records():
    matrix = load_matrix()
    assert matrix["schemaVersion"] == 2
    assert matrix["verdict"] == "observed_control_evidence_only"
    controls = {item["controlId"]: item for item in matrix["controls"]}
    assert set(controls) == REQUIRED_IDS
    assert all(validate_control_record(item) == [] for item in controls.values())
    assert all(item["observedState"] == "not_verified" for item in controls.values())
    assert all(item["evidenceType"] == "none" for item in controls.values())


def test_boundary_docs_preserve_external_control_and_japanese_gate_limits():
    paths = [
        ROOT / "docs/enterprise-security-boundary.md",
        ROOT / "docs/reference/enterprise-control-checklist.md",
        ROOT / "README.md",
        ROOT / "README.ja.md",
        ROOT / "README.zh-CN.md",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "external control" in text.lower() or "external_control_required" in text
    assert "observed control evidence" in text.lower()
    for claim in ("SOC 2", "ISO 27001", "SLSA"):
        assert claim in text
    assert "not a compliance" in text.lower() or "not a substitute" in text.lower()


@pytest.mark.parametrize("forbidden", ["compliant", "verified", "enterprise_ready"])
def test_matrix_does_not_expose_a_compliance_or_verified_verdict(forbidden):
    matrix = load_matrix()
    assert matrix["verdict"] != forbidden
    assert all(item["observedState"] != forbidden for item in matrix["controls"])


def test_matrix_default_controls_evaluate_to_not_verified():
    from datetime import UTC, datetime

    controls = load_matrix()["controls"]
    results = [evaluate_control(item, now=datetime(2026, 8, 2, tzinfo=UTC)) for item in controls]
    assert all(result["state"] == "not_verified" for result in results)
    assert all(result["reasons"] == ["external_evidence_missing"] for result in results)
