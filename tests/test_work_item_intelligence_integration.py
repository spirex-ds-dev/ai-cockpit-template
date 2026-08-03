from __future__ import annotations

import json
import sys

import scripts.ai_work_item_status as status_cli
from scripts.ai_work_item_intelligence import append_fact, read_snapshot


def test_cli_returns_stable_not_found_envelope(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["ai_work_item_status.py", "--work-item", "missing-item"])
    assert status_cli.main() == 10
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "ok": False,
        "data": None,
        "error": {"code": "not_found", "message": "snapshot not found for missing-item"},
    }


def test_list_cli_delegates_only_to_read_query(monkeypatch, capsys) -> None:
    calls: list[dict[str, object]] = []

    def query(**kwargs):
        calls.append(kwargs)
        return {"schemaVersion": 1, "indexVersion": 0, "entries": []}

    monkeypatch.setattr(status_cli, "query", query)
    monkeypatch.setattr(
        sys, "argv", ["ai_work_item_status.py", "--list-active", "--state", "active"]
    )
    assert status_cli.main() == 0
    assert calls == [
        {
            "work_item": None,
            "state": "active",
            "pending_human_decisions": False,
            "eligible_action": None,
            "after_index_version": None,
            "schema_version": 1,
        }
    ]
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["context"] == {
        "scope": "current_worktree",
        "aggregatesAcrossWorktrees": False,
        "schedulerOwnership": "external_agent",
    }


def test_cli_passes_explicit_schema_version(monkeypatch, capsys) -> None:
    calls: list[dict[str, object]] = []

    def query(**kwargs):
        calls.append(kwargs)
        return {"schemaVersion": 2, "identity": {"workItemId": "version-item"}}

    monkeypatch.setattr(status_cli, "query", query)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_work_item_status.py", "--work-item", "version-item", "--schema-version", "2"],
    )
    assert status_cli.main() == 0
    assert calls[0]["schema_version"] == 2
    assert json.loads(capsys.readouterr().out)["data"]["schemaVersion"] == 2


def test_cli_defaults_to_v1_without_network_or_scheduler_side_effect(monkeypatch, capsys) -> None:
    calls: list[dict[str, object]] = []

    def query(**kwargs):
        calls.append(kwargs)
        return {"schemaVersion": 1, "identity": {"workItemId": "v1-item"}}

    monkeypatch.setattr(status_cli, "query", query)
    monkeypatch.setattr(sys, "argv", ["ai_work_item_status.py", "--work-item", "v1-item"])

    assert status_cli.main() == 0
    assert calls[0]["schema_version"] == 1
    assert json.loads(capsys.readouterr().out)["data"]["schemaVersion"] == 1


def test_cli_preserves_inconsistent_source_error_without_rebuild(monkeypatch, capsys) -> None:
    def query(**_kwargs):
        raise status_cli.IntelligenceError("inconsistent", "source digest mismatch")

    monkeypatch.setattr(status_cli, "query", query)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_work_item_status.py", "--work-item", "source-item", "--schema-version", "2"],
    )

    assert status_cli.main() == 12
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "inconsistent"


def test_v1_compatibility_omits_v2_completion_and_v2_exposes_current_state(tmp_path) -> None:
    append_fact("completion-cli-item", "verification_passed", {}, root=tmp_path)
    append_fact("completion-cli-item", "verification_failed", {}, root=tmp_path)

    v1 = read_snapshot("completion-cli-item", schema_version=1, root=tmp_path)
    v2 = read_snapshot("completion-cli-item", schema_version=2, root=tmp_path)

    assert "completion" not in v1
    assert v2["completion"]["verification"] == {
        "state": "invalidated",
        "lastPassedFactId": "completion-cli-item:1",
        "invalidatedBy": "completion-cli-item:2",
    }
