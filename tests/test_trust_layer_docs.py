from pathlib import Path

from check_trust_layer_docs import (
    CORE_TERMS,
    SECTION_IDS,
    check_repository,
    core_term_errors,
    section_ids,
)


ROOT = Path(__file__).resolve().parents[1]


def test_trust_layer_documentation_is_complete_and_aligned():
    assert check_repository(ROOT) == []


def test_three_languages_share_section_ids_and_heading_count():
    documents = [
        ROOT / "docs" / "trust-layer.md",
        ROOT / "docs" / "trust-layer.zh-CN.md",
        ROOT / "docs" / "trust-layer.ja.md",
    ]
    assert all(
        section_ids(path.read_text(encoding="utf-8")) == list(SECTION_IDS) for path in documents
    )


def test_checker_rejects_missing_core_boundary(tmp_path):
    text = (ROOT / "docs" / "trust-layer.ja.md").read_text(encoding="utf-8")
    broken = text.replace(CORE_TERMS["ja"][0], "人間信頼レイヤー", 1)
    assert core_term_errors("ja", broken, "trust-layer.ja.md")


def test_checker_reports_missing_repository_files(tmp_path):
    errors = check_repository(tmp_path)
    assert any("missing Trust Layer document" in error for error in errors)
    assert any("missing Documentation Architecture" in error for error in errors)
    assert any("missing README" in error for error in errors)
