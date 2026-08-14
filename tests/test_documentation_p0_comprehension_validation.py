"""Evidence-bound checks for the six-question P0 comprehension protocol."""

from pathlib import Path

ROOT = Path(__file__).parents[1]
PAGES = [
    ROOT / "docs/reference/comprehension-review-2026-08-14.md",
    ROOT / "docs/reference/comprehension-review-2026-08-14.ja.md",
    ROOT / "docs/reference/comprehension-review-2026-08-14.zh-CN.md",
]


def test_each_language_records_six_answers_and_explicit_limit():
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        assert text.count("| 正答 |") + text.count("| 正确 |") + text.count("| Correct |") == 6
        assert "6/6" in text
        assert "native" in text.lower() or "母語" in text or "母语" in text
        assert "not" in text.lower() or "未" in text or "不" in text


def test_protocol_pages_preserve_critical_boundary_answers():
    for page in PAGES:
        text = page.read_text(encoding="utf-8").lower()
        assert "sandbox" in text or "サンドボックス" in text or "沙箱" in text
        assert "unknown" in text
        assert "human" in text or "人" in text
        assert "agent" in text
