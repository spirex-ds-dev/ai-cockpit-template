import json
import sys

import ai_finish
import ai_generate_human_report as human
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


def test_human_report_pipeline_generates_review_artifacts_and_summary_binding(
    tmp_path, monkeypatch
):
    task = "example-task"
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "changedFiles": [],
                "documentationAlignment": {
                    "checks": [{"area": "documentationCommandsCapability", "evidence": []}]
                },
            }
        ),
        encoding="utf-8",
    )
    outcome_path = tmp_path / "outcome.json"
    outcome_value = _outcome(task)
    outcome_value.update(
        {
            "format": "ai-cockpit-task-outcome",
            "schemaVersion": 1,
            "bindings": {
                "taskId": task,
                "contractDigest": "a" * 64,
                "summaryDigest": "b" * 64,
                "verificationDigest": "c" * 64,
                "baseCommit": "d" * 40,
                "headCommit": "e" * 40,
                "lifecycleStage": "pre_merge",
                "pullRequest": {"state": "not_created"},
                "aiCockpitVersion": "repository-governance",
                "generatorVersion": "1.0",
            },
        }
    )
    outcome_path.write_text(json.dumps(outcome_value), encoding="utf-8")
    json_path = tmp_path / "task_report.json"
    markdown_path = tmp_path / "task_report.md"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    contract_path = tmp_path / ".ai/work-items/active" / f"{task}.contract.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(
        json.dumps({"scope": ["task_report.json", "task_report.md"]}), encoding="utf-8"
    )
    monkeypatch.setattr(
        ai_finish, "_outcome_paths", lambda _: (outcome_path, tmp_path / "outcome.md")
    )
    monkeypatch.setattr(ai_finish, "_human_report_paths", lambda: (json_path, markdown_path))

    ok, message = ai_finish.run_human_report_pipeline(task, summary_path)

    assert ok
    assert message == "Human Benefit Report pipeline passed"
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert human.validate_human_report(report, outcome_value) == []
    assert markdown_path.read_text(encoding="utf-8") == human.render_human_report(report)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert {item["path"] for item in summary["changedFiles"]} == {
        "task_report.json",
        "task_report.md",
    }
    assert summary["documentationAlignment"]["checks"][0]["evidence"] == ["task_report.md"]


def test_archived_human_report_refreshes_after_outcome_path_rewrite(tmp_path, monkeypatch):
    task = "example-task"
    archive = tmp_path / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    outcome_value = _outcome(task)
    outcome_value.update(
        {
            "format": "ai-cockpit-task-outcome",
            "schemaVersion": 1,
            "bindings": {
                "taskId": task,
                "contractDigest": "a" * 64,
                "summaryDigest": "b" * 64,
                "verificationDigest": "c" * 64,
                "baseCommit": "d" * 40,
                "headCommit": "e" * 40,
                "lifecycleStage": "pre_merge",
                "pullRequest": {"state": "not_created"},
                "aiCockpitVersion": "repository-governance",
                "generatorVersion": "1.0",
            },
        }
    )
    outcome_path = archive / f"{task}.outcome.json"
    outcome_path.write_text(json.dumps(outcome_value), encoding="utf-8")
    json_path = tmp_path / ".ai/cockpit/task_report.json"
    markdown_path = tmp_path / ".ai/cockpit/task_report.md"
    json_path.parent.mkdir(parents=True)
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "_human_report_paths", lambda: (json_path, markdown_path))

    ok, message = ai_finish.refresh_archived_human_report(task)

    assert ok
    assert message == "Archived Human Benefit Report binding passed"
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert human.validate_human_report(report, outcome_value) == []


def test_unscoped_current_report_remains_generated_evidence_not_summary_ownership(
    tmp_path, monkeypatch
):
    task = "example-task"
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps({"changedFiles": []}), encoding="utf-8")
    outcome_path = tmp_path / "outcome.json"
    outcome_value = _outcome(task)
    outcome_value.update(
        {
            "format": "ai-cockpit-task-outcome",
            "schemaVersion": 1,
            "bindings": {
                "taskId": task,
                "contractDigest": "a" * 64,
                "summaryDigest": "b" * 64,
                "verificationDigest": "c" * 64,
                "baseCommit": "d" * 40,
                "headCommit": "e" * 40,
                "lifecycleStage": "pre_merge",
                "pullRequest": {"state": "not_created"},
                "aiCockpitVersion": "repository-governance",
                "generatorVersion": "1.0",
            },
        }
    )
    outcome_path.write_text(json.dumps(outcome_value), encoding="utf-8")
    contract_path = tmp_path / ".ai/work-items/active" / f"{task}.contract.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(json.dumps({"scope": ["fixture.txt"]}), encoding="utf-8")
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ai_finish, "_outcome_paths", lambda _: (outcome_path, tmp_path / "outcome.md")
    )

    ok, _ = ai_finish.run_human_report_pipeline(task, summary_path)

    assert ok
    assert json.loads(summary_path.read_text(encoding="utf-8"))["changedFiles"] == []


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


def test_outcome_pipeline_structures_legacy_known_gaps_as_limitations(tmp_path, monkeypatch):
    task = "example-task"
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(
        json.dumps({"workItemId": task, "baseCommit": "a" * 40, "verification": []}),
        encoding="utf-8",
    )
    warning = "Hosted provider checks were not_run."
    summary_path.write_text(
        json.dumps({"verification": [], "changedFiles": [], "knownGaps": [warning]}),
        encoding="utf-8",
    )
    json_path = tmp_path / "outcome.json"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "_outcome_paths", lambda _: (json_path, tmp_path / "outcome.md"))

    ok, message = ai_finish.run_task_outcome_pipeline(task, summary_path, contract_path)

    assert ok, message
    sections = json.loads(json_path.read_text(encoding="utf-8"))["sections"]
    assert sections["limitations"][0]["sourceWarning"] == warning
    assert sections["nonRiskExplanations"][0]["sourceWarning"] == warning
    assert sections["forbiddenClaims"]


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


def test_finish_defaults_to_active_outcome_and_accepts_conversation_language(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ai_finish.py", "--task", "example-task"])

    args = ai_finish.parse_args()

    assert args.archive is False
    assert args.language == "en"


def test_direct_outcome_report_is_localized_and_explicit_about_archive_boundary():
    outcome = _outcome("example-task")

    report = ai_finish.render_direct_outcome_report(outcome, "zh-CN")

    assert "工单结果报告" in report
    assert "任务结果: example-task" in report
    assert "归档必须显式执行" in report


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
