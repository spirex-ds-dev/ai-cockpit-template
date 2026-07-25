"""Tests for the opt-in, sanitized pull-request Outcome Summary."""

import json

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


def profile(*, enabled: bool = True, fields: list[str] | None = None) -> dict[str, object]:
    return {
        "reporting": {
            "pullRequestSummary": {
                "enabled": enabled,
                **({"fields": fields} if fields is not None else {}),
            }
        }
    }


def test_profile_must_explicitly_enable_pr_summary() -> None:
    assert render_pr_summary(sample_outcome(), {}) == ""
    assert render_pr_summary(sample_outcome(), profile(enabled=False)) == ""


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
