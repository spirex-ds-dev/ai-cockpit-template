import hashlib
import json

from ai_generate_task_outcome import generate_outcome
from ai_outcome_gate import validate_terminal_outcome
from ai_render_task_outcome import render_task_outcome


def _sha256_json(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _write_outcome_fixture(tmp_path, *, status="completed", color=None):
    task = "outcome-gate-task"
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    outcome_path = tmp_path / "outcome.json"
    markdown_path = tmp_path / "outcome.md"
    base = "1" * 40
    head = "2" * 40
    verification = [{"check": "quality", "result": "passed"}]
    contract_path.write_text(json.dumps({"workItemId": task, "baseCommit": base}), encoding="utf-8")
    summary_path.write_text(json.dumps({"verification": verification}), encoding="utf-8")
    outcome = generate_outcome(
        task,
        {
            "taskId": task,
            "contractDigest": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
            "summaryDigest": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            "verificationDigest": _sha256_json(verification),
            "baseCommit": base,
            "headCommit": head,
            "lifecycleStage": "pre_merge",
            "pullRequest": {"state": "not_created"},
            "aiCockpitVersion": "repository-governance",
            "generatorVersion": "1.2",
        },
        evidence={"status": status, "locale": "en"},
    )
    if color is not None:
        outcome["humanStatusColor"] = color
    outcome_path.write_text(json.dumps(outcome), encoding="utf-8")
    markdown_path.write_text(render_task_outcome(outcome), encoding="utf-8")
    return outcome_path, markdown_path, contract_path, summary_path, base, head


def test_terminal_gate_accepts_current_completed_green_outcome(tmp_path):
    outcome_path, markdown_path, contract_path, summary_path, base, head = _write_outcome_fixture(
        tmp_path
    )

    result = validate_terminal_outcome(
        outcome_path,
        markdown_path,
        expected_task_id="outcome-gate-task",
        contract_path=contract_path,
        summary_path=summary_path,
        expected_base_commit=base,
        expected_head_commit=head,
    )

    assert result.valid is True
    assert result.issues == ()


def test_terminal_gate_rejects_yellow_outcome(tmp_path):
    outcome_path, markdown_path, contract_path, summary_path, base, head = _write_outcome_fixture(
        tmp_path, status="needs_human_confirmation", color="yellow"
    )

    result = validate_terminal_outcome(
        outcome_path,
        markdown_path,
        expected_task_id="outcome-gate-task",
        contract_path=contract_path,
        summary_path=summary_path,
        expected_base_commit=base,
        expected_head_commit=head,
    )

    assert result.valid is False
    assert any("completed" in issue for issue in result.issues)
    assert any("green" in issue for issue in result.issues)


def test_terminal_gate_rejects_stale_summary_and_head_bindings(tmp_path):
    outcome_path, markdown_path, contract_path, summary_path, base, _head = _write_outcome_fixture(
        tmp_path
    )
    summary_path.write_text(
        json.dumps(
            {
                "verification": [
                    {"check": "quality", "result": "passed"},
                    {"check": "new", "result": "passed"},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = validate_terminal_outcome(
        outcome_path,
        markdown_path,
        expected_task_id="outcome-gate-task",
        contract_path=contract_path,
        summary_path=summary_path,
        expected_base_commit=base,
        expected_head_commit="3" * 40,
    )

    assert result.valid is False
    assert any("summaryDigest" in issue for issue in result.issues)
    assert any("verificationDigest" in issue for issue in result.issues)
    assert any("headCommit" in issue for issue in result.issues)
