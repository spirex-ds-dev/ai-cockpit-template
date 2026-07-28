"""Tests for the opt-in, sanitized pull-request Outcome Summary."""

import json
import sys

from scripts import ai_render_task_outcome_pr
from scripts.ai_render_task_outcome_pr import render_pr_summary


def sample_outcome() -> dict[str, object]:
    return {
        "workItemId": "example-task",
        "status": "completed_with_warnings",
        "bindings": {"contractDigest": "a" * 64, "headCommit": "b" * 40},
        "sections": {
            "outcomeSummary": "Completed the bounded change; one warning remains.",
            "taskOverview": "A reviewer-facing overview.",
            "deliveredChanges": [
                {"title": "Added the guarded renderer", "source": "/private/path"}
            ],
            "findings": [
                {
                    "title": "Evidence gap",
                    "severity": "medium",
                    "evidence": [{"source": "secret-token"}],
                }
            ],
            "risks": [{"title": "Residual compatibility risk", "kind": "potential_risk"}],
            "warnings": ["Review the remaining compatibility warning."],
            "forcedStops": [{"stage": "finish", "reason": "private stop detail"}],
            "residualRisks": [{"title": "Residual compatibility risk"}],
            "evidence": [{"source": ".ai/private.json", "digest": "c" * 64}],
        },
    }


def profile(
    *,
    enabled: bool = True,
    fields: list[str] | None = None,
    language: str | None = None,
) -> dict[str, object]:
    return {
        "reporting": {
            "pullRequestSummary": {
                "enabled": enabled,
                **({"fields": fields} if fields is not None else {}),
                **({"language": language} if language is not None else {}),
            }
        }
    }


def test_profile_must_explicitly_enable_pr_summary() -> None:
    assert render_pr_summary(sample_outcome(), {}) == ""
    assert render_pr_summary(sample_outcome(), profile(enabled=False)) == ""
    assert (
        render_pr_summary(
            sample_outcome(),
            {"reporting": {"pullRequestSummary": {"enabled": "false"}}},
        )
        == ""
    )


def test_only_allowlisted_safe_sections_are_rendered() -> None:
    rendered = render_pr_summary(
        sample_outcome(),
        profile(
            fields=[
                "status",
                "outcomeSummary",
                "deliveredChanges",
                "findings",
                "risks",
                "warnings",
                "residualRisks",
            ]
        ),
    )
    assert "## Task Outcome Summary" in rendered
    assert "Status: `completed_with_warnings`" in rendered
    assert "Completed the bounded change" in rendered
    assert "Added the guarded renderer" in rendered
    assert "Evidence gap" in rendered
    assert "Residual compatibility risk" in rendered
    assert ".ai/private.json" not in rendered
    assert "secret-token" not in rendered
    assert "private stop detail" not in rendered
    assert "contractDigest" not in rendered
    assert "## Evidence" not in rendered
    assert "## Forced Stops" not in rendered


def test_empty_and_warning_states_are_explicit() -> None:
    candidate = sample_outcome()
    candidate["status"] = "needs_human_confirmation"
    candidate["sections"] = {"outcomeSummary": "", "warnings": [], "residualRisks": []}
    rendered = render_pr_summary(
        candidate, profile(fields=["status", "outcomeSummary", "warnings", "residualRisks"])
    )
    assert "Status: `needs_human_confirmation`" in rendered
    assert "Outcome: None" in rendered
    assert "Warnings: None" in rendered
    assert "Residual Risks: None" in rendered


def test_rendering_is_deterministic_and_does_not_mutate_input() -> None:
    candidate = sample_outcome()
    before = json.dumps(candidate, sort_keys=True)
    first = render_pr_summary(candidate, profile(fields=["status", "findings", "warnings"]))
    assert first == render_pr_summary(candidate, profile(fields=["status", "findings", "warnings"]))
    assert json.dumps(candidate, sort_keys=True) == before


def test_japanese_pr_summary_localizes_chrome_and_preserves_approved_values() -> None:
    fields = [
        "status",
        "outcomeSummary",
        "taskOverview",
        "deliveredChanges",
        "findings",
        "risks",
        "warnings",
        "residualRisks",
    ]
    english = render_pr_summary(sample_outcome(), profile(fields=fields), language="en")
    japanese = render_pr_summary(sample_outcome(), profile(fields=fields), language="ja-JP")

    assert "## タスク結果の概要" in japanese
    assert "- 状態: `completed_with_warnings`" in japanese
    assert "- 結果: Completed the bounded change; one warning remains." in japanese
    assert "- タスク概要: A reviewer-facing overview." in japanese
    assert "- 変更内容:" in japanese
    assert "- 検出事項:" in japanese
    assert "- リスク:" in japanese
    assert "- 警告:" in japanese
    assert "- 残存リスク:" in japanese
    for value in (
        "completed_with_warnings",
        "Completed the bounded change; one warning remains.",
        "A reviewer-facing overview.",
        "Added the guarded renderer",
        "Evidence gap",
        "Residual compatibility risk",
        "Review the remaining compatibility warning.",
    ):
        assert value in english
        assert value in japanese


def test_japanese_pr_summary_preserves_sanitization_and_opt_in_boundaries() -> None:
    candidate = sample_outcome()
    candidate["sections"]["warnings"] = [  # type: ignore[index]
        "token=fixture-sensitive",
        "/Users/example/private.txt",
        "80 percent productivity",
    ]
    fields = ["status", "warnings"]

    for language in ("en", "ja"):
        rendered = render_pr_summary(candidate, profile(fields=fields), language=language)
        assert "fixture-sensitive" not in rendered
        assert "/Users/example/private.txt" not in rendered
        assert "80 percent productivity" not in rendered
        assert "[redacted]" in rendered
        assert "[path redacted]" in rendered
        assert "[redacted unsupported quantitative claim]" in rendered
        assert ".ai/private.json" not in rendered
        assert "private stop detail" not in rendered

    assert render_pr_summary(candidate, profile(enabled=False), language="ja") == ""


def test_japanese_empty_state_uses_localized_marker() -> None:
    candidate = sample_outcome()
    candidate["sections"] = {"outcomeSummary": "", "warnings": []}

    rendered = render_pr_summary(
        candidate,
        profile(fields=["status", "outcomeSummary", "warnings"], language="ja"),
    )

    assert "- 状態: `completed_with_warnings`" in rendered
    assert "- 結果: なし" in rendered
    assert "- 警告: なし" in rendered


def test_cli_language_selection_and_unsupported_locale_fail_before_write(
    tmp_path, monkeypatch, capsys
) -> None:
    outcome_path = tmp_path / "outcome.json"
    profile_path = tmp_path / "profile.json"
    output_path = tmp_path / "summary.md"
    outcome_path.write_text(json.dumps(sample_outcome()), encoding="utf-8")
    profile_path.write_text(
        "reporting:\n"
        "  pullRequestSummary:\n"
        "    enabled: true\n"
        "    fields:\n"
        "      - status\n"
        "      - outcomeSummary\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai_render_task_outcome_pr.py",
            str(outcome_path),
            str(profile_path),
            "--language",
            "ja",
            "--output",
            str(output_path),
        ],
    )

    assert ai_render_task_outcome_pr._main() == 0
    assert "## タスク結果の概要" in output_path.read_text(encoding="utf-8")

    output_path.write_text("sentinel", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai_render_task_outcome_pr.py",
            str(outcome_path),
            str(profile_path),
            "--language",
            "fr",
            "--output",
            str(output_path),
        ],
    )

    assert ai_render_task_outcome_pr._main() == 2
    assert output_path.read_text(encoding="utf-8") == "sentinel"
    assert "unsupported Outcome locale" in capsys.readouterr().err
