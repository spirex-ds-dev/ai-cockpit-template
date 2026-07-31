"""Regression checks for the Conditional GO capability truth boundary."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from ai_capability_truth import (
    CapabilityTruthError,
    build_evidence_source,
    regenerate_matrix,
    validate_matrix,
)
from check_docs_metadata import capability_claim_errors

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs/reference/capability-truth-matrix.json"
MARKDOWN_PATH = ROOT / "docs/reference/capability-truth-matrix.md"


def load_matrix() -> dict:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def test_matrix_uses_closed_status_vocabulary_and_evidence_fields() -> None:
    matrix = load_matrix()
    statuses = set(matrix["statusVocabulary"])
    assert statuses == {"implemented", "template_only", "adopter_installed", "planned"}
    assert matrix["capabilities"]
    for capability in matrix["capabilities"]:
        assert capability["status"] in statuses
        assert capability["id"]
        assert capability["claim"]
        assert capability["evidence"]
        assert capability["sourceEvidence"]
        assert capability["testEvidence"]
        assert capability["commandEvidence"]
        assert capability["limitations"]
        assert capability["evidenceSource"]["algorithm"] == "sha256-canonical-json-v1"
        assert capability["evidenceSource"]["fileCount"] == len(
            capability["evidenceSource"]["files"]
        )
        assert capability["evidenceSource"]["digest"].startswith("sha256:")
        assert capability["digest"].startswith("sha256:")
        if capability["status"] == "planned":
            assert capability.get("missingEvidence")


def test_remaining_review_gaps_and_completed_evidence_are_explicit() -> None:
    capabilities = {item["id"]: item for item in load_matrix()["capabilities"]}
    quick_install = capabilities["quick_install_release_archive_digest"]
    assert quick_install["status"] == "implemented"
    assert {
        "install.sh",
        "scripts/verify_quick_install_release.py",
        "release.json",
    } <= set(quick_install["evidence"])
    assert "release.json" not in quick_install["sourceEvidence"]
    assert "tests/test_quick_install_release.py" in quick_install["testEvidence"]
    assert "does not prove" in quick_install["limitations"]
    assert capabilities["independent_ci_release_evidence"]["status"] == "implemented"
    assert capabilities["ten_stage_calibration_session"]["status"] == "implemented"
    assert capabilities["candidate_activation_and_active_preservation"]["status"] == "implemented"
    assert capabilities["bootstrap_wizard_lifecycle"]["status"] == "implemented"
    assert capabilities["ownership_manifest_and_managed_regions"]["status"] == "adopter_installed"
    assert capabilities["governed_update_and_uninstall"]["status"] == "adopter_installed"
    uninstall = capabilities["governed_update_and_uninstall"]
    assert "proposalDigest" in uninstall["claim"]
    assert "detached filesystem removal" in uninstall["claim"]
    assert "Purge" in uninstall["limitations"]
    assert "not implemented" in uninstall["limitations"]
    assert "tests/test_japanese_adopter_lifecycle.py" in uninstall["testEvidence"]


def test_matrix_document_points_to_machine_readable_source_and_plan() -> None:
    document = MARKDOWN_PATH.read_text(encoding="utf-8")
    assert "capability-truth-matrix.json" in document
    assert "2026-07-29-pre-release-documentation-truth-corrective.md" in document
    assert "template_only" in document
    assert "adopter_installed" in document


def test_documentation_claims_are_checked_against_the_matrix() -> None:
    assert capability_claim_errors(ROOT) == []


def test_machine_matrix_evidence_binding_is_valid() -> None:
    assert validate_matrix(MATRIX_PATH) == []


def test_evidence_source_digest_changes_only_for_bound_file_bytes(tmp_path) -> None:
    (tmp_path / "source.py").write_text("first\n", encoding="utf-8")
    (tmp_path / "test.py").write_text("test\n", encoding="utf-8")
    (tmp_path / "unrelated.py").write_text("unrelated\n", encoding="utf-8")

    before = build_evidence_source(["source.py"], ["test.py"], root=tmp_path)
    (tmp_path / "unrelated.py").write_text("changed\n", encoding="utf-8")
    unchanged = build_evidence_source(["source.py"], ["test.py"], root=tmp_path)
    (tmp_path / "source.py").write_text("second\n", encoding="utf-8")
    changed = build_evidence_source(["source.py"], ["test.py"], root=tmp_path)

    assert before == unchanged
    assert before["digest"] != changed["digest"]


@pytest.mark.parametrize(
    ("paths", "setup", "diagnostic"),
    [
        (["missing.py"], "none", "missing"),
        (["../escape.py"], "none", "escapes repository"),
        (["source.py", "./source.py"], "file", "duplicate"),
        (["alias.py"], "symlink", "symbolic link"),
    ],
)
def test_evidence_source_fails_closed_for_unsafe_inventory(
    tmp_path, paths, setup, diagnostic
) -> None:
    if setup == "file":
        (tmp_path / "source.py").write_text("source\n", encoding="utf-8")
    elif setup == "symlink":
        (tmp_path / "target.py").write_text("target\n", encoding="utf-8")
        (tmp_path / "alias.py").symlink_to(tmp_path / "target.py")

    with pytest.raises(CapabilityTruthError, match=diagnostic):
        build_evidence_source(paths, [], root=tmp_path)


def test_validate_matrix_rejects_bound_byte_drift_and_regeneration_repairs_it(
    tmp_path,
) -> None:
    (tmp_path / "source.py").write_text("source\n", encoding="utf-8")
    (tmp_path / "test.py").write_text("test\n", encoding="utf-8")
    matrix = {
        "statusVocabulary": ["implemented", "template_only", "adopter_installed", "planned"],
        "capabilities": [
            {
                "id": "bounded",
                "status": "implemented",
                "claim": "Bound evidence exists.",
                "evidence": ["source.py"],
                "verification": ["test.py"],
                "sourceEvidence": ["source.py"],
                "testEvidence": ["test.py"],
                "commandEvidence": ["pytest"],
                "limitations": "Repository-local evidence only.",
                "digest": "stale",
            }
        ],
    }
    regenerated = regenerate_matrix(copy.deepcopy(matrix), root=tmp_path)
    matrix_path = tmp_path / "matrix.json"
    matrix_path.write_text(json.dumps(regenerated), encoding="utf-8")
    assert validate_matrix(matrix_path, root=tmp_path) == []

    (tmp_path / "source.py").write_text("changed\n", encoding="utf-8")
    errors = validate_matrix(matrix_path, root=tmp_path)
    assert any("evidenceSource does not match" in error for error in errors)
