"""Structural contract for the trilingual P0 decision journey."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "decision": "docs/concepts/decision-states",
    "status": "docs/reference/how-to-read-cockpit-status",
    "lifecycle": "docs/operations/work-item-lifecycle",
    "recovery": "docs/operations/recovery",
}
LOCALES = ("", ".ja", ".zh-CN")
REQUIRED = {
    "": ("Purpose", "Audience", "Outcome", "Scenario", "Decision", "Stop", "Next"),
    ".ja": ("目的", "対象", "結果", "シナリオ", "判断", "停止", "次"),
    ".zh-CN": ("目的", "读者", "结果", "场景", "决定", "停止", "下一步"),
}


def read_page(stem: str, locale: str) -> str:
    return (ROOT / f"{stem}{locale}.md").read_text(encoding="utf-8")


def test_each_p0_topic_has_three_locales_and_reader_contract() -> None:
    for stem in PAGES.values():
        for locale in LOCALES:
            text = read_page(stem, locale)
            assert text.startswith("---\n"), stem + locale
            lowered = text.lower()
            for marker in REQUIRED[locale]:
                assert marker.lower() in lowered, f"{stem}{locale}: {marker}"


def test_status_and_stop_pages_explain_human_action_and_safe_boundary() -> None:
    for stem in PAGES.values():
        for locale in LOCALES:
            text = read_page(stem, locale).lower()
            assert any(word in text for word in ("human", "人", "人間")), stem + locale
            assert any(word in text for word in ("next", "下一", "次", "次に")), stem + locale
            assert any(word in text for word in ("stop", "停止", "止め", "中止")), stem + locale
            assert any(word in text for word in ("guess", "推测", "推測", "推測し", "猜测")), (
                stem + locale
            )


def test_localized_pages_link_only_to_same_language_p0_siblings() -> None:
    for stem in PAGES.values():
        for locale in (".ja", ".zh-CN"):
            text = read_page(stem, locale)
            assert "fallback" not in text.lower()
            assert ".md)" not in text.replace(f"{locale}.md)", "")


def test_registry_activates_only_the_four_complete_topics() -> None:
    registry = json.loads(
        (ROOT / "docs/reference/documentation-authority-registry.json").read_text()
    )
    topics = {topic["topic"]: topic for topic in registry["topics"]}
    for topic in ("decision-states", "lifecycle", "recovery"):
        assert topics[topic]["enforcementStatus"] == "active"
        assert all((ROOT / path).exists() for path in topics[topic]["localizedPaths"].values())
    assert topics["security-boundaries"]["enforcementStatus"] == "active"


def test_journey_validator_handles_malformed_registry_and_missing_planned_path(
    tmp_path: Path,
) -> None:
    from scripts.ai_documentation_journey import planned_gaps, validate_topics

    assert validate_topics({"topics": "bad"}, tmp_path) == ["registry topics must be a list"]
    registry = {
        "topics": [
            {
                "topic": "future",
                "criticality": "P0",
                "enforcementStatus": "planned",
                "localizedPaths": {"en": "docs/future.md"},
            }
        ]
    }
    assert planned_gaps(registry, tmp_path)[0]["reason"] == "path does not exist"
