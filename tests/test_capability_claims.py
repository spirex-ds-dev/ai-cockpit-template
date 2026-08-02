"""Tests for source-bound public capability claim validation."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

from ai_capability_freshness import current_environment, make_record
from ai_capability_truth import regenerate_matrix, row_digest
from ai_check_capability_claims import claim_errors, extract_claim_ids


def _front_matter(*, claims: tuple[str, ...] = (), authority: str = "canonical") -> str:
    claim_lines = ""
    if claims:
        claim_lines = "capabilityClaims:\n" + "".join(f"  - {item}\n" for item in claims)
    return (
        "---\n"
        "author: Ray\n"
        "title: Fixture\n"
        "description: Fixture document.\n"
        "audience: adopter\n"
        "status: current\n"
        f"authority: {authority}\n"
        "lastVerifiedBy: fixture\n"
        f"{claim_lines}"
        "---\n\n"
    )


def _row(identifier: str, status: str = "implemented") -> dict:
    row = {
        "id": identifier,
        "status": status,
        "claim": f"{identifier} claim.",
        "evidence": ["source.py", "test.py"],
        "verification": ["pytest"],
        "sourceEvidence": ["source.py"],
        "testEvidence": ["test.py"],
        "commandEvidence": ["pytest -q"],
        "limitations": "Repository-local evidence only; not production assurance.",
        "digest": "pending",
    }
    if status == "planned":
        row["missingEvidence"] = "Executable source and verification are not present yet."
    return row


def _repository(tmp_path: Path, rows: list[dict]) -> Path:
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / "source.py").write_text("source\n", encoding="utf-8")
    (tmp_path / "test.py").write_text("test\n", encoding="utf-8")
    matrix = regenerate_matrix(
        {
            "statusVocabulary": [
                "implemented",
                "template_only",
                "adopter_installed",
                "planned",
            ],
            "capabilities": copy.deepcopy(rows),
        },
        root=tmp_path,
    )
    (tmp_path / "docs/reference/capability-truth-matrix.json").write_text(
        json.dumps(matrix), encoding="utf-8"
    )
    return tmp_path


def test_extract_claim_ids_supports_yaml_and_inline_markers() -> None:
    text = (
        _front_matter(claims=("alpha", "beta"))
        + "<!-- capability-claim: gamma -->\n"
        + "<!-- capability-claim: alpha -->\n"
    )

    assert extract_claim_ids(text) == {"alpha", "beta", "gamma"}


def test_unbound_multilingual_claim_terms_fail_with_actionable_path(tmp_path: Path) -> None:
    root = _repository(tmp_path, [_row("bounded")])
    (root / "README.md").write_text("This supports governed work.\n", encoding="utf-8")
    (root / "README.ja.md").write_text("統制された作業を検証します。\n", encoding="utf-8")
    (root / "README.zh-CN.md").write_text("支持受治理的工作。\n", encoding="utf-8")

    errors = claim_errors(root)

    assert any("README.md" in error and "unbound capability claim" in error for error in errors)
    assert any("README.ja.md" in error and "unbound capability claim" in error for error in errors)
    assert any(
        "README.zh-CN.md" in error and "unbound capability claim" in error for error in errors
    )


def test_unknown_id_and_changed_evidence_fail_closed(tmp_path: Path) -> None:
    root = _repository(tmp_path, [_row("bounded")])
    (root / "README.md").write_text(
        _front_matter(claims=("unknown",)) + "This supports governed work.\n",
        encoding="utf-8",
    )
    unknown_errors = claim_errors(root)
    assert any("unknown capability id: unknown" in error for error in unknown_errors)

    (root / "README.md").write_text(
        _front_matter(claims=("bounded",)) + "This supports governed work.\n",
        encoding="utf-8",
    )
    (root / "source.py").write_text("changed\n", encoding="utf-8")
    stale_errors = claim_errors(root)
    assert any(
        "evidenceSource does not match current evidence bytes" in error for error in stale_errors
    )
    assert any("bounded" in error and "evidence_stale" in error for error in stale_errors)


def test_expired_freshness_record_rejects_a_bound_claim(tmp_path: Path) -> None:
    root = _repository(tmp_path, [_row("bounded")])
    document = root / "README.md"
    document.write_text(
        _front_matter(claims=("bounded",)) + "This supports governed work.\n",
        encoding="utf-8",
    )
    matrix_path = root / "docs/reference/capability-truth-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    row = matrix["capabilities"][0]
    row["freshness"] = make_record(
        environment=current_environment(),
        scope=["source.py", "test.py"],
        now=datetime(2020, 1, 1, tzinfo=UTC),
    )
    row["digest"] = row_digest(row)
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    assert any("bounded" in error and "evidence_stale" in error for error in claim_errors(root))


def test_state_qualifiers_reject_overclaim_and_accept_bounded_language(tmp_path: Path) -> None:
    root = _repository(
        tmp_path,
        [_row("template_cap", "template_only"), _row("future_cap", "planned")],
    )
    document = root / "README.md"
    document.write_text(
        _front_matter(claims=("template_cap", "future_cap"))
        + "This supports both capabilities now.\n",
        encoding="utf-8",
    )
    errors = claim_errors(root)
    assert any("template_cap" in error and "template_only" in error for error in errors)
    assert any("future_cap" in error and "planned" in error for error in errors)

    document.write_text(
        _front_matter(claims=("template_cap", "future_cap"))
        + "The template provides this rule, but it does not prove adopter\ninstallation.\n"
        + "The second capability is planned for a future release.\n",
        encoding="utf-8",
    )
    assert claim_errors(root) == []


def test_multilingual_siblings_require_equal_binding_sets(tmp_path: Path) -> None:
    root = _repository(tmp_path, [_row("alpha"), _row("beta")])
    (root / "README.md").write_text(
        _front_matter(claims=("alpha",)) + "This supports governed work.\n",
        encoding="utf-8",
    )
    (root / "README.ja.md").write_text(
        _front_matter(claims=("alpha", "beta")) + "統制された作業をサポートします。\n",
        encoding="utf-8",
    )
    (root / "README.zh-CN.md").write_text(
        _front_matter(claims=("alpha",)) + "支持受治理的工作。\n",
        encoding="utf-8",
    )

    errors = claim_errors(root)
    assert any("multilingual capability binding mismatch" in error for error in errors)
    assert any("README.ja.md" in error and "beta" in error for error in errors)

    (root / "README.ja.md").write_text(
        _front_matter(claims=("alpha",)) + "統制された作業をサポートします。\n",
        encoding="utf-8",
    )
    assert claim_errors(root) == []


def test_supporting_records_and_generated_matrix_projection_are_excluded(
    tmp_path: Path,
) -> None:
    root = _repository(tmp_path, [_row("bounded")])
    supporting = root / "docs/design.md"
    supporting.write_text(
        _front_matter(authority="supporting") + "This guarantees a future capability.\n",
        encoding="utf-8",
    )
    projection = root / "docs/reference/capability-truth-matrix.md"
    projection.write_text(
        _front_matter() + "The generated matrix verifies evidence.\n", encoding="utf-8"
    )

    assert claim_errors(root) == []


def test_translation_sibling_of_canonical_document_is_in_scope(tmp_path: Path) -> None:
    root = _repository(tmp_path, [_row("bounded")])
    canonical = root / "docs/guide.md"
    canonical.write_text(
        _front_matter(claims=("bounded",)) + "This supports governed work.\n",
        encoding="utf-8",
    )
    translation = root / "docs/guide.ja.md"
    translation.write_text(
        _front_matter(authority="derived") + "統制された作業をサポートします。\n",
        encoding="utf-8",
    )

    errors = claim_errors(root)

    assert any("guide.ja.md" in error and "unbound capability claim" in error for error in errors)
    assert any("multilingual capability binding mismatch" in error for error in errors)
