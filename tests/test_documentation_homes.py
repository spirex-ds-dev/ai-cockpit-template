"""Tests for the reader-first multilingual documentation homes."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOMES = {
    "en": ROOT / "docs/README.md",
    "ja": ROOT / "docs/README.ja.md",
    "zh-CN": ROOT / "docs/README.zh-CN.md",
}
REQUIRED_SECTIONS = {
    "en": (
        "North Star / identity",
        "Purpose",
        "Design philosophy",
        "Architecture",
        "Capabilities and boundaries",
        "Human decisions",
    ),
    "ja": ("North Star / identity", "目的", "設計思想", "アーキテクチャ", "能力と境界", "人の判断"),
    "zh-CN": ("North Star / 身份", "目的", "设计思想", "架构", "能力与边界", "人的决定"),
}


def markdown_targets(text: str) -> set[str]:
    return {
        target.split("#", 1)[0]
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
        if not target.startswith(("http://", "https://", "mailto:"))
    }


def test_all_localized_homes_exist_and_keep_core_narrative_order() -> None:
    for locale, home in HOMES.items():
        assert home.is_file(), home
        text = home.read_text(encoding="utf-8")
        positions = [
            text.lower().index(f"**{section}".lower()) for section in REQUIRED_SECTIONS[locale]
        ]
        positions.extend(
            [
                text.lower().index(
                    "## "
                    + (
                        "choose a reader goal"
                        if locale == "en"
                        else "読者の目的から選ぶ"
                        if locale == "ja"
                        else "按读者目标选择"
                    ).lower()
                ),
                text.lower().index(
                    (
                        "| Recover from a stop"
                        if locale == "en"
                        else "| stop から回復する"
                        if locale == "ja"
                        else "| 从停止中恢复"
                    ).lower()
                ),
            ]
        )
        assert positions == sorted(positions), home


def test_each_home_links_to_existing_current_destinations_without_archive_routes() -> None:
    for home in HOMES.values():
        for target in markdown_targets(home.read_text(encoding="utf-8")):
            assert "docs/archive/" not in target
            if target.startswith("/") or not target:
                continue
            assert (home.parent / target).is_file(), (home, target)


def test_root_readmes_use_matching_language_documentation_homes() -> None:
    expected = {
        "README.md": "docs/README.md",
        "README.ja.md": "docs/README.ja.md",
        "README.zh-CN.md": "docs/README.zh-CN.md",
    }
    for filename, target in expected.items():
        assert target in (ROOT / filename).read_text(encoding="utf-8")


def test_non_english_homes_expose_same_language_adoption_routes() -> None:
    for locale in ("ja", "zh-CN"):
        text = HOMES[locale].read_text(encoding="utf-8").lower()
        assert "first-calibration" in text or "首次校准" in text or "最初の calibration" in text
        assert "fallback" not in text.split("##", 1)[-1]
