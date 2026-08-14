from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_chinese_p0_has_no_known_standalone_english_explanations():
    pages = [
        "README.zh-CN.md",
        "docs/README.zh-CN.md",
        "docs/purpose.zh-CN.md",
        "docs/getting-started/first-calibration.zh-CN.md",
    ]
    text = "\n".join(read(page) for page in pages)
    assert (
        "The template provides this capability; it does not prove adopter installation." not in text
    )


def test_chinese_home_keeps_complete_route_and_same_language_links():
    home = read("docs/README.zh-CN.md")
    for marker in (
        "North Star / 身份",
        "目的",
        "设计思想",
        "架构",
        "能力与边界",
        "人的决定",
        "确认何时继续、调查或停止。",
    ):
        assert marker in home
    for link in (
        "purpose.zh-CN.md",
        "philosophy/design-philosophy.zh-CN.md",
        "architecture.zh-CN.md",
        "capabilities.zh-CN.md",
        "concepts/decision-states.zh-CN.md",
        "operations/recovery.zh-CN.md",
    ):
        assert link in home
