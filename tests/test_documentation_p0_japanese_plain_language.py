from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_japanese_p0_has_no_known_standalone_english_explanations():
    pages = [
        "README.ja.md",
        "docs/README.ja.md",
        "docs/purpose.ja.md",
        "docs/getting-started/first-calibration.ja.md",
    ]
    forbidden = (
        "this template provides the proposal capability",
        "The template provides this capability; it does not prove adopter installation.",
    )
    text = "\n".join(read(page) for page in pages)
    assert not any(sentence in text for sentence in forbidden)


def test_japanese_home_navigation_is_complete_and_same_language():
    home = read("docs/README.ja.md")
    assert "進行・調査・停止の判断を確認します。" in home
    assert "\n   で、進行" not in home
    for link in (
        "purpose.ja.md",
        "philosophy/design-philosophy.ja.md",
        "architecture.ja.md",
        "capabilities.ja.md",
        "concepts/decision-states.ja.md",
        "operations/recovery.ja.md",
    ):
        assert link in home
