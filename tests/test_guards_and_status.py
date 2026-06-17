import json

import ai_check_backtrack
import ai_check_coverage_guard
import ai_checkpoint
import ai_generate_status


def test_backtrack_detects_deleted_test_and_work_item():
    items = ai_check_backtrack.detect_items([
        ("D", "tests/unit_test.py"),
        ("D", ".ai/work-items/archive/2026/task.summary.json"),
    ])
    assert {item.kind for item in items} == {"deleted_test", "removed_work_item_record"}


def test_coverage_detects_production_change_without_test(tmp_path, monkeypatch):
    policy = tmp_path / "coverage.yaml"
    policy.write_text(
        "production:\n  include:\n    - src/**\ntests:\n  include:\n    - tests/**\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_check_coverage_guard, "POLICY", policy)
    assert ai_check_coverage_guard.detect(["src/service.py"])
    assert ai_check_coverage_guard.detect(["src/service.py", "tests/test_service.py"]) == []


def test_checkpoint_next_action_stops_on_unknowns():
    contract = {"notCodable": False, "unknowns": ["decision"], "verification": []}
    assert ai_checkpoint.next_action(contract, None).startswith("Stop coding")


def test_retry_circuit_breaker_counts_consecutive_failures(tmp_path):
    log = tmp_path / "events.jsonl"
    events = [
        {"workItemId": "task", "eventType": "check_passed"},
        {"workItemId": "task", "eventType": "check_failed"},
        {"workItemId": "task", "eventType": "check_failed"},
    ]
    log.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
    assert ai_generate_status.consecutive_failure_count("task", log) == 2
    state, blockers = ai_generate_status.status_for(
        {"workItemId": "task", "notCodable": False, "unknowns": [], "verification": []},
        {"verification": []},
        retry_threshold=2,
        observability_log=log,
    )
    assert state == "blocked_by_ai_loop"
    assert blockers
