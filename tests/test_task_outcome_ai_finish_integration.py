import json
import os
import sys

import ai_finish
from scripts.ai_generate_task_outcome import generate_outcome
from scripts.ai_render_task_outcome import render_task_outcome
from ai_governance_compression import render_active_status


def _outcome(task: str) -> dict:
    sections = {
        "outcomeSummary": "Completed from structured evidence.",
        "taskOverview": "A governed Work Item.",
    }
    for key in (
        "deliveredChanges",
        "findings",
        "risks",
        "warnings",
        "interventions",
        "forcedStops",
        "resolutions",
        "recurrencePrevention",
        "avoidedImpact",
        "residualRisks",
        "humanDecisions",
        "evidence",
    ):
        sections[key] = [{"subject": "evidence"}] if key == "evidence" else []
    return {"workItemId": task, "status": "completed", "sections": sections}


def test_outcome_pipeline_orders_generation_validation_render_validation_and_records_link(
    tmp_path, monkeypatch
):
    task = "example-task"
    summary_path = tmp_path / "summary.json"
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(json.dumps({"taskId": task}), encoding="utf-8")
    summary_path.write_text(json.dumps({"taskOutcomeInput": "raw.json"}), encoding="utf-8")
    json_path = tmp_path / "outcome.json"
    markdown_path = tmp_path / "outcome.md"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "_outcome_paths", lambda _: (json_path, markdown_path))
    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command[1] if len(command) > 1 else command[0])
        if "generate_task_outcome" in " ".join(command):
            json_path.write_text(json.dumps(_outcome(task)), encoding="utf-8")
            markdown_path.write_text("# Task Outcome\n", encoding="utf-8")
        return 0, 1, "valid"

    monkeypatch.setattr(ai_finish, "run", fake_run)
    ok, message = ai_finish.run_task_outcome_pipeline(task, summary_path)

    assert ok
    assert message == "Outcome pipeline passed"
    assert calls[0].endswith("ai_generate_task_outcome.py")
    assert calls[1] == "-c"
    assert calls[2].endswith("ai_render_task_outcome.py")
    assert calls[3] == "-c"
    state = json.loads(summary_path.read_text(encoding="utf-8"))["taskOutcome"]
    assert state["markdownPath"] == "outcome.md"
    assert state["evidenceCount"] == 1


def test_outcome_pipeline_failure_preserves_raw_evidence_and_records_structured_failure(
    tmp_path, monkeypatch
):
    task = "example-task"
    summary_path = tmp_path / "summary.json"
    raw_path = tmp_path / "raw.json"
    raw = '{"taskId":"example-task","events":[{"eventType":"finding"}]}'
    raw_path.write_text(raw, encoding="utf-8")
    summary_path.write_text(json.dumps({"taskOutcomeInput": "raw.json"}), encoding="utf-8")
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ai_finish,
        "_outcome_paths",
        lambda _: (tmp_path / "outcome.json", tmp_path / "outcome.md"),
    )
    monkeypatch.setattr(ai_finish, "run", lambda *_args, **_kwargs: (1, 4, "schema: invalid"))

    ok, message = ai_finish.run_task_outcome_pipeline(task, summary_path)

    assert not ok
    assert "schema: invalid" in message
    assert raw_path.read_text(encoding="utf-8") == raw
    state = json.loads(summary_path.read_text(encoding="utf-8"))["taskOutcome"]
    assert state["status"] == "failed"
    assert state["rawEvidencePath"] == "raw.json"
    assert "error" in state


def test_outcome_pipeline_without_contract_fails_closed(tmp_path):
    summary_path = tmp_path / "summary.json"
    summary_path.write_text("{}", encoding="utf-8")
    assert ai_finish.run_task_outcome_pipeline("example-task", summary_path) == (
        False,
        "mandatory Task Outcome requires the active Contract",
    )


def test_outcome_pipeline_without_opt_in_derives_a_pre_merge_report(tmp_path, monkeypatch):
    task = "example-task"
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(
        json.dumps(
            {
                "workItemId": task,
                "baseCommit": "a" * 40,
                "verification": [],
            }
        ),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(
            {
                "verification": [],
                "changedFiles": [{"path": "fixture.txt", "reason": "fixture"}],
                "observedIssues": [],
            }
        ),
        encoding="utf-8",
    )
    json_path = tmp_path / "outcome.json"
    markdown_path = tmp_path / "outcome.md"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "_outcome_paths", lambda _: (json_path, markdown_path))

    ok, _ = ai_finish.run_task_outcome_pipeline(task, summary_path, contract_path)

    assert ok
    outcome = json.loads(json_path.read_text(encoding="utf-8"))
    assert outcome["bindings"]["lifecycleStage"] == "pre_merge"
    assert outcome["bindings"]["pullRequest"] == {"state": "not_created"}
    assert markdown_path.exists()
    recorded_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert recorded_summary["taskOutcome"]["markdownPath"] == "outcome.md"
    assert {item["path"] for item in recorded_summary["changedFiles"]} == {
        "fixture.txt",
        "outcome.json",
        "outcome.md",
    }


def test_outcome_pipeline_missing_input_fails_closed(tmp_path, monkeypatch):
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps({"taskOutcomeInput": "missing-raw.json"}), encoding="utf-8")
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    ok, message = ai_finish.run_task_outcome_pipeline("example-task", summary_path)
    assert not ok
    assert "does not exist" in message


def test_finish_execution_priority_runs_summary_after_mandatory_outcome_and_quality():
    assert ai_finish.finish_execution_priority(
        {"check": "aiSummary"}
    ) > ai_finish.finish_execution_priority({"check": "aiStatus"})
    assert ai_finish.finish_execution_priority(
        {"check": "aiSummary"}
    ) > ai_finish.finish_execution_priority({"check": "quality"})


def test_finish_defaults_to_active_outcome_and_requires_explicit_archive(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ai_finish.py", "--task", "example-task"])
    assert ai_finish.parse_args().archive is False
    monkeypatch.setattr(sys, "argv", ["ai_finish.py", "--task", "example-task", "--archive"])
    assert ai_finish.parse_args().archive is True


def test_finish_accepts_an_explicit_conversation_report_language(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["ai_finish.py", "--task", "example-task", "--language", "zh-CN"]
    )

    assert ai_finish.parse_args().language == "zh-CN"
    assert "工单结果报告" in ai_finish.REPORT_BOUNDARY_TEXT["zh-CN"][0]
    assert "タスク結果レポート" in ai_finish.REPORT_BOUNDARY_TEXT["ja"][0]
    assert "Task Outcome Report" in ai_finish.REPORT_BOUNDARY_TEXT["en"][0]


def test_finish_removes_report_language_make_context_before_nested_commands(monkeypatch):
    monkeypatch.setenv("REPORT_LANGUAGE", "zh-CN")
    monkeypatch.setenv("MAKEFLAGS", "REPORT_LANGUAGE=zh-CN")
    monkeypatch.setenv("MAKEOVERRIDES", "${-*-command-variables-*-}")

    ai_finish.isolate_report_language_from_nested_commands()

    assert "REPORT_LANGUAGE" not in os.environ
    assert "MAKEFLAGS" not in os.environ
    assert "MAKEOVERRIDES" not in os.environ


def test_pre_merge_outcome_projects_summary_issues_risks_and_human_corrections(
    tmp_path, monkeypatch
):
    task = "example-task"
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(
        json.dumps({"workItemId": task, "baseCommit": "a" * 40, "verification": []}),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(
            {
                "verification": [],
                "changedFiles": [],
                "observedIssues": [
                    {
                        "id": "RFE-100",
                        "category": "process_issue",
                        "severity": "high",
                        "stage": "finish",
                        "description": "Finish archived before human report.",
                        "state": "resolved",
                        "resolution": "Default finish now preserves the active Outcome.",
                    }
                ],
                "residualRisks": [
                    {
                        "level": "medium",
                        "area": "hosted_ci",
                        "detail": "Exact-Head hosted CI remains required.",
                    }
                ],
                "userCorrectionsCaptured": [
                    {"request": "Report before archive.", "action": "Require explicit archive."}
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "current_head", lambda: "b" * 40)

    payload = ai_finish._pre_merge_outcome_input(task, contract_path, summary_path)
    outcome = generate_outcome(
        task, payload["bindings"], events=payload["events"], evidence=payload["evidence"]
    )
    assert outcome["sections"]["findings"][0]["findingFingerprint"] == "RFE-100"
    assert outcome["sections"]["findings"][0]["state"] == "resolved"
    assert (
        outcome["sections"]["resolutions"][0]["action"]
        == "Default finish now preserves the active Outcome."
    )
    assert outcome["sections"]["residualRisks"][0]["title"] == "hosted_ci"
    assert outcome["sections"]["humanDecisions"] == ["Report before archive."]


def test_rendered_outcome_keeps_human_decision_details_and_evidence_context():
    outcome = {
        "workItemId": "example-task",
        "status": "completed_with_warnings",
        "sections": {
            "outcomeSummary": "A process issue was detected and remains partially verified.",
            "taskOverview": "Governed corrective.",
            "deliveredChanges": ["scripts/ai_finish.py"],
            "findings": [
                {
                    "title": "RFE-100",
                    "category": "process",
                    "severity": "high",
                    "state": "unresolved",
                    "description": "Finish archived before human report.",
                    "evidence": [{"source": "summary.json", "subject": "RFE-100"}],
                }
            ],
            "risks": [],
            "warnings": [],
            "interventions": [],
            "forcedStops": [],
            "resolutions": [],
            "recurrencePrevention": [],
            "avoidedImpact": [],
            "residualRisks": [],
            "humanDecisions": ["Report before archive."],
            "evidence": [{"source": "summary.json", "subject": "Summary"}],
        },
    }

    rendered = render_task_outcome(outcome)

    assert "Category: process; Severity: high; State: unresolved" in rendered
    assert "Finish archived before human report." in rendered
    assert "Evidence: summary.json — RFE-100" in rendered
    assert "Report before archive." in rendered


def test_status_contains_only_outcome_link_count_and_status_not_full_report():
    status = render_active_status(
        {
            "recommendation": "needs_investigation",
            "signals": [],
            "evidence": {},
            "decisionDrivers": [],
        },
        work_item_id="example-task",
        mode="code",
        contract_path="contract.json",
        summary_path="summary.json",
        task_outcome={
            "status": "completed",
            "markdownPath": ".ai/work-items/active/example-task.outcome.md",
            "evidenceCount": 3,
        },
    )

    assert "Task Outcome" in status
    assert "example-task.outcome.md" in status
    assert "Evidence Count: `3`" in status
    assert "Full Outcome" not in status
    assert "score" not in status.lower()
