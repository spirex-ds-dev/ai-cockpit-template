import json
import runpy
import sys
import subprocess
import fcntl
import hashlib
from pathlib import Path

import pytest
import ai_archive_work_item
import ai_common
import ai_check_scope
import ai_resume_work_item
import ai_start
import ai_start_receipt
from ai_resume_work_item import ResumeError
from ai_resume_work_item import resume_contract
from ai_start_receipt import build_receipt
from ai_start_receipt import current_branch
from ai_start_receipt import receipt_path
from ai_start_receipt import receipt_binding
from ai_start_receipt import skeleton_digest
from ai_start_receipt import scope_digest
from ai_start_receipt import validate_receipt
from ai_start_receipt import validate_resume_history


def test_start_and_archive_use_clean_git_environment():
    assert all(not key.startswith("GIT_") for key in ai_common.clean_git_environment())


def test_rewrite_archived_path_references_preserves_non_path_scalars():
    active = ".ai/work-items/active/task.contract.json"
    archived = ".ai/work-items/archive/2026/task.contract.json"
    evidence = {
        "path": active,
        "nested": [active, "make ai-finish CONTRACT=" + active, 622, True, None],
    }

    rewritten = ai_archive_work_item._rewrite_archived_path_references(evidence, {active: archived})

    assert rewritten == {
        "path": archived,
        "nested": [archived, "make ai-finish CONTRACT=" + active, 622, True, None],
    }


def test_start_preflight_can_skip_contract_validation_for_new_skeleton(monkeypatch):
    observed = {}

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **_kwargs):
        observed["command"] = command
        return Result()

    monkeypatch.setattr(ai_start.subprocess, "run", fake_run)
    assert (
        ai_start.run_make(
            "ai-preflight",
            contract=".ai/work-items/active/example.contract.json",
            variables=["AI_PREFLIGHT_VALIDATE_CONTRACT=false"],
        )[0]
        == 0
    )
    assert observed["command"][-1] == "AI_PREFLIGHT_VALIDATE_CONTRACT=false"


def test_next_available_task_id_resolves_archive_collision_before_creation():
    assert (
        ai_start.next_available_task_id(
            "publish-new-version",
            {"publish-new-version", "publish-new-version-20260725"},
            date="20260725",
        )
        == "publish-new-version-20260725-2"
    )


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


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_commit(root: Path, name: str, content: str) -> str:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(root, "add", name)
    _git(root, "commit", "-m", f"write {name}")
    return _git(root, "rev-parse", "HEAD")


def _write_predecessor_archive(root: Path, work_item_id: str, sequence: int) -> str:
    archive = root / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True, exist_ok=True)
    predecessor_contract = archive / f"{work_item_id}.contract.json"
    predecessor_summary = archive / f"{work_item_id}.summary.json"
    predecessor_contract.write_text(
        json.dumps({"workItemId": work_item_id}) + "\n", encoding="utf-8"
    )
    predecessor_summary.write_text(
        json.dumps({"workItemId": work_item_id}) + "\n", encoding="utf-8"
    )
    manifest = archive / f"{work_item_id}.archive-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": "ai-cockpit-archive-manifest",
                "manifestVersion": 1,
                "workItemId": work_item_id,
                "archiveSequence": sequence,
                "contractPath": (f".ai/work-items/archive/2026/{work_item_id}.contract.json"),
                "summaryPath": (f".ai/work-items/archive/2026/{work_item_id}.summary.json"),
                "contractSha256": hashlib.sha256(predecessor_contract.read_bytes()).hexdigest(),
                "summarySha256": hashlib.sha256(predecessor_summary.read_bytes()).hexdigest(),
                "generatedStatusExcluded": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return f".ai/work-items/archive/2026/{work_item_id}.archive-manifest.json"


def _closed_predecessor(work_item_id: str, merge_commit: str, manifest_path: str) -> dict:
    return {
        "workItemId": work_item_id,
        "status": "closed",
        "pr": {"merged": True, "mergeCommit": merge_commit},
        "closure": {
            "succeeded": True,
            "localBranchDeleted": True,
            "remoteBranchDeleted": True,
            "baseSynchronized": True,
            "evidence": manifest_path,
        },
    }


def _resume_fixture(tmp_path: Path) -> tuple[Path, Path, Path, str, str]:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.com")
    start = _write_commit(root, "seed.txt", "start\n")
    _git(root, "switch", "-c", "codex/paused-task")

    contract_path = root / ".ai/work-items/active/paused-task.contract.json"
    receipt_file = root / ".ai/work-items/starts/paused-task.json"
    contract_path.parent.mkdir(parents=True)
    receipt_file.parent.mkdir(parents=True)
    contract = {
        "contractVersion": 2,
        "workItemId": "paused-task",
        "mode": "code",
        "title": "Paused task",
        "baseCommit": start,
        "scope": ["src/**"],
    }
    receipt = build_receipt(
        contract,
        timestamp="2026-07-28T00:00:00+00:00",
        project_root=root,
    )
    contract["startReceipt"] = receipt_binding(receipt)
    receipt_file.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    _git(root, "switch", "main")
    target = _write_commit(root, "corrective.txt", "fixed\n")
    _git(root, "update-ref", "refs/remotes/origin/main", target)
    _git(root, "switch", "codex/paused-task")
    _git(root, "rebase", target)

    manifest = _write_predecessor_archive(root, "corrective", 1)
    contract["predecessorWorkItem"] = _closed_predecessor("corrective", target, manifest)
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    return root, contract_path, receipt_file, start, target


def test_resume_contract_appends_source_bound_lineage_without_rewriting_receipt(tmp_path):
    root, contract_path, receipt_file, start, target = _resume_fixture(tmp_path)
    original_receipt = receipt_file.read_bytes()
    original_binding = json.loads(contract_path.read_text(encoding="utf-8"))["startReceipt"]

    transition = resume_contract(
        contract_path,
        base_remote="origin",
        base_branch="main",
        timestamp="2026-07-28T01:00:00+00:00",
        project_root=root,
    )

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert transition["fromBaseCommit"] == start
    assert transition["toBaseCommit"] == target
    assert transition["predecessorMergeCommit"] == target
    assert transition["workBranch"] == "codex/paused-task"
    assert len(transition["priorContractDigest"]) == 64
    assert contract["baseCommit"] == target
    assert contract["resumeHistory"] == [transition]
    assert contract["startReceipt"] == original_binding
    assert receipt_file.read_bytes() == original_receipt
    assert validate_receipt(contract, receipt, project_root=root) == []


def test_resume_contract_appends_second_transition_without_rewriting_first(tmp_path):
    root, contract_path, receipt_file, _start, first_target = _resume_fixture(tmp_path)
    first = resume_contract(
        contract_path,
        base_remote="origin",
        base_branch="main",
        timestamp="2026-07-28T01:00:00+00:00",
        project_root=root,
    )

    _git(root, "switch", "main")
    second_target = _write_commit(root, "corrective-2.txt", "fixed again\n")
    _git(root, "update-ref", "refs/remotes/origin/main", second_target)
    _git(root, "switch", "codex/paused-task")
    _git(root, "rebase", second_target)
    manifest = _write_predecessor_archive(root, "corrective-2", 2)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["predecessorWorkItem"] = _closed_predecessor("corrective-2", second_target, manifest)
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

    second = resume_contract(
        contract_path,
        base_remote="origin",
        base_branch="main",
        timestamp="2026-07-28T02:00:00+00:00",
        project_root=root,
    )

    resumed = json.loads(contract_path.read_text(encoding="utf-8"))
    assert resumed["resumeHistory"][0] == first
    assert resumed["resumeHistory"][1] == second
    assert second["fromBaseCommit"] == first_target
    assert second["toBaseCommit"] == second_target
    assert (
        validate_receipt(
            resumed,
            json.loads(receipt_file.read_text(encoding="utf-8")),
            project_root=root,
        )
        == []
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda contract: contract.pop("resumeHistory"), "resumeHistory is required"),
        (
            lambda contract: contract["resumeHistory"][0].update({"resumeVersion": 99}),
            "resumeHistory[0].resumeVersion is unsupported",
        ),
        (
            lambda contract: contract["resumeHistory"][0].pop("priorContractDigest"),
            "resumeHistory[0] missing field: priorContractDigest",
        ),
        (
            lambda contract: contract["resumeHistory"][0].update({"fromBaseCommit": "f" * 40}),
            "resumeHistory[0].fromBaseCommit does not continue from the immutable Start Receipt",
        ),
        (
            lambda contract: contract.update({"baseCommit": "e" * 40}),
            "resumeHistory final toBaseCommit does not match Contract baseCommit",
        ),
        (
            lambda contract: contract["resumeHistory"][0].update(
                {"workBranch": "codex/different-task"}
            ),
            "workBranch does not match immutable Start Receipt",
        ),
    ],
)
def test_resume_history_rejects_direct_or_malformed_baseline_transition(
    tmp_path, mutation, expected
):
    root, contract_path, receipt_file, _start, _target = _resume_fixture(tmp_path)
    resume_contract(
        contract_path,
        base_remote="origin",
        base_branch="main",
        timestamp="2026-07-28T01:00:00+00:00",
        project_root=root,
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    mutation(contract)
    assert any(
        expected in issue for issue in validate_resume_history(contract, receipt, project_root=root)
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda contract: contract["predecessorWorkItem"].update({"status": "open"}),
            "predecessor status must be closed",
        ),
        (
            lambda contract: contract["predecessorWorkItem"]["pr"].update(
                {"mergeCommit": "f" * 40}
            ),
            "predecessor merge commit must equal resume target",
        ),
        (
            lambda contract: contract["predecessorWorkItem"]["closure"].update(
                {"evidence": ".ai/work-items/archive/2026/missing.archive-manifest.json"}
            ),
            "predecessor archive manifest is missing",
        ),
    ],
)
def test_resume_contract_is_atomic_when_source_binding_fails(tmp_path, mutation, expected):
    root, contract_path, receipt_file, _start, _target = _resume_fixture(tmp_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    mutation(contract)
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    before_contract = contract_path.read_bytes()
    before_receipt = receipt_file.read_bytes()

    with pytest.raises(ResumeError, match=expected):
        resume_contract(
            contract_path,
            base_remote="origin",
            base_branch="main",
            timestamp="2026-07-28T01:00:00+00:00",
            project_root=root,
        )

    assert contract_path.read_bytes() == before_contract
    assert receipt_file.read_bytes() == before_receipt


def test_resume_history_rejects_non_ancestor_and_manifest_digest_mismatch(tmp_path, monkeypatch):
    root, contract_path, receipt_file, _start, _target = _resume_fixture(tmp_path)
    resume_contract(
        contract_path,
        base_remote="origin",
        base_branch="main",
        timestamp="2026-07-28T01:00:00+00:00",
        project_root=root,
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    manifest_path = root / contract["resumeHistory"][0]["predecessorManifestPath"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["summarySha256"] = "f" * 64
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    monkeypatch.setattr(ai_start_receipt, "_git_is_ancestor", lambda *_args: False)

    issues = validate_resume_history(contract, receipt, project_root=root)

    assert "resumeHistory[0]: fromBaseCommit is not an ancestor of toBaseCommit" in issues
    assert "resumeHistory[0]: predecessor manifest summarySha256 does not match" in issues


def test_resume_contract_rejects_wrong_original_branch_and_missing_remote_atomically(
    tmp_path,
):
    root, contract_path, receipt_file, _start, _target = _resume_fixture(tmp_path)
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    receipt["baseBranch"] = "codex/other-task"
    receipt_file.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    before = contract_path.read_bytes()

    with pytest.raises(ResumeError, match="current branch does not match immutable Start Receipt"):
        resume_contract(
            contract_path,
            base_remote="origin",
            base_branch="main",
            project_root=root,
        )
    assert contract_path.read_bytes() == before

    receipt["baseBranch"] = "codex/paused-task"
    receipt_file.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ResumeError, match="Needed a single revision"):
        resume_contract(
            contract_path,
            base_remote="missing",
            base_branch="main",
            project_root=root,
        )
    assert contract_path.read_bytes() == before


def test_resume_cli_reports_success_and_failure(tmp_path, monkeypatch, capsys):
    root, contract_path, _receipt_file, _start, _target = _resume_fixture(tmp_path)
    monkeypatch.setattr(ai_resume_work_item, "PROJECT_ROOT", root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai_resume_work_item.py",
            "--contract",
            str(contract_path.relative_to(root)),
            "--base-remote",
            "origin",
            "--base-branch",
            "main",
        ],
    )
    assert ai_resume_work_item.main() == 0
    assert "Work Item resume recorded:" in capsys.readouterr().out

    def reject(*_args, **_kwargs):
        raise ResumeError("rejected")

    monkeypatch.setattr(ai_resume_work_item, "resume_contract", reject)
    assert ai_resume_work_item.main() == 1
    assert "Work Item resume failed: rejected" in capsys.readouterr().out


def test_resume_helpers_reject_malformed_inputs_with_specific_diagnostics(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(ResumeError, match="Contract cannot be read"):
        ai_resume_work_item._load_json(malformed, "Contract")

    malformed.write_text("[]", encoding="utf-8")
    with pytest.raises(ResumeError, match="Contract must be a JSON object"):
        ai_resume_work_item._load_json(malformed, "Contract")

    target = "a" * 40
    with pytest.raises(ResumeError, match="predecessorWorkItem must be an evidence object"):
        ai_resume_work_item._predecessor_transition_fields({}, target)

    predecessor = _closed_predecessor("corrective", target, "manifest.json")
    predecessor["closure"]["localBranchDeleted"] = False
    with pytest.raises(ResumeError, match="predecessor closure is incomplete"):
        ai_resume_work_item._predecessor_transition_fields(
            {"predecessorWorkItem": predecessor}, target
        )

    predecessor = _closed_predecessor("", target, "manifest.json")
    with pytest.raises(ResumeError, match="predecessor Work Item ID is missing"):
        ai_resume_work_item._predecessor_transition_fields(
            {"predecessorWorkItem": predecessor}, target
        )

    predecessor = _closed_predecessor("corrective", target, "")
    with pytest.raises(ResumeError, match="predecessor archive manifest path is missing"):
        ai_resume_work_item._predecessor_transition_fields(
            {"predecessorWorkItem": predecessor}, target
        )


def test_resume_contract_rejects_contract_outside_repository(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside.contract.json"
    outside.write_text('{"workItemId":"outside"}\n', encoding="utf-8")

    with pytest.raises(ResumeError, match="Contract must be inside the repository"):
        resume_contract(
            outside,
            base_remote="origin",
            base_branch="main",
            project_root=repository,
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
        "budgetImpact": {"expectedMetrics": {"archiveGrowth": 1}},
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
        "documentationAlignment": {
            "status": "aligned",
            "checkedAt": "2026-07-28T00:00:00+00:00",
            "checks": [
                {
                    "area": "plan",
                    "status": "not_applicable",
                    "evidence": [],
                    "reason": "fixture",
                },
                {
                    "area": "contractSummaryEvidence",
                    "status": "aligned",
                    "evidence": [".ai/work-items/active/task.contract.json"],
                    "reason": "fixture",
                },
                {
                    "area": "documentationCommandsCapability",
                    "status": "not_applicable",
                    "evidence": [],
                    "reason": "fixture",
                },
                {
                    "area": "multilingualSemantics",
                    "status": "not_applicable",
                    "evidence": [],
                    "reason": "fixture",
                },
                {
                    "area": "limitationsUnknownsHistory",
                    "status": "aligned",
                    "evidence": [".ai/work-items/active/task.contract.json"],
                    "reason": "fixture",
                },
            ],
        },
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


def test_ai_start_failed_no_active_refresh_restores_status_bytes(tmp_path, monkeypatch):
    status = tmp_path / ".ai" / "cockpit" / "current_status.md"
    status.parent.mkdir(parents=True)
    status.write_bytes(b"original status\n")
    stale = (
        "cockpit status no-active state must not persist changed files; run `make repair-ai-status`"
    )
    persistent = "worktree remains dirty"

    monkeypatch.setattr(ai_start, "DEFAULT_STATUS", status)
    monkeypatch.setattr(
        ai_start,
        "write_no_active_status",
        lambda path: path.write_bytes(b"regenerated status\n"),
    )
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: [persistent])

    assert ai_start.refresh_stale_no_active_status([stale]) == [persistent]
    assert status.read_bytes() == b"original status\n"


def test_ai_start_failed_no_active_refresh_removes_new_status(tmp_path, monkeypatch):
    status = tmp_path / ".ai" / "cockpit" / "current_status.md"
    stale = (
        "cockpit status no-active state must not persist changed files; run `make repair-ai-status`"
    )

    monkeypatch.setattr(ai_start, "DEFAULT_STATUS", status)

    def write_status(path):
        path.parent.mkdir(parents=True)
        path.write_bytes(b"regenerated status\n")

    monkeypatch.setattr(ai_start, "write_no_active_status", write_status)
    monkeypatch.setattr(ai_start, "validate_status_consistency", lambda: ["worktree remains dirty"])

    assert ai_start.refresh_stale_no_active_status([stale]) == ["worktree remains dirty"]
    assert not status.exists()


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
    summary = json.loads((active / "sample.summary.json").read_text(encoding="utf-8"))
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
    assert summary["documentationAlignment"]["status"] == "not_checked"
    assert {item["area"] for item in summary["documentationAlignment"]["checks"]} == {
        "plan",
        "contractSummaryEvidence",
        "documentationCommandsCapability",
        "multilingualSemantics",
        "limitationsUnknownsHistory",
    }
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
    success = active / "task.success.json"
    outcome = active / "task.outcome.json"
    markdown = active / "task.outcome.md"
    events = active / "task.events.jsonl"
    contract.write_text(json.dumps(archive_contract("code")), encoding="utf-8")
    summary.write_text(json.dumps(archive_summary()), encoding="utf-8")
    review.write_text(json.dumps({"workItemId": "task", "result": "ok"}), encoding="utf-8")
    success.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "workItemId": "task",
                "criteria": [
                    {
                        "id": "SC-TASK",
                        "statement": "Archived with the Work Item.",
                        "evidenceHints": ["tests/test_start_and_archive.py"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    outcome.write_text('{"workItemId":"task"}\n', encoding="utf-8")
    markdown.write_text("# Task Outcome: task\n", encoding="utf-8")
    events.write_text('{"eventType":"completed"}\n', encoding="utf-8")
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
    assert next(archive.glob("*/task.success.json")).exists()
    assert (
        next(archive.glob("*/task.outcome.json")).read_text(encoding="utf-8")
        == '{"workItemId":"task"}\n'
    )
    assert next(archive.glob("*/task.outcome.md")).exists()
    assert next(archive.glob("*/task.events.jsonl")).exists()
    data = json.loads(archived_summary.read_text(encoding="utf-8"))
    assert data["archiveSequence"] == 1
    assert "/active/" not in data["contractPath"]
    assert all(
        "/active/" not in evidence
        for check in data["documentationAlignment"]["checks"]
        for evidence in check["evidence"]
    )
    assert any(
        evidence.endswith("/archive/2026/task.contract.json")
        for check in data["documentationAlignment"]["checks"]
        for evidence in check["evidence"]
    )
    assert all(
        "/archive/" in item["path"] or item["path"] == ".ai/cockpit/current_status.md"
        for item in data["changedFiles"]
    )
    assert any(item["path"].endswith("task.review.json") for item in data["changedFiles"])
    assert any(item["path"].endswith("task.outcome.json") for item in data["changedFiles"])
    assert any(item["path"] == ".ai/cockpit/current_status.md" for item in data["changedFiles"])
    index = json.loads((archive / "index.json").read_text(encoding="utf-8"))
    assert index["entries"][0]["summaryPath"].endswith("task.summary.json")
    assert len(index["entries"][0]["contractSha256"]) == 64
    assert len(index["entries"][0]["summarySha256"]) == 64
    manifest = next(archive.glob("*/task.archive-manifest.json"))
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["format"] == "ai-cockpit-archive-manifest"
    assert manifest_data["generatedStatusExcluded"] is True
    assert {item["path"].split("/")[-1] for item in manifest_data["outcomeArtifacts"]} == {
        "task.outcome.json",
        "task.outcome.md",
        "task.events.jsonl",
    }
    assert len(index["entries"][0]["manifestSha256"]) == 64
    assert index["entries"][0]["manifestPath"].endswith("task.archive-manifest.json")


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
