import json
import sys

import ai_check_agent_risk
import ai_finish
import ai_generate_human_report as human
from ai_check_task_outcome import validate_outcome
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
    assert state["humanStatusColor"] == "green"
    assert state["completionFact"] == "All declared finish checks passed."


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


def test_pre_archive_critical_coverage_records_success_and_failure(monkeypatch):
    class Observer:
        def __init__(self):
            self.events = []

        def check_started(self, **kwargs):
            self.events.append(("started", kwargs))

        def check_passed(self, **kwargs):
            self.events.append(("passed", kwargs))

        def check_failed(self, **kwargs):
            self.events.append(("failed", kwargs))

    contract = {"workItemId": "example-task", "baseCommit": "a" * 40}
    observer = Observer()
    monkeypatch.setattr(ai_finish, "run", lambda _command: (0, 17, "coverage passed"))

    assert ai_finish.run_pre_archive_critical_coverage(contract, obs=observer) == (
        0,
        "coverage passed",
    )
    assert observer.events[0][0] == "started"
    assert observer.events[0][1]["command"] == (
        "make check-changed-critical-coverage AI_BASE_COMMIT="
        + "a" * 40
        + " CONTRACT=.ai/work-items/active/example-task.contract.json"
    )
    assert observer.events[1][0] == "passed"

    monkeypatch.setattr(ai_finish, "run", lambda _command: (1, 19, "coverage failed"))
    assert ai_finish.run_pre_archive_critical_coverage(contract, obs=observer) == (
        1,
        "coverage failed",
    )
    assert observer.events[-1][0] == "failed"


def test_pre_archive_critical_coverage_requires_contract_base():
    assert ai_finish.pre_archive_critical_coverage_command({"workItemId": "example-task"}) == (
        None,
        "Contract baseCommit is required for pre-archive critical coverage",
    )


def test_pre_archive_critical_coverage_requires_work_item_and_preserves_plain_failure_text():
    class Observer:
        def check_started(self, **_kwargs):
            raise AssertionError("missing Contract identity must not invoke the gate")

    assert ai_finish.pre_archive_critical_coverage_command({"baseCommit": "a" * 40}) == (
        None,
        "pre-archive changed-critical coverage requires a Work Item id",
    )
    assert ai_finish.run_pre_archive_critical_coverage(
        {"baseCommit": "a" * 40}, obs=Observer()
    ) == (2, "pre-archive changed-critical coverage requires a Work Item id")
    assert ai_finish.outcome_failure_message("quality", "lint command failed") == (
        "Finish blocked at quality: lint command failed"
    )
    assert ai_finish.verification_priority({"check": "aiStatusCheck"}) == 30


def test_failed_check_selection_uses_latest_failure_and_fails_closed_on_bad_summary(tmp_path):
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "verification": [
                    {"check": "quality", "result": "failed"},
                    {"check": "aiSummary", "result": "passed"},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert ai_finish.failed_check_from_summary(summary_path, "verification") == "quality"
    summary_path.write_text(json.dumps({"verification": {}}), encoding="utf-8")
    assert ai_finish.failed_check_from_summary(summary_path, "verification") == "verification"
    summary_path.write_text(
        json.dumps({"verification": [{"check": "", "result": "failed"}]}), encoding="utf-8"
    )
    assert ai_finish.failed_check_from_summary(summary_path, "verification") == "verification"
    assert (
        ai_finish.failed_check_from_summary(tmp_path / "missing.json", "verification")
        == "verification"
    )


def test_blocked_finish_failure_preserves_gate_exit_status(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ai_finish, "write_blocked_outcome", lambda *_args, **_kwargs: (True, "persisted")
    )

    assert (
        ai_finish.return_blocked_finish_failure(
            task="example-task",
            contract_path=tmp_path / "contract.json",
            summary_path=tmp_path / "summary.json",
            failed_check="preArchiveCriticalCoverage",
            failure_message="gate failed",
            code=2,
        )
        == 2
    )
    monkeypatch.setattr(
        ai_finish,
        "write_blocked_outcome",
        lambda *_args, **_kwargs: (False, "report refresh failed"),
    )
    assert (
        ai_finish.return_blocked_finish_failure(
            task="example-task",
            contract_path=tmp_path / "contract.json",
            summary_path=tmp_path / "summary.json",
            failed_check="preArchiveCriticalCoverage",
            failure_message="gate failed",
            code=1,
        )
        == 1
    )


def test_documentation_alignment_failure_is_reported_without_raising(tmp_path):
    summary_path = tmp_path / "summary.json"
    summary_path.write_text("not-json", encoding="utf-8")

    errors = ai_finish.documentation_alignment_issues(summary_path, {})

    assert len(errors) == 1
    assert errors[0].startswith("documentationAlignment could not be validated:")


def test_blocked_outcome_refreshes_the_exact_active_review_report(tmp_path, monkeypatch):
    task = "example-task"
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(
        json.dumps({"workItemId": task, "baseCommit": "a" * 40, "verification": []}),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps({"changedFiles": [], "verification": []}), encoding="utf-8")
    outcome_path = tmp_path / "outcome.json"
    markdown_path = tmp_path / "outcome.md"
    report_json = tmp_path / "task_report.json"
    report_markdown = tmp_path / "task_report.md"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "current_head", lambda: "b" * 40)
    monkeypatch.setattr(ai_finish, "_outcome_paths", lambda _task: (outcome_path, markdown_path))
    monkeypatch.setattr(ai_finish, "_human_report_paths", lambda: (report_json, report_markdown))

    ok, message = ai_finish.write_blocked_outcome(
        task,
        contract_path,
        summary_path,
        failed_check="quality",
        failure_message="quality gate failed",
    )

    assert ok, message
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    assert outcome["status"] == "blocked"
    assert validate_outcome(
        outcome, markdown_path.read_text(encoding="utf-8"), expected_task_id=task
    ).valid
    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert human.validate_human_report(report, outcome) == []
    assert report_markdown.read_text(encoding="utf-8") == human.render_human_report(report)
    assert any("quality gate failed" in warning for warning in outcome["sections"]["warnings"])


def test_blocked_outcome_normalizes_coverage_metrics_for_valid_report(tmp_path, monkeypatch):
    task = "example-task"
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(
        json.dumps({"workItemId": task, "baseCommit": "a" * 40, "verification": []}),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps({"changedFiles": [], "verification": []}), encoding="utf-8")
    outcome_path = tmp_path / "outcome.json"
    markdown_path = tmp_path / "outcome.md"
    report_json = tmp_path / "task_report.json"
    report_markdown = tmp_path / "task_report.md"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "current_head", lambda: "b" * 40)
    monkeypatch.setattr(ai_finish, "_outcome_paths", lambda _task: (outcome_path, markdown_path))
    monkeypatch.setattr(ai_finish, "_human_report_paths", lambda: (report_json, report_markdown))

    ok, message = ai_finish.write_blocked_outcome(
        task,
        contract_path,
        summary_path,
        failed_check="preArchiveCriticalCoverage",
        failure_message="scripts/ai_finish.py: 83.50% is below 85%",
    )

    assert ok, message
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    assert validate_outcome(
        outcome, markdown_path.read_text(encoding="utf-8"), expected_task_id=task
    ).valid
    assert "preArchiveCriticalCoverage" in outcome["sections"]["warnings"][0]
    assert "%" not in outcome["sections"]["warnings"][0]


def test_blocked_outcome_survives_report_refresh_failure(tmp_path, monkeypatch):
    task = "example-task"
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(
        json.dumps({"workItemId": task, "baseCommit": "a" * 40, "verification": []}),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps({"changedFiles": [], "verification": []}), encoding="utf-8")
    outcome_path = tmp_path / "outcome.json"
    markdown_path = tmp_path / "outcome.md"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "current_head", lambda: "b" * 40)
    monkeypatch.setattr(ai_finish, "_outcome_paths", lambda _task: (outcome_path, markdown_path))
    monkeypatch.setattr(
        ai_finish, "run_human_report_pipeline", lambda *_args: (False, "report writer unavailable")
    )

    ok, message = ai_finish.write_blocked_outcome(
        task,
        contract_path,
        summary_path,
        failed_check="aiDiffOwnership",
        failure_message="stale report blocks retry",
    )

    assert not ok
    assert "report writer unavailable" in message
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    assert outcome["status"] == "blocked"
    assert validate_outcome(
        outcome, markdown_path.read_text(encoding="utf-8"), expected_task_id=task
    ).valid


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


def test_human_report_pipeline_binds_generated_outcome_markdown_before_finish_recheck(
    tmp_path, monkeypatch
):
    task = "example-task"
    outcome_path = tmp_path / "outcome.json"
    outcome_markdown = tmp_path / "outcome.md"
    summary_path = tmp_path / "summary.json"
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
    outcome_markdown.write_text("# Task Outcome\n", encoding="utf-8")
    summary_path.write_text(
        json.dumps(
            {
                "changedFiles": [{"path": "outcome.md", "reason": "generated Outcome"}],
                "documentationAlignment": {
                    "checks": [{"area": "documentationCommandsCapability", "evidence": []}]
                },
            }
        ),
        encoding="utf-8",
    )
    report_json = tmp_path / "task_report.json"
    report_markdown = tmp_path / "task_report.md"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    active_contract = tmp_path / ".ai/work-items/active" / f"{task}.contract.json"
    active_contract.parent.mkdir(parents=True)
    active_contract.write_text(
        json.dumps({"scope": ["outcome.md", "task_report.json", "task_report.md"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_finish, "_outcome_paths", lambda _: (outcome_path, outcome_markdown))
    monkeypatch.setattr(ai_finish, "_human_report_paths", lambda: (report_json, report_markdown))

    ok, message = ai_finish.run_human_report_pipeline(task, summary_path)

    assert ok, message
    evidence = json.loads(summary_path.read_text(encoding="utf-8"))["documentationAlignment"][
        "checks"
    ][0]["evidence"]
    assert evidence == ["outcome.md", "task_report.md"]


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


def test_outcome_pipeline_preserves_non_risk_explanation_without_warning_or_yellow_status(
    tmp_path, monkeypatch
):
    task = "example-task"
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(
        json.dumps({"workItemId": task, "baseCommit": "a" * 40, "verification": []}),
        encoding="utf-8",
    )
    explanation = {
        "sourceWarning": "Hosted verification is not required by the Contract.",
        "reason": "The Contract does not require hosted verification for this Work Item.",
        "evidence": [{"source": "contract", "subject": "verification"}],
    }
    summary_path.write_text(
        json.dumps(
            {
                "verification": [],
                "changedFiles": [],
                "knownGaps": [],
                "nonRiskExplanations": [explanation],
            }
        ),
        encoding="utf-8",
    )
    json_path = tmp_path / "outcome.json"
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "_outcome_paths", lambda _: (json_path, tmp_path / "outcome.md"))

    ok, message = ai_finish.run_task_outcome_pipeline(task, summary_path, contract_path)

    assert ok, message
    outcome = json.loads(json_path.read_text(encoding="utf-8"))
    assert outcome["status"] == "completed"
    assert outcome["sections"]["warnings"] == []
    assert outcome["sections"]["limitations"] == []
    assert outcome["sections"]["nonRiskExplanations"] == [explanation]


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


def test_finish_archives_using_only_same_state_verification(tmp_path, monkeypatch):
    task = "example-task"
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    contract_path = active / f"{task}.contract.json"
    summary_path = active / f"{task}.summary.json"
    contract = {
        "contractVersion": 2,
        "workItemId": task,
        "baseCommit": "d" * 40,
        "scope": [],
        "verification": [],
    }
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    digest = ai_finish.worktree_digest_for_finish([], summary_path.relative_to(tmp_path).as_posix())
    summary_data = {
        "verification": [
            {
                "check": "aiSummary",
                "result": "passed",
                "runner": "ai_finish",
                "contractHash": __import__("hashlib")
                .sha256(contract_path.read_bytes())
                .hexdigest(),
                "commitSha": "a" * 40,
                "executionContractPath": contract_path.relative_to(tmp_path).as_posix(),
                "executionSummaryPath": summary_path.relative_to(tmp_path).as_posix(),
                "worktreeDigest": digest,
            }
        ]
    }
    summary_data["verification"][0]["outcomeInputDigest"] = ai_finish.outcome_input_digest(
        summary_data
    )
    summary_path.write_text(json.dumps(summary_data), encoding="utf-8")
    outcome_path = active / f"{task}.outcome.json"
    outcome_path.write_text(json.dumps(_outcome(task)), encoding="utf-8")

    class Observer:
        def lifecycle_phase_finished(self, *_args, **_kwargs):
            pass

        def check_started(self, **_kwargs):
            pass

        def check_passed(self, **_kwargs):
            pass

        def check_failed(self, **_kwargs):
            pass

        def work_item_finished(self, **_kwargs):
            pass

    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_finish, "ensure_work_item_branch", lambda: None)
    monkeypatch.setattr(ai_finish, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_finish, "changed_paths", lambda _contract: [])
    monkeypatch.setattr(ai_finish, "preview", lambda **_kwargs: [])
    monkeypatch.setattr(ai_finish, "create_observability", lambda **_kwargs: Observer())
    monkeypatch.setattr(
        ai_check_agent_risk, "validate_checkpoint_bindings", lambda *_args, **_kwargs: []
    )
    monkeypatch.setattr(ai_finish, "documentation_alignment_issues", lambda *_args: [])
    monkeypatch.setattr(
        ai_finish, "_outcome_paths", lambda _task: (outcome_path, active / f"{task}.outcome.md")
    )
    monkeypatch.setattr(ai_finish, "render_direct_outcome_report", lambda *_args: "report\n")
    monkeypatch.setattr(ai_finish, "refresh_archived_human_report", lambda _task: (True, "ok"))
    commands = []
    monkeypatch.setattr(
        ai_finish,
        "run",
        lambda command, **_kwargs: commands.append(command) or (0, 1, "ok"),
    )
    monkeypatch.setattr(sys, "argv", ["ai_finish.py", "--task", task, "--archive"])

    assert ai_finish.main() == 0
    assert commands == [
        [
            "make",
            "check-changed-critical-coverage",
            "AI_BASE_COMMIT=" + "d" * 40,
            "CONTRACT=.ai/work-items/active/example-task.contract.json",
        ],
        ["make", "archive-work-item", f"CONTRACT={contract_path.relative_to(tmp_path).as_posix()}"],
    ]


def test_reused_finish_verification_blocks_archive_when_documentation_alignment_is_incomplete(
    tmp_path, monkeypatch
):
    """A stale completed Outcome must not reach archive through the reuse path."""
    task = "example-task"
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    contract_path = active / f"{task}.contract.json"
    summary_path = active / f"{task}.summary.json"
    contract = {
        "contractVersion": 2,
        "workItemId": task,
        "baseCommit": "a" * 40,
        "scope": [],
        "verification": [],
    }
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    digest = ai_finish.worktree_digest_for_finish([], summary_path.relative_to(tmp_path).as_posix())
    summary_path.write_text(
        json.dumps(
            {
                "verification": [
                    {
                        "check": "aiSummary",
                        "result": "passed",
                        "runner": "ai_finish",
                        "contractHash": __import__("hashlib")
                        .sha256(contract_path.read_bytes())
                        .hexdigest(),
                        "commitSha": "a" * 40,
                        "executionContractPath": contract_path.relative_to(tmp_path).as_posix(),
                        "executionSummaryPath": summary_path.relative_to(tmp_path).as_posix(),
                        "worktreeDigest": digest,
                    }
                ],
                "documentationAlignment": {
                    "schemaVersion": 1,
                    "status": "not_checked",
                    "checkedAt": None,
                    "checks": [],
                },
            }
        ),
        encoding="utf-8",
    )
    (active / f"{task}.outcome.json").write_text(json.dumps(_outcome(task)), encoding="utf-8")
    (active / f"{task}.outcome.md").write_text("# Task Outcome\n", encoding="utf-8")

    class Observer:
        def lifecycle_phase_finished(self, *_args, **_kwargs):
            pass

        def check_started(self, **_kwargs):
            pass

        def check_passed(self, **_kwargs):
            pass

        def check_failed(self, **_kwargs):
            pass

        def work_item_finished(self, **_kwargs):
            pass

    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_finish, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_finish, "ensure_work_item_branch", lambda: None)
    monkeypatch.setattr(ai_finish, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_finish, "changed_paths", lambda _contract: [])
    monkeypatch.setattr(ai_finish, "preview", lambda **_kwargs: [])
    monkeypatch.setattr(ai_finish, "create_observability", lambda **_kwargs: Observer())
    monkeypatch.setattr(
        ai_check_agent_risk, "validate_checkpoint_bindings", lambda *_args, **_kwargs: []
    )
    blocked = {}
    monkeypatch.setattr(
        ai_finish,
        "return_blocked_finish_failure",
        lambda **kwargs: blocked.update(kwargs) or kwargs["code"],
    )
    commands = []
    monkeypatch.setattr(
        ai_finish,
        "run",
        lambda command, **_kwargs: commands.append(command) or (0, 1, "ok"),
    )
    monkeypatch.setattr(sys, "argv", ["ai_finish.py", "--task", task, "--archive"])

    assert ai_finish.main() == 1
    assert blocked["failed_check"] == "documentationAlignment"
    assert commands == []


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
