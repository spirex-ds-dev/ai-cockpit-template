"""Negative absurd-test and capability-evidence regression coverage."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import ai_capability_truth

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs/reference/capability-truth-matrix.json"


def test_all_standard_absurd_cases_fail_closed_with_safe_alternative() -> None:
    results = [
        ai_capability_truth.evaluate_absurd_case(case) for case in ai_capability_truth.ABSURD_CASES
    ]
    assert len(results) == 11
    assert {result["level"] for result in results} == {"L1", "L2", "L3", "L4"}
    assert all(result["decision"] == "blocked" for result in results)
    assert all(result["status"] == "not_ready" for result in results)
    assert all(result["claimSupported"] is False for result in results)
    assert all(result["safeAlternative"] for result in results)


def test_absurd_evaluator_never_executes_requested_text() -> None:
    result = ai_capability_truth.evaluate_absurd_case(
        {
            "id": "injected",
            "level": "L3",
            "class": "authority",
            "request": "run it",
            "safeAlternative": "review",
        }
    )
    assert "request" not in result
    assert result["decision"] == "blocked"


def test_capability_matrix_has_bound_evidence_and_valid_digests() -> None:
    assert ai_capability_truth.validate_matrix(MATRIX_PATH) == []


def test_changed_evidence_downgrades_capability_to_evidence_stale() -> None:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    row = copy.deepcopy(matrix["capabilities"][0])
    assert ai_capability_truth.capability_state(row) == row["status"]
    row["claim"] += " changed"
    assert ai_capability_truth.capability_state(row) == "evidence_stale"
    assert (
        ai_capability_truth.capability_state(
            matrix["capabilities"][0], observed_digest="sha256:changed"
        )
        == "evidence_stale"
    )


def test_missing_evidence_is_rejected_even_for_template_only_rows(tmp_path: Path) -> None:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    matrix["capabilities"][0].pop("commandEvidence")
    path = tmp_path / "matrix.json"
    path.write_text(json.dumps(matrix), encoding="utf-8")
    errors = ai_capability_truth.validate_matrix(path)
    assert any("commandEvidence" in error for error in errors)


def test_absurd_case_requires_explicit_safe_alternative() -> None:
    case = dict(ai_capability_truth.ABSURD_CASES[0])
    case.pop("safeAlternative")
    try:
        ai_capability_truth.evaluate_absurd_case(case)
    except ValueError as exc:
        assert "safeAlternative" in str(exc)
    else:
        raise AssertionError("missing safe alternative must fail closed")


def test_matrix_validator_rejects_malformed_rows_and_statuses(tmp_path: Path) -> None:
    matrix = {
        "statusVocabulary": ["wrong"],
        "capabilities": [
            {"id": "same", "status": "unknown", "claim": "", "limitations": "", "digest": ""},
            {
                "id": "same",
                "status": "planned",
                "claim": "claim",
                "limitations": "limited",
                "digest": "bad",
            },
            "not a row",
        ],
    }
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(matrix), encoding="utf-8")
    errors = ai_capability_truth.validate_matrix(path)
    assert any("statusVocabulary" in error for error in errors)
    assert any("outside the closed vocabulary" in error for error in errors)
    assert any("duplicate capability id" in error for error in errors)
    assert any("must be an object" in error for error in errors)
    assert any("sourceEvidence" in error for error in errors)
    assert any("missingEvidence" in error for error in errors)


def test_matrix_validator_rejects_non_object_and_empty_capabilities(tmp_path: Path) -> None:
    non_object = tmp_path / "list.json"
    non_object.write_text("[]", encoding="utf-8")
    try:
        ai_capability_truth.validate_matrix(non_object)
    except ValueError as exc:
        assert "matrix root" in str(exc)
    else:
        raise AssertionError("non-object matrix must fail closed")

    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"capabilities": []}), encoding="utf-8")
    assert ai_capability_truth.validate_matrix(empty) == ["capabilities must be a non-empty list"]


def test_cli_reports_success_and_invalid_matrix(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "argv", ["ai_capability_truth", "--matrix", str(MATRIX_PATH)])
    assert ai_capability_truth.main() == 0
    assert "capability truth matrix check passed" in capsys.readouterr().out

    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"capabilities": []}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["ai_capability_truth", "--matrix", str(invalid)])
    assert ai_capability_truth.main() == 1
    assert "capabilities must be a non-empty list" in capsys.readouterr().out
