"""Focused tests for Project Profile controlled Outcome locale views."""

import json

import pytest

from scripts.ai_render_task_outcome_multilingual import (
    normalize_locale,
    render_localized_outcome,
    render_outcome_files,
    selected_locales,
)


def outcome() -> dict[str, object]:
    return {
        "workItemId": "locale-task",
        "status": "completed_with_warnings",
        "sections": {
            "outcomeSummary": "One source summary.",
            "taskOverview": "The same fact source.",
            "deliveredChanges": [{"title": "Added renderer"}],
            "findings": [
                {
                    "title": "Evidence gap",
                    "category": "evidence",
                    "severity": "medium",
                    "state": "unresolved",
                    "description": "A human must decide.",
                }
            ],
            "risks": [],
            "warnings": ["Review remains bounded."],
            "interventions": [],
            "forcedStops": [],
            "resolutions": [],
            "recurrencePrevention": [],
            "avoidedImpact": [],
            "residualRisks": [],
            "humanDecisions": [],
            "evidence": [],
        },
    }


def profile(default: str = "ja", languages: list[str] | None = None) -> dict[str, object]:
    policy: dict[str, object] = {"defaultLanguage": default}
    if languages is not None:
        policy["languages"] = languages
    return {"reporting": {"defaultLanguage": default, "taskOutcome": policy}}


def test_locale_aliases_are_normalized_without_ambiguity() -> None:
    assert normalize_locale("ja-JP") == "ja"
    assert normalize_locale("en_US") == "en"
    assert normalize_locale("zh-CN") == "zh-CN"
    with pytest.raises(ValueError):
        normalize_locale("fr")


def test_default_language_and_explicit_generation_set() -> None:
    assert selected_locales(profile()) == ("ja",)
    assert selected_locales(profile(default="en", languages=["ja-JP", "en", "zh"])) == (
        "ja",
        "en",
        "zh-CN",
    )


def test_no_silent_fallback_for_invalid_profile_policy() -> None:
    with pytest.raises(ValueError):
        selected_locales(profile(default="fr"))
    with pytest.raises(ValueError):
        selected_locales(profile(languages=["ja", "fr"]))


def test_three_languages_have_localized_chrome_and_shared_facts() -> None:
    rendered = {
        locale: render_localized_outcome(outcome(), locale) for locale in ("ja", "en", "zh-CN")
    }
    assert "## 概要" in rendered["ja"]
    assert "## Outcome Summary" in rendered["en"]
    assert "## 结果摘要" in rendered["zh-CN"]
    for text in rendered.values():
        assert "One source summary." in text
        assert "A human must decide." in text
    assert "Category: evidence; Severity: medium; State: unresolved" in rendered["en"]
    assert "分類: evidence; 重大度: medium; 状態: unresolved" in rendered["ja"]
    assert "类别: evidence; 严重性: medium; 状态: unresolved" in rendered["zh-CN"]
    assert "なし" in rendered["ja"]
    assert "无" in rendered["zh-CN"]
    assert rendered["ja"] != rendered["en"] != rendered["zh-CN"]


def test_file_generation_is_exact_and_does_not_mutate_source(tmp_path) -> None:
    source = outcome()
    before = json.dumps(source, sort_keys=True)
    paths = render_outcome_files(source, profile(languages=["en", "zh-CN"]), tmp_path)
    assert [path.name for path in paths] == [
        "locale-task.outcome.en.md",
        "locale-task.outcome.zh-CN.md",
    ]
    assert not (tmp_path / "locale-task.outcome.ja.md").exists()
    assert json.dumps(source, sort_keys=True) == before
