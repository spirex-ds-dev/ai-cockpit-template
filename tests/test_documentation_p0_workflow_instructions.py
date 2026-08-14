"""Regression checks for the executable first Work Item workflow instructions."""

from pathlib import Path

ROOT = Path(__file__).parents[1]
PAGES = (
    ROOT / "docs/getting-started/first-work-item.md",
    ROOT / "docs/getting-started/first-work-item.ja.md",
    ROOT / "docs/getting-started/first-work-item.zh-CN.md",
)


def test_first_work_item_pages_use_the_canonical_before_edit_checkpoint() -> None:
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        assert "make ai-prepare-implementation" in text, page
        assert "CONTRACT=.ai/work-items/active/" in text, page
        assert "SUMMARY=.ai/work-items/active/" in text, page
        assert "ai-checkpoint" not in text.lower(), page


def test_first_work_item_pages_make_archive_before_pr_explicit() -> None:
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        lowered = text.lower()
        finish = lowered.index("make ai-finish")
        assert lowered.index("archive=true", finish) >= finish, page
        assert any(token in lowered[finish:] for token in ("push", "推送")), page
        assert "pr" in lowered[finish:], page
        assert any(token in lowered[finish:] for token in ("merge", "合并")), page
        assert lowered.index("make ai-close-work-item", finish) >= finish, page
