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
            "findings": [],
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
        "humanHandoff": {
            "locale": "zh-CN",
            "completed": [{"title": "完成内容", "detail": "完成了交接层。", "evidence": []}],
            "passed": [{"title": "通过检查", "detail": "焦点测试已通过。", "evidence": []}],
            "retained": [{"title": "保留事项", "detail": "仍需人工确认。", "evidence": []}],
            "risks": [
                {
                    "severity": "medium",
                    "title": "风险",
                    "detail": "环境范围有限",
                    "state": "unresolved",
                    "evidence": [],
                }
            ],
            "redReasons": [],
            "questions": {
                "problemCount": 1,
                "blockedProblems": [],
                "resolvedProblems": ["旧交付缺口"],
                "resolutionApproach": ["增加结构化投影"],
                "avoidedRisks": ["误报完成"],
                "remainingRisks": ["需明确语言"],
                "agentUnknowns": ["Provider UI 不在范围内"],
                "humanConfirmations": ["确认保留事项"],
                "recurrenceLikelihood": "低",
                "nextTime": "开始时绑定语言",
            },
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
        assert "None" in text
    assert "## 已完成" in rendered["zh-CN"]
    assert "完成了交接层。" in rendered["zh-CN"]
    assert "### What was completed" in rendered["en"]
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
