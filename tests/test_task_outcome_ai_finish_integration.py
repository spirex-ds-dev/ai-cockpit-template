import json

import ai_finish
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


def test_outcome_pipeline_without_input_is_compatible(tmp_path):
    summary_path = tmp_path / "summary.json"
    summary_path.write_text("{}", encoding="utf-8")
    assert ai_finish.run_task_outcome_pipeline("example-task", summary_path) == (
        True,
        "Outcome integration not requested: no taskOutcomeInput",
    )


def test_outcome_pipeline_missing_input_fails_closed(tmp_path, monkeypatch):
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps({"taskOutcomeInput": "missing-raw.json"}), encoding="utf-8")
    monkeypatch.setattr(ai_finish, "PROJECT_ROOT", tmp_path)
    ok, message = ai_finish.run_task_outcome_pipeline("example-task", summary_path)
    assert not ok
    assert "does not exist" in message


def test_finish_execution_priority_moves_summary_before_status_only_for_opt_in():
    assert ai_finish.finish_execution_priority(
        {"check": "aiSummary"}
    ) < ai_finish.finish_execution_priority({"check": "aiStatus"})
    assert ai_finish.verification_priority(
        {"check": "aiSummary"}
    ) > ai_finish.verification_priority({"check": "aiStatus"})


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
