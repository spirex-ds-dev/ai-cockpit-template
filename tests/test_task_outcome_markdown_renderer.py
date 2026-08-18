"""Focused tests for the standalone derived Markdown renderer."""

from copy import deepcopy

from scripts.ai_generate_task_outcome import generate_outcome
from scripts.ai_render_task_outcome import render_task_outcome


def outcome() -> dict[str, object]:
    bindings = {
        "taskId": "task-outcome-markdown-renderer",
        "contractDigest": "a" * 64,
        "summaryDigest": "b" * 64,
        "verificationDigest": "c" * 64,
        "baseCommit": "1" * 40,
        "headCommit": "2" * 40,
        "pullRequest": {"number": 17, "url": "https://example.test/pull/17"},
        "aiCockpitVersion": "1.0",
        "generatorVersion": "1.0",
    }
    return generate_outcome("task-outcome-markdown-renderer", bindings)


def test_empty_report_has_all_sections_and_none_markers() -> None:
    rendered = render_task_outcome(outcome())
    assert rendered.startswith("# Task Outcome: task-outcome-markdown-renderer")
    assert rendered.count("## ") >= 17
    assert rendered.count("None") >= 10


def test_structured_items_and_conditional_language_are_readable() -> None:
    candidate = outcome()
    candidate["status"] = "completed_with_warnings"
    candidate["sections"]["findings"] = [{"title": "Evidence gap", "severity": "medium"}]
    candidate["sections"]["avoidedImpact"] = ["If not detected, could have led to a false claim."]
    candidate["sections"]["humanDecisions"] = ["Owner approved the bounded change"]
    rendered = render_task_outcome(candidate)
    assert "Status: `completed_with_warnings`" in rendered
    assert "- Evidence gap" in rendered
    assert "If not detected" in rendered
    assert "Owner approved" in rendered


def test_blocked_diagnostics_are_visible_in_markdown() -> None:
    candidate = outcome()
    candidate.update(
        {
            "status": "blocked",
            "humanStatusColor": "red",
            "failedGate": "quality",
            "recoveryCondition": "Run a passing quality retry.",
        }
    )

    rendered = render_task_outcome(candidate)

    assert "Human Status: `red`" in rendered
    assert "Failed Gate: `quality`" in rendered
    assert "Recovery Condition: Run a passing quality retry." in rendered


def test_rendering_is_deterministic_and_does_not_mutate_input() -> None:
    candidate = outcome()
    before = deepcopy(candidate)
    assert render_task_outcome(candidate) == render_task_outcome(candidate)
    assert candidate == before


def test_implementation_approach_renders_customer_summary_before_evidence() -> None:
    candidate = outcome()
    candidate["sections"]["implementationApproach"] = {
        "status": "complete",
        "summary": {
            "status": "verified",
            "text": "Customers can understand the governed implementation path.",
        },
        "mechanism": {
            "status": "verified",
            "text": "The Outcome renderer projects the structured approach.",
        },
        "affectedComponents": [
            {
                "component": "Task Outcome",
                "detail": "The Markdown view includes the approach section.",
                "status": "verified",
            }
        ],
        "designDecisions": [],
        "technicalDetails": [
            {
                "topic": "Evidence binding",
                "detail": "The output retains the repository evidence reference.",
                "status": "verified",
            }
        ],
        "evidence": [
            {
                "claim": "The renderer emits the approach section.",
                "source": "scripts/ai_render_task_outcome.py",
                "subject": "implementationApproach",
                "status": "verified",
            }
        ],
    }

    rendered = render_task_outcome(candidate)

    assert "## Implementation Approach" in rendered
    assert "Customers can understand the governed implementation path." in rendered
    assert "scripts/ai_render_task_outcome.py#implementationApproach" in rendered
    assert rendered.index("Customers can understand") < rendered.index("### Technical details")
    assert rendered.index("### Technical details") < rendered.index("### Evidence")
