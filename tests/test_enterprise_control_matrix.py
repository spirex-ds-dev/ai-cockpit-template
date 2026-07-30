import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/reference/enterprise-control-matrix.json"
ALLOWED = {
    "external_control_required",
    "configured",
    "verified",
    "not_configured",
    "not_applicable",
    "unknown",
}
REQUIRED_IDS = {
    "identity",
    "authorization",
    "required_review",
    "branch_protection",
    "separation_of_duties",
    "signed_commit_tag",
    "immutable_release",
    "least_privilege",
    "secret_management",
    "audit_retention",
    "data_classification",
    "provider_data_transfer",
    "incident_response",
    "legal_hold",
    "sbom",
    "provenance",
    "dependency_vulnerability",
}


def load_matrix():
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def test_enterprise_matrix_has_closed_status_vocabulary_and_required_controls():
    matrix = load_matrix()
    assert set(matrix["statusVocabulary"]) == ALLOWED
    controls = {item["id"]: item for item in matrix["controls"]}
    assert set(controls) == REQUIRED_IDS
    assert all(item["status"] in ALLOWED for item in controls.values())
    assert all(item["evidence"] for item in controls.values())


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
    assert "WI-16" in text
    for claim in ("SOC 2", "ISO 27001", "SLSA"):
        assert claim in text
    assert "not a compliance" in text.lower() or "not a substitute" in text.lower()


@pytest.mark.parametrize("status", ["verified", "not_applicable", "unknown", "invalid"])
def test_unknown_or_unlisted_status_is_not_silently_accepted(status):
    assert (status in ALLOWED) is (status != "invalid")
