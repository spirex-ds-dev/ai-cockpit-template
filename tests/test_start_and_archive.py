import json
import runpy
import sys
import subprocess
import fcntl
import pytest
import ai_archive_work_item
import ai_common
import ai_check_scope
import ai_start
import ai_start_receipt
from ai_start_receipt import build_receipt
from ai_start_receipt import current_branch
from ai_start_receipt import receipt_path
from ai_start_receipt import receipt_binding
from ai_start_receipt import skeleton_digest
from ai_start_receipt import scope_digest
from ai_start_receipt import validate_receipt


def test_start_and_archive_use_clean_git_environment():
    assert all(not key.startswith("GIT_") for key in ai_common.clean_git_environment())


def test_start_receipt_binds_contract_and_rejects_tampering(tmp_path):
    contract = {
        "contractVersion": 2,
        "workItemId": "receipt_task",
        "mode": "code",
        "title": "Receipt",
        "baseCommit": "a" * 40,
        "scope": ["src", "tests"],
    }
    receipt = build_receipt(contract, timestamp="2026-07-17T00:00:00+00:00")
    contract["startReceipt"] = receipt_binding(receipt)
    assert receipt["contractSkeletonDigest"] == skeleton_digest(contract)
    assert validate_receipt(contract, receipt, project_root=tmp_path) == []

    tampered = dict(receipt)
    tampered["baseCommit"] = "b" * 40
    assert "Start Receipt baseCommit does not match Contract" in validate_receipt(
        contract, tampered, project_root=tmp_path
    )


def test_start_receipt_rejects_missing_binding_and_receipt():
    contract = {
        "contractVersion": 2,
        "workItemId": "receipt_task",
        "baseCommit": "a" * 40,
        "scope": [],
    }
    assert validate_receipt(contract, None) == ["Start Receipt is missing"]
    receipt = build_receipt(contract)
    assert "Contract startReceipt binding is missing" in validate_receipt(contract, receipt)


def test_start_receipt_rejects_malformed_fields_and_binding():
    contract = {
        "contractVersion": 2,
        "workItemId": "receipt_task",
        "mode": "code",
        "title": "Receipt",
        "baseCommit": "a" * 40,
        "scope": [],
    }
    receipt = build_receipt(contract, timestamp="not-a-timestamp")
    receipt.update(
        {
            "receiptVersion": 99,
            "workItemId": "other",
            "receiptPath": "wrong.json",
            "baseCommit": "b" * 40,
            "initialScopeDigest": "short",
            "contractSkeletonDigest": "short",
        }
    )
    contract["startReceipt"] = {"path": "wrong.json"}
    issues = validate_receipt(contract, receipt)
    assert len(issues) >= 7
    assert "Start Receipt receiptVersion is unsupported" in issues
    assert "Start Receipt startTimestamp is not ISO-8601" in issues
    assert "Start Receipt initialScopeDigest must be a SHA-256 digest" in issues
    assert "Start Receipt contractSkeletonDigest must be a SHA-256 digest" in issues


def test_start_receipt_helpers_and_tracked_validation(monkeypatch, tmp_path):
    contract = {
        "contractVersion": 2,
        "workItemId": "receipt_task",
        "mode": "code",
        "title": "Receipt",
        "baseCommit": "a" * 40,
        "scope": ["src"],
    }
    receipt = build_receipt(contract, timestamp="2026-07-17T00:00:00+00:00", project_root=tmp_path)
    contract["startReceipt"] = receipt_binding(receipt)
    assert len(scope_digest(contract["scope"])) == 64
    assert receipt_path("receipt_task", project_root=tmp_path).name == "receipt_task.json"
    assert isinstance(current_branch(project_root=tmp_path), str)

    class Result:
        returncode = 1

    monkeypatch.setattr("ai_start_receipt.subprocess.run", lambda *args, **kwargs: Result())
    assert "Start Receipt is not Git-tracked" in validate_receipt(
        contract, receipt, project_root=tmp_path, require_tracked=True
    )


def test_start_receipt_cli_success_and_fail_closed_paths(monkeypatch, tmp_path):
    contract_path = tmp_path / "contract.json"
    receipt_file = tmp_path / "receipt.json"
    contract_path.write_text(json.dumps({"workItemId": "receipt_task"}), encoding="utf-8")
    receipt_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(ai_start_receipt, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start_receipt, "receipt_path", lambda _work_item_id: receipt_file)
    monkeypatch.setattr(ai_start_receipt, "validate_receipt", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_start_receipt.py", "--contract", "contract.json", "--receipt", "receipt.json"],
    )
    assert ai_start_receipt.main() == 0

    monkeypatch.setattr(ai_start_receipt, "validate_receipt", lambda *args, **kwargs: ["bad"])
    assert ai_start_receipt.main() == 1

    monkeypatch.setattr(sys, "argv", ["ai_start_receipt.py", "--contract", "missing.json"])
    assert ai_start_receipt.main() == 1


def test_start_receipt_rejects_invalid_contract_shapes_and_bad_file(monkeypatch, tmp_path):
    for contract in (
        {},
        {"workItemId": "task", "scope": "bad", "baseCommit": "a" * 40},
        {"workItemId": "task", "scope": [1], "baseCommit": ""},
        {"workItemId": "task", "scope": [], "baseCommit": ""},
    ):
        with pytest.raises(ValueError):
            build_receipt(contract, project_root=tmp_path)

    contract_path = tmp_path / "contract.json"
    receipt_file = tmp_path / "receipt.json"
    contract_path.write_text(json.dumps({"workItemId": "task"}), encoding="utf-8")
    receipt_file.write_text("not-json", encoding="utf-8")
    monkeypatch.setattr(ai_start_receipt, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start_receipt, "receipt_path", lambda _work_item_id: receipt_file)
    monkeypatch.setattr(sys, "argv", ["ai_start_receipt.py", "--contract", "contract.json"])
    assert ai_start_receipt.main() == 1

    monkeypatch.setattr(sys, "argv", ["ai_start_receipt.py", "--contract", "missing.json"])
    with pytest.raises(SystemExit):
        runpy.run_path(ai_start_receipt.__file__, run_name="__main__")


def test_scope_guard_adds_bound_receipt_path(monkeypatch):
    class Observation:
        def check_passed(self, **_kwargs):
            return None

        def check_failed(self, **_kwargs):
            return None

        def guard_violation(self, **_kwargs):
            return None

    contract = {
        "workItemId": "receipt_task",
        "scope": ["scripts/ai_start.py"],
        "outOfScope": [],
        "startReceipt": {"path": ".ai/work-items/starts/receipt_task.json"},
    }
    monkeypatch.setattr(ai_check_scope, "load_json", lambda _path: contract)
    monkeypatch.setattr(
        ai_check_scope,
        "changed_paths",
        lambda _contract: [".ai/work-items/starts/receipt_task.json"],
    )
    monkeypatch.setattr(ai_check_scope, "simple_yaml_lists", lambda _path: {})
    monkeypatch.setattr(ai_check_scope, "create_observability", lambda **_kwargs: Observation())
    monkeypatch.setattr(ai_check_scope, "elapsed_ms", lambda _start: 1)
    monkeypatch.setattr(sys, "argv", ["ai_check_scope.py", "contract.json"])
    assert ai_check_scope.main() == 0

    contract["outOfScope"] = [".ai/work-items/starts/**"]
    assert ai_check_scope.main() == 1

    contract["outOfScope"] = []
    contract["destructiveChangePolicy"] = {
        "allowed": True,
        "requiresHumanApproval": False,
        "allowPatterns": [".ai/work-items/starts/**"],
    }
    monkeypatch.setattr(sys, "argv", ["ai_check_scope.py", "contract.json", "--verbose"])
    assert ai_check_scope.main() == 0

    contract["destructiveChangePolicy"]["allowPatterns"] = []
    monkeypatch.setattr(sys, "argv", ["ai_check_scope.py", "contract.json", "--verbose"])
    assert ai_check_scope.main() == 0


def test_start_receipt_missing_fields_fails_closed():
    contract = {"workItemId": "receipt_task", "baseCommit": "a" * 40, "scope": []}
    issues = validate_receipt(contract, {})
    assert "Start Receipt missing field: receiptVersion" in issues
    assert "Start Receipt missing field: contractSkeletonDigest" in issues


def test_journey_policy_keeps_refactor_contract_boundaries():
    acceptance, guidelines, out_of_scope, destructive = ai_start.journey_policy("refactor")

    assert (
        "Code structural changes are completed without changing functional behavior." in acceptance
    )
    assert "Zero functional changes allowed." in guidelines
    assert "Adding new features" in out_of_scope
    assert destructive["allowed"] is False


def archive_contract(mode: str = "review") -> dict[str, object]:
    return {
        "contractVersion": 2,
        "workItemId": "task",
        "mode": mode,
        "title": "Task",
        "baseCommit": "a" * 40,
        "baselineDirtyPaths": [],
        "scope": [
            "scripts/ai_archive_work_item.py",
            "tests/test_start_and_archive.py",
            ".ai/cockpit/current_status.md",
            ".ai/work-items/archive/**",
        ],
        "outOfScope": ["Product source changes"],
        "sources": [{"path": "scripts/ai_archive_work_item.py", "reason": "fixture"}],
        "unknowns": [],
        "notCodable": False,
        "acceptance": ["done"],
        "verification": [{"check": "quality", "required": True}],
        "riskAssessment": {"level": "low", "riskTypes": [], "reason": "fixture"},
        "agentCapability": {
            "canImplement": True,
            "canVerify": True,
            "needsHumanDecision": False,
            "blockedReason": "",
        },
        "executionDecision": {"status": "continue", "reason": "fixture"},
        "checkpointPolicy": {
            "requiredBeforeFinish": False,
            "requiredStages": [],
            "reason": "fixture",
        },
        "destructiveChangePolicy": {
            "allowed": False,
            "requiresHumanApproval": True,
            "allowPatterns": [],
        },
        "rollbackNote": "revert",
    }


def archive_summary(*, verification_result: str = "passed") -> dict[str, object]:
    return {
        "summaryVersion": 2,
        "workItemId": "task",
        "contractPath": ".ai/work-items/active/task.contract.json",
        "changedFiles": [
            {"path": ".ai/work-items/active/task.contract.json", "reason": "contract"},
            {"path": ".ai/work-items/active/task.summary.json", "reason": "summary"},
            {"path": ".ai/work-items/active/task.review.json", "reason": "review"},
        ],
        "sourcesUsed": ["scripts/ai_archive_work_item.py"],
        "verification": [
            {"check": "quality", "result": verification_result},
            {
                "check": "aiSummary",
                "result": "passed",
                "worktreeDigest": "a" * 64,
            },
        ],
        "unknownsRemaining": [],
        "risk": {"level": "low", "detail": "fixture"},
        "generatedFiles": [],
        "destructiveChanges": [],
        "observedIssues": [],
    }


def stub_active_status(monkeypatch):
    monkeypatch.setattr(ai_start, "write_active_status", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ai_start, "run_make", lambda *_args, **_kwargs: (0, ""))


def test_ai_start_refreshes_only_stale_no_active_status(monkeypatch):
    stale = (
        "cockpit status Changed Files do not match current Git changes; run `make repair-ai-status`"
    )
    no_active_stale = (
        "cockpit status no-active state must not persist changed files; run `make repair-ai-status`"
    )
    calls = []
    monkeypatch.setattr(ai_start, "write_no_active_status", lambda path: calls.append(path))
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])

    assert ai_start.refresh_stale_no_active_status([stale]) == []
    assert calls == [ai_start.DEFAULT_STATUS]
    assert ai_start.refresh_stale_no_active_status([no_active_stale]) == []
    assert calls == [ai_start.DEFAULT_STATUS, ai_start.DEFAULT_STATUS]
    assert ai_start.refresh_stale_no_active_status(["different lifecycle error"]) == [
        "different lifecycle error"
    ]


def test_ai_start_default_contains_agent_risk_gate(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    monkeypatch.setattr(ai_start, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_start, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])
    monkeypatch.setattr(ai_start, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_start, "capture_dirty_baseline", lambda: [])
    stub_active_status(monkeypatch)
    monkeypatch.setattr(
        ai_start,
        "create_observability",
        lambda **_: type("Obs", (), {"work_item_started": lambda *a, **k: None})(),
    )
    monkeypatch.setattr(sys, "argv", ["ai_start.py", "--task", "sample", "--mode", "code"])

    assert ai_start.main() == 0
    contract = json.loads((active / "sample.contract.json").read_text(encoding="utf-8"))
    checks = [item["check"] for item in contract["verification"]]
    assert "aiAgentRisk" in checks
    assert "aiCheckpoint" in checks
    assert "aiReviewPolicy" in checks
    assert "aiDiffOwnership" in checks
    assert contract["contractVersion"] == 2
    assert contract["notCodable"] is False
    assert contract["baseCommit"] == "a" * 40
    assert contract["checkpointPolicy"]["requiredStages"] == ["before_edit", "before_finish"]
    assert ".ai/cockpit/current_status.md" in contract["scope"]
    receipt = tmp_path / ".ai" / "work-items" / "starts" / "sample.json"
    assert receipt.exists()
    assert json.loads(receipt.read_text(encoding="utf-8"))["workItemId"] == "sample"


def test_ai_start_fails_closed_when_preflight_gate_blocks(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    monkeypatch.setattr(ai_start, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_start, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])
    monkeypatch.setattr(ai_start, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_start, "capture_dirty_baseline", lambda: [])
    monkeypatch.setattr(ai_start, "write_active_status", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ai_start, "run_make", lambda *_args, **_kwargs: (1, "gate blocked"))
    monkeypatch.setattr(
        ai_start,
        "create_observability",
        lambda **_: type("Obs", (), {"work_item_started": lambda *a, **k: None})(),
    )
    monkeypatch.setattr(sys, "argv", ["ai_start.py", "--task", "blocked", "--mode", "code"])

    assert ai_start.main() == 1
    assert (active / "blocked.contract.json").exists()


def test_ai_start_requires_initial_commit(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    monkeypatch.setattr(ai_start, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_start, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])
    monkeypatch.setattr(ai_start, "current_head", lambda: "")
    stub_active_status(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["ai_start.py", "--task", "sample"])

    assert ai_start.validate_start_state("sample", force=False) is None
    assert ai_start.main() == 1
    assert not (active / "sample.contract.json").exists()


def test_ai_start_refuses_when_an_active_work_item_already_exists(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    (active / "existing.contract.json").write_text(
        json.dumps({"workItemId": "existing"}), encoding="utf-8"
    )
    (active / "existing.summary.json").write_text(
        json.dumps({"workItemId": "existing"}), encoding="utf-8"
    )
    monkeypatch.setattr(ai_start, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_start, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])
    monkeypatch.setattr(ai_start, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_start, "capture_dirty_baseline", lambda: [])
    stub_active_status(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["ai_start.py", "--task", "sample"])

    assert ai_start.main() == 1
    assert not (active / "sample.contract.json").exists()
    assert not (active / "sample.summary.json").exists()


def test_ai_start_refuses_when_start_lock_is_held(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    monkeypatch.setattr(ai_start, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_start, "PROJECT_ROOT", tmp_path)
    lock_path = ai_start.start_lock_path()
    lock_handle = lock_path.open("a+", encoding="utf-8")
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])
    monkeypatch.setattr(ai_start, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_start, "capture_dirty_baseline", lambda: [])
    stub_active_status(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["ai_start.py", "--task", "sample"])

    try:
        assert ai_start.main() == 1
        assert not (active / "sample.contract.json").exists()
        assert not (active / "sample.summary.json").exists()
    finally:
        lock_handle.close()
        lock_path.unlink(missing_ok=True)


def test_archive_refuses_to_overwrite_existing_audit_record(tmp_path, monkeypatch):
    active = tmp_path / "active"
    archive = tmp_path / "archive"
    active.mkdir()
    contract = active / "task.contract.json"
    contract.write_text(json.dumps(archive_contract("review")), encoding="utf-8")
    year_dir = archive / str(__import__("datetime").datetime.now().year)
    year_dir.mkdir(parents=True)
    (year_dir / contract.name).write_text("existing", encoding="utf-8")
    monkeypatch.setattr(ai_archive_work_item, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_archive_work_item, "ARCHIVE_BASE_DIR", archive)
    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["ai_archive_work_item.py", str(contract)])

    assert ai_archive_work_item.main() == 1


def test_archive_dry_run_and_successful_review_item(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    archive = tmp_path / ".ai" / "work-items" / "archive"
    active.mkdir(parents=True)
    contract = active / "task.contract.json"
    contract.write_text(json.dumps(archive_contract("review")), encoding="utf-8")
    monkeypatch.setattr(ai_archive_work_item, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_archive_work_item, "ARCHIVE_BASE_DIR", archive)
    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["ai_archive_work_item.py", str(contract), "--dry-run"])
    assert ai_archive_work_item.main() == 0
    assert contract.exists()

    calls = []

    def fake_run(cmd, cwd=None, check=False, **kwargs):
        calls.append(cmd)
        return None

    observer = type("Obs", (), {"record": lambda *_args, **_kwargs: None})()
    monkeypatch.setattr(ai_archive_work_item, "create_observability", lambda **_kwargs: observer)
    monkeypatch.setattr(ai_archive_work_item.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["ai_archive_work_item.py", str(contract)])
    assert ai_archive_work_item.main() == 0
    assert not contract.exists()
    assert list(archive.glob("*/task.contract.json"))
    assert any(
        any(str(part).endswith("ai_generate_status.py") for part in cmd) and "--no-active" in cmd
        for cmd in calls
    )
    index = json.loads((archive / "index.json").read_text(encoding="utf-8"))
    assert index["indexVersion"] == 1
    assert index["entries"][0]["workItemId"] == "task"
    assert index["entries"][0]["contractPath"].endswith("task.contract.json")


def test_archive_code_item_rewrites_summary_paths(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    archive = tmp_path / ".ai" / "work-items" / "archive"
    active.mkdir(parents=True)
    contract = active / "task.contract.json"
    summary = active / "task.summary.json"
    review = active / "task.review.json"
    contract.write_text(json.dumps(archive_contract("code")), encoding="utf-8")
    summary.write_text(json.dumps(archive_summary()), encoding="utf-8")
    review.write_text(json.dumps({"workItemId": "task", "result": "ok"}), encoding="utf-8")
    monkeypatch.setattr(ai_archive_work_item, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_archive_work_item, "ARCHIVE_BASE_DIR", archive)
    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_archive_work_item, "validate_contract", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ai_archive_work_item, "validate_summary", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        ai_archive_work_item,
        "create_observability",
        lambda **_kwargs: type("Obs", (), {"record": lambda *_args, **_kwargs: None})(),
    )
    monkeypatch.setattr(ai_archive_work_item.subprocess, "run", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        ai_archive_work_item, "_current_worktree_digest", lambda _contract: "a" * 64
    )
    monkeypatch.setattr(sys, "argv", ["ai_archive_work_item.py", str(contract)])

    assert ai_archive_work_item.main() == 0
    archived_summary = next(archive.glob("*/task.summary.json"))
    data = json.loads(archived_summary.read_text(encoding="utf-8"))
    assert data["archiveSequence"] == 1
    assert "/active/" not in data["contractPath"]
    assert all(
        "/archive/" in item["path"] or item["path"] == ".ai/cockpit/current_status.md"
        for item in data["changedFiles"]
    )
    assert any(item["path"].endswith("task.review.json") for item in data["changedFiles"])
    assert any(item["path"] == ".ai/cockpit/current_status.md" for item in data["changedFiles"])
    index = json.loads((archive / "index.json").read_text(encoding="utf-8"))
    assert index["entries"][0]["summaryPath"].endswith("task.summary.json")
    assert len(index["entries"][0]["contractSha256"]) == 64
    assert len(index["entries"][0]["summarySha256"]) == 64


def test_archive_rolls_back_when_status_regeneration_fails(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    archive = tmp_path / ".ai" / "work-items" / "archive"
    active.mkdir(parents=True)
    contract = active / "task.contract.json"
    summary = active / "task.summary.json"
    contract.write_text(json.dumps(archive_contract("code")), encoding="utf-8")
    summary.write_text(json.dumps(archive_summary()), encoding="utf-8")
    monkeypatch.setattr(ai_archive_work_item, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_archive_work_item, "ARCHIVE_BASE_DIR", archive)
    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_archive_work_item, "validate_contract", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ai_archive_work_item, "validate_summary", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        ai_archive_work_item, "_current_worktree_digest", lambda _contract: "a" * 64
    )

    def fake_run(cmd, cwd=None, check=False):
        if any(str(part).endswith("ai_generate_status.py") for part in cmd):
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
        return None

    monkeypatch.setattr(ai_archive_work_item.subprocess, "run", fake_run)
    monkeypatch.setattr(
        ai_archive_work_item,
        "create_observability",
        lambda **_kwargs: type("Obs", (), {"record": lambda *_args, **_kwargs: None})(),
    )
    monkeypatch.setattr(sys, "argv", ["ai_archive_work_item.py", str(contract)])

    assert ai_archive_work_item.main() == 1
    assert contract.exists()
    assert summary.exists()
    assert not list(archive.glob("*/task.contract.json"))


def test_archive_rolls_back_when_index_write_fails(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    archive = tmp_path / ".ai" / "work-items" / "archive"
    active.mkdir(parents=True)
    contract = active / "task.contract.json"
    summary = active / "task.summary.json"
    contract.write_text(json.dumps(archive_contract("code")), encoding="utf-8")
    summary.write_text(json.dumps(archive_summary()), encoding="utf-8")
    monkeypatch.setattr(ai_archive_work_item, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_archive_work_item, "ARCHIVE_BASE_DIR", archive)
    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_archive_work_item, "validate_contract", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ai_archive_work_item, "validate_summary", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        ai_archive_work_item, "_current_worktree_digest", lambda _contract: "a" * 64
    )
    monkeypatch.setattr(ai_archive_work_item.subprocess, "run", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        ai_archive_work_item,
        "_write_archive_index",
        lambda _index: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr(
        ai_archive_work_item,
        "create_observability",
        lambda **_kwargs: type("Obs", (), {"record": lambda *_args, **_kwargs: None})(),
    )
    monkeypatch.setattr(sys, "argv", ["ai_archive_work_item.py", str(contract)])

    assert ai_archive_work_item.main() == 1
    assert contract.exists()
    assert summary.exists()
    assert not list(archive.glob("*/task.contract.json"))


def test_archive_rejects_invalid_summary_before_moving_files(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    archive = tmp_path / ".ai" / "work-items" / "archive"
    active.mkdir(parents=True)
    contract = active / "task.contract.json"
    summary = active / "task.summary.json"
    contract.write_text(json.dumps(archive_contract("code")), encoding="utf-8")
    summary.write_text(json.dumps(archive_summary(verification_result="not_run")), encoding="utf-8")
    monkeypatch.setattr(ai_archive_work_item, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_archive_work_item, "ARCHIVE_BASE_DIR", archive)
    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["ai_archive_work_item.py", str(contract)])

    assert ai_archive_work_item.main() == 1
    assert contract.exists()
    assert summary.exists()
    assert not list(archive.rglob("task.contract.json"))


def test_archive_rejects_stale_worktree_digest_before_moving_files(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    archive = tmp_path / ".ai" / "work-items" / "archive"
    active.mkdir(parents=True)
    contract = active / "task.contract.json"
    summary = active / "task.summary.json"
    contract.write_text(json.dumps(archive_contract("code")), encoding="utf-8")
    summary_data = archive_summary()
    summary_data["verification"] = [
        {"check": "quality", "result": "passed"},
        {"check": "aiSummary", "result": "passed", "worktreeDigest": "b" * 64},
    ]
    summary.write_text(json.dumps(summary_data), encoding="utf-8")
    monkeypatch.setattr(ai_archive_work_item, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_archive_work_item, "ARCHIVE_BASE_DIR", archive)
    monkeypatch.setattr(ai_archive_work_item, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ai_archive_work_item, "_current_worktree_digest", lambda _contract: "a" * 64
    )
    monkeypatch.setattr(sys, "argv", ["ai_archive_work_item.py", str(contract)])

    assert ai_archive_work_item.main() == 1
    assert contract.exists()
    assert summary.exists()
    assert not list(archive.rglob("task.contract.json"))


def test_ai_start_journeys(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    monkeypatch.setattr(ai_start, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_start, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])
    monkeypatch.setattr(ai_start, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_start, "capture_dirty_baseline", lambda: [])
    stub_active_status(monkeypatch)
    monkeypatch.setattr(
        ai_start,
        "create_observability",
        lambda **_: type("Obs", (), {"work_item_started": lambda *a, **k: None})(),
    )

    # Test refactor journey
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_start.py", "--task", "refactor_task", "--mode", "code", "--journey", "refactor"],
    )
    assert ai_start.main() == 0
    contract = json.loads((active / "refactor_task.contract.json").read_text(encoding="utf-8"))
    summary = json.loads((active / "refactor_task.summary.json").read_text(encoding="utf-8"))
    assert "Zero functional changes allowed." in contract["guidelines"]
    assert "Adding new features" in contract["outOfScope"]
    assert contract["destructiveChangePolicy"]["allowed"] is False
    assert any(
        item["guideline"] == "Zero functional changes allowed."
        for item in summary["guidelinesCompliance"]
    )

    for path in active.glob("*.json"):
        path.unlink()

    # Test cleanup journey
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai_start.py", "--task", "cleanup_task", "--mode", "code", "--journey", "cleanup"],
    )
    assert ai_start.main() == 0
    contract_c = json.loads((active / "cleanup_task.contract.json").read_text(encoding="utf-8"))
    assert contract_c["destructiveChangePolicy"]["allowed"] is False
    assert contract_c["destructiveChangePolicy"]["requiresHumanApproval"] is True


def test_ai_start_generates_active_status(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    generated = []
    monkeypatch.setattr(ai_start, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_start, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])
    monkeypatch.setattr(ai_start, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_start, "capture_dirty_baseline", lambda: [])
    monkeypatch.setattr(
        ai_start,
        "write_active_status",
        lambda contract, summary, **_kwargs: generated.append((contract, summary)),
    )
    monkeypatch.setattr(ai_start, "run_make", lambda *_args, **_kwargs: (0, ""))
    monkeypatch.setattr(
        ai_start,
        "create_observability",
        lambda **_: type("Obs", (), {"work_item_started": lambda *a, **k: None})(),
    )
    monkeypatch.setattr(sys, "argv", ["ai_start.py", "--task", "status_task", "--mode", "code"])

    assert ai_start.main() == 0
    assert generated == [
        (active / "status_task.contract.json", active / "status_task.summary.json"),
        (active / "status_task.contract.json", active / "status_task.summary.json"),
    ]


def test_ai_start_rolls_back_pair_when_status_generation_fails(tmp_path, monkeypatch):
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    status = tmp_path / ".ai" / "cockpit" / "current_status.md"
    status.parent.mkdir(parents=True)
    status.write_text("previous status\n", encoding="utf-8")
    monkeypatch.setattr(ai_start, "ACTIVE_DIR", active)
    monkeypatch.setattr(ai_start, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [])
    monkeypatch.setattr(ai_start, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(ai_start, "capture_dirty_baseline", lambda: [])
    monkeypatch.setattr(
        ai_start,
        "write_active_status",
        lambda *_: (_ for _ in ()).throw(RuntimeError("status failed")),
    )
    monkeypatch.setattr(sys, "argv", ["ai_start.py", "--task", "status_task", "--mode", "code"])

    assert ai_start.main() == 1
    assert not list(active.glob("status_task.*.json"))
    assert status.read_text(encoding="utf-8") == "previous status\n"
