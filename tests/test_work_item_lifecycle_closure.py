from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
from pathlib import Path

import ai_close_work_item as closure
import pytest
from ai_observability import AiEventType


def test_lifecycle_phase_event_type_is_available_to_closure() -> None:
    assert AiEventType.LIFECYCLE_PHASE_FINISHED.value == "lifecycle_phase_finished"


def run_command(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )


def repository_runner(cwd: Path) -> closure.Runner:
    def run(args, check=False):
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        )
        converted = closure.CommandResult(
            result.returncode,
            result.stdout,
            result.stderr,
        )
        if check and converted.returncode != 0:
            raise RuntimeError(converted.stderr.strip() or "git command failed")
        return converted

    return run


def test_quality_gate_requires_at_least_85_percent_coverage() -> None:
    makefile = (closure.PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "--cov-fail-under=85" in makefile


def test_make_close_work_item_forwards_explicit_worktree_argument() -> None:
    result = subprocess.run(
        [
            "make",
            "-n",
            "ai-close-work-item",
            "TASK=example",
            "ARGS=--worktree /tmp/registered-child",
        ],
        cwd=closure.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert (
        'scripts/ai_close_work_item.py --task "example" --worktree /tmp/registered-child'
        in result.stdout
    )


def test_archived_evidence_uses_strict_summary_validation() -> None:
    source = inspect.getsource(closure._verify_archived_evidence)
    assert "legacy_archive=False" in source


def test_archived_evidence_rejects_non_green_current_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / ".ai/work-items/archive"
    archive_year = archive / "2026"
    archive_year.mkdir(parents=True)
    task = "current-green-gate"
    contract_path = archive_year / f"{task}.contract.json"
    contract_path.write_text(
        json.dumps({"contractVersion": 2, "workItemId": task, "baseCommit": "a" * 40}),
        encoding="utf-8",
    )
    contract_path.with_name(f"{task}.summary.json").write_text(
        json.dumps({"workItemId": task}), encoding="utf-8"
    )
    contract_path.with_name(f"{task}.outcome.json").write_text(
        json.dumps(
            {"workItemId": task, "status": "needs_human_confirmation", "humanStatusColor": "yellow"}
        ),
        encoding="utf-8",
    )
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    status = tmp_path / ".ai/cockpit/current_status.md"
    status.parent.mkdir(parents=True)
    status.write_text("- State: `no_active_work_item`\n", encoding="utf-8")
    monkeypatch.setattr(closure, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(closure, "ARCHIVE_DIR", archive)
    monkeypatch.setattr(closure, "ACTIVE_DIR", active)
    monkeypatch.setattr(closure, "STATUS_PATH", status)
    monkeypatch.setattr(closure, "validate_contract", lambda _contract: [])
    monkeypatch.setattr(closure, "validate_summary", lambda *_args, **_kwargs: [])

    with pytest.raises(RuntimeError, match="completed|green"):
        closure._verify_archived_evidence(task)


def prepare_superseded_archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    archive = tmp_path / ".ai/work-items/archive"
    contract = archive / "2026/example.contract.json"
    contract.parent.mkdir(parents=True)
    contract.write_text("{}", encoding="utf-8")
    contract.with_name("example.summary.json").write_text("{}", encoding="utf-8")
    outcome = contract.with_name("example.outcome.json")
    outcome.write_text(json.dumps({"workItemId": "example", "status": "blocked"}), encoding="utf-8")
    successor = {
        "workItemId": "successor",
        "branch": "codex/successor",
        "baseCommit": "a" * 40,
    }
    contract.with_name("example.successor-receipt.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "transition": "superseded",
                "predecessor": {"workItemId": "example"},
                "predecessorOutcomeDigest": hashlib.sha256(outcome.read_bytes()).hexdigest(),
                "successor": successor,
                "successorWorkItemId": successor["workItemId"],
                "issue": "https://github.com/spirex-ds-dev/ai-cockpit-template/issues/1",
                "authority": "user",
                "reason": "A verified successor owns the corrective delivery.",
            }
        ),
        encoding="utf-8",
    )
    active = tmp_path / ".ai/work-items/active"
    active.mkdir(parents=True)
    status = tmp_path / ".ai/cockpit/current_status.md"
    status.parent.mkdir(parents=True)
    status.write_text("- State: `no_active_work_item`\n", encoding="utf-8")
    monkeypatch.setattr(closure, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(closure, "ARCHIVE_DIR", archive)
    monkeypatch.setattr(closure, "ACTIVE_DIR", active)
    monkeypatch.setattr(closure, "STATUS_PATH", status)
    monkeypatch.setattr(closure, "validate_contract", lambda _contract: [])
    return contract


def test_superseded_archived_evidence_accepts_bound_failed_verification_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = prepare_superseded_archive(tmp_path, monkeypatch)
    monkeypatch.setattr(
        closure,
        "validate_summary",
        lambda *_args, **_kwargs: ["required verification is not passed: quality"],
    )

    assert closure._verify_archived_evidence("example") == contract


def test_superseded_archived_evidence_rejects_unrelated_summary_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare_superseded_archive(tmp_path, monkeypatch)
    monkeypatch.setattr(
        closure,
        "validate_summary",
        lambda *_args, **_kwargs: [
            "required verification is not passed: quality",
            "summary contractHash does not match Contract",
        ],
    )

    with pytest.raises(RuntimeError, match="summary contractHash does not match Contract"):
        closure._verify_archived_evidence("example")


def test_final_human_report_binds_provider_facts_outside_source_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract_path = tmp_path / ".ai/work-items/archive/2026/example.contract.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text("{}", encoding="utf-8")
    outcome = {
        "format": "ai-cockpit-task-outcome",
        "schemaVersion": 1,
        "workItemId": "example",
        "status": "completed",
        "bindings": {
            "taskId": "example",
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
        "sections": {
            "outcomeSummary": "Completed.",
            "taskOverview": "Example.",
            "deliveredChanges": [],
            "findings": [],
            "risks": [],
            "warnings": [],
            "interventions": [],
            "forcedStops": [],
            "resolutions": [],
            "recurrencePrevention": [],
            "avoidedImpact": [],
            "residualRisks": [],
            "humanDecisions": [],
            "evidence": [{"source": "contract.json", "subject": "Contract"}],
        },
    }
    contract_path.with_name("example.outcome.json").write_text(
        json.dumps(outcome), encoding="utf-8"
    )
    receipts = tmp_path / "target/task-closure-receipts"
    monkeypatch.setattr(closure, "CLOSURE_RECEIPTS_DIR", receipts)
    facts = {
        "pullRequest": "https://example.test/pr/1",
        "mergeCommit": "f" * 40,
        "base": "origin/main",
        "baseCommit": "1" * 40,
        "workBranch": "codex/example",
        "cleanup": "scheduled",
        "continueFrom": str(tmp_path),
    }

    json_path, markdown_path = closure.generate_final_human_report("example", contract_path, facts)

    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["phase"] == "final"
    assert report["closure"] == facts
    assert "Continue from" in markdown_path.read_text(encoding="utf-8")


def test_closure_receipt_persists_machine_readable_closure_facts(tmp_path: Path, monkeypatch):
    contract_path = tmp_path / ".ai/work-items/archive/2026/example.contract.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text("{}", encoding="utf-8")
    contract_path.with_name("example.outcome.json").write_text(
        json.dumps({"workItemId": "example"}), encoding="utf-8"
    )
    monkeypatch.setattr(closure, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(closure, "CLOSURE_RECEIPTS_DIR", tmp_path / "receipts")
    monkeypatch.setattr(
        closure, "generate_final_human_report", lambda *_: (tmp_path / "r.json", tmp_path / "r.md")
    )
    pr = {
        "url": "https://example.test/pr/1",
        "number": 1,
        "state": "MERGED",
        "headRefOid": "a" * 40,
        "mergeCommit": {"oid": "b" * 40},
    }
    closure.generate_closure_receipt(
        "example",
        contract_path,
        pr,
        work_branch="codex/example",
        base_remote="origin",
        base_branch="main",
        base_commit="c" * 40,
        base_worktree=None,
    )
    receipt = json.loads((tmp_path / "receipts/example.closure.json").read_text(encoding="utf-8"))
    assert receipt["workItemId"] == "example"
    assert receipt["pullRequest"]["state"] == "merged"
    assert receipt["providerEvidence"] == []


def test_explicit_worktree_scopes_git_but_leaves_provider_cli_unprefixed() -> None:
    commands: list[tuple[str, ...]] = []

    def runner(args, _check):
        commands.append(tuple(args))
        return closure.CommandResult(0, "")

    scoped = closure._in_worktree(runner, "/tmp/child-worktree")

    scoped(["status", "--porcelain"], False)
    scoped(["gh", "pr", "view", "474"], False)

    assert commands == [
        ("-C", "/tmp/child-worktree", "status", "--porcelain"),
        ("gh", "pr", "view", "474"),
    ]


def test_verify_pr_explicitly_selects_the_requested_work_item_branch() -> None:
    commands: list[tuple[str, ...]] = []
    payload = {
        "state": "MERGED",
        "headRefName": "codex/child",
        "headRefOid": "child-head",
        "baseRefName": "codex/parent",
        "mergedAt": "2026-07-30T00:00:00Z",
        "mergeCommit": {"oid": "merge-child"},
        "url": "https://example.test/pr/474",
    }

    def runner(args, _check):
        commands.append(tuple(args))
        return closure.CommandResult(0, __import__("json").dumps(payload))

    assert (
        closure._verify_pr(runner, "codex/child", "main", "child-head", allow_stacked_base=True)
        == payload
    )
    assert commands == [
        (
            "gh",
            "pr",
            "view",
            "codex/child",
            "--json",
            "state,headRefName,headRefOid,baseRefName,mergedAt,mergeCommit,url",
        )
    ]


def test_registered_target_worktree_rejects_missing_path(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="does not exist"):
        closure._registered_target_worktree(str(tmp_path / "missing"))


def test_registered_target_worktree_accepts_same_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "child"
    target.mkdir()
    source_root = tmp_path / "policy"
    source_root.mkdir()
    calls: list[tuple[str, ...]] = []

    def runner(args, _check):
        calls.append(tuple(args))
        if args == ["rev-parse", "--show-toplevel"]:
            return closure.CommandResult(0, f"{target}\n")
        if args == ["worktree", "list", "--porcelain"]:
            return closure.CommandResult(0, f"worktree {source_root}\n")
        raise AssertionError(args)

    monkeypatch.setattr(closure, "PROJECT_ROOT", source_root)
    monkeypatch.setattr(closure, "_in_worktree", lambda _runner, _path: runner)

    assert closure._registered_target_worktree(str(target)) is runner
    assert calls == [
        ("rev-parse", "--show-toplevel"),
        ("worktree", "list", "--porcelain"),
    ]


def test_close_branch_discovery_uses_remote_identity_for_duplicate_branch_names() -> None:
    with pytest.raises(RuntimeError, match="could not uniquely discover"):
        closure._discover_base(
            lambda args, _check: closure.CommandResult(
                0,
                "origin\nupstream\n" if args == ["remote"] else f"{args[-1].split('/')[2]}/main\n",
            )
        )


class FakeGit:
    def __init__(
        self,
        *,
        fail_on: tuple[str, ...] | None = None,
        remote_branch_exists: bool = False,
        remote_check_returncode: int | None = None,
    ) -> None:
        self.commands: list[tuple[str, ...]] = []
        self.fail_on = fail_on
        self.remote_branch_exists = remote_branch_exists
        self.remote_check_returncode = remote_check_returncode
        self.current_branch = "codex/example"
        self.base_worktree_path = ""
        self.base_branch = "main"
        self.work_branch_commit = "work123"

    def __call__(self, args: list[str] | tuple[str, ...], check: bool) -> closure.CommandResult:
        command = tuple(args)
        self.commands.append(command)
        normalized = command[2:] if command[:1] == ("-C",) else command
        if self.fail_on and normalized[: len(self.fail_on)] == self.fail_on:
            if check:
                raise RuntimeError(f"forced failure: {' '.join(normalized)}")
            return closure.CommandResult(1, "", "forced failure")
        if normalized == ("branch", "--show-current"):
            branch = self.base_branch if command[:1] == ("-C",) else self.current_branch
            return closure.CommandResult(0, f"{branch}\n")
        if normalized == ("switch", self.base_branch):
            self.current_branch = self.base_branch
            return closure.CommandResult(0, "")
        if normalized == ("switch", "--detach", "HEAD"):
            self.current_branch = ""
            return closure.CommandResult(0, "")
        if normalized == ("switch", "codex/example"):
            self.current_branch = "codex/example"
            return closure.CommandResult(0, "")
        if normalized == ("worktree", "list", "--porcelain"):
            if self.base_worktree_path:
                return closure.CommandResult(
                    0,
                    f"worktree /tmp/base-worktree\nHEAD abc123\nbranch refs/heads/{self.base_branch}\n\n",
                )
            return closure.CommandResult(0, "")
        if normalized == ("status", "--porcelain", "--untracked-files=all"):
            return closure.CommandResult(0, "")
        if normalized == ("rev-parse", "codex/example"):
            return closure.CommandResult(0, f"{self.work_branch_commit}\n")
        if normalized[:2] in {
            ("rev-parse", self.base_branch),
            ("rev-parse", f"origin/{self.base_branch}"),
        }:
            return closure.CommandResult(0, "abc123\n")
        if normalized[:3] == ("ls-remote", "--exit-code", "--heads"):
            if self.remote_check_returncode is not None:
                return closure.CommandResult(
                    self.remote_check_returncode, "", "remote check failed"
                )
            return closure.CommandResult(0 if self.remote_branch_exists else 2, "", "")
        return closure.CommandResult(0, "")


def prepare(monkeypatch: pytest.MonkeyPatch, fake: FakeGit) -> None:
    monkeypatch.setattr(
        closure,
        "_verify_archived_evidence",
        lambda _task: closure.PROJECT_ROOT / ".ai/work-items/archive/2026/example.contract.json",
    )
    monkeypatch.setattr(closure, "_discover_base", lambda _runner: ("origin", "main"))
    monkeypatch.setattr(
        closure,
        "_verify_pr",
        lambda _runner, _branch, _base, _branch_commit, **_kwargs: {
            "url": "https://example.test/pr/1",
            "headRefOid": "work123",
            "baseRefName": "main",
            "mergeCommit": {"oid": "merge123"},
        },
    )
    monkeypatch.setattr(
        closure,
        "generate_closure_receipt",
        lambda *_args, **_kwargs: closure.PROJECT_ROOT / "target/example.closure.md",
    )
    monkeypatch.setattr(closure, "validate_closure_receipt", lambda *_args, **_kwargs: None)


def test_task_branch_mismatch_stops_before_provider_or_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit()
    provider_calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        closure,
        "_verify_archived_evidence",
        lambda _task: closure.PROJECT_ROOT / ".ai/work-items/archive/2026/example.contract.json",
    )
    monkeypatch.setattr(closure, "_discover_base", lambda _runner: ("origin", "main"))
    monkeypatch.setattr(
        closure,
        "_verify_pr",
        lambda *_args, **_kwargs: provider_calls.append(("gh", "pr", "view")),
    )

    with pytest.raises(RuntimeError, match="requested Work Item does not match"):
        closure.close_work_item("different-task", fake)

    assert provider_calls == []
    assert not any(command[:2] == ("push", "origin") for command in fake.commands)
    assert not any(command[:2] == ("branch", "-D") for command in fake.commands)


def test_recorded_start_branch_is_limited_to_codex_namespace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(closure, "PROJECT_ROOT", tmp_path)
    receipt = tmp_path / ".ai/work-items/starts/example.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text('{"baseBranch":"codex/legacy-example"}', encoding="utf-8")

    assert closure._recorded_start_branch("example") == "codex/legacy-example"

    receipt.write_text('{"baseBranch":"main"}', encoding="utf-8")
    assert closure._recorded_start_branch("example") is None


def test_success_proves_remote_absence_before_local_branch_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit()
    prepare(monkeypatch, fake)

    result = closure.close_work_item("example", fake)

    assert result["state"] == "closed"
    assert result["repositoryState"] == "ready_on_base"
    assert result["nextWorkItemReady"] is True
    assert result["baseWorktree"] == ""
    remote_delete = fake.commands.index(("push", "origin", "--delete", "codex/example"))
    remote_absence = fake.commands.index(
        ("ls-remote", "--exit-code", "--heads", "origin", "codex/example")
    )
    local_delete = fake.commands.index(("branch", "-D", "codex/example"))

    assert remote_delete < remote_absence < local_delete


def test_success_emits_closure_receipt_before_remote_branch_deletion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake = FakeGit()
    prepare(monkeypatch, fake)
    receipt_path = tmp_path / "example.closure.md"
    monkeypatch.setattr(
        closure,
        "generate_closure_receipt",
        lambda *_args, **_kwargs: receipt_path,
    )

    result = closure.close_work_item("example", fake)

    assert result["closureReceipt"] == str(receipt_path)
    remote_delete = fake.commands.index(("push", "origin", "--delete", "codex/example"))
    assert remote_delete > 0


def test_closure_receipt_failure_blocks_all_branch_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit()
    prepare(monkeypatch, fake)
    monkeypatch.setattr(
        closure,
        "generate_closure_receipt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("Closure Receipt invalid")),
    )

    with pytest.raises(RuntimeError, match="Closure Receipt invalid"):
        closure.close_work_item("example", fake)

    assert not any(command[:3] == ("push", "origin", "--delete") for command in fake.commands)
    assert not any(command[:2] == ("branch", "-D") for command in fake.commands)


def test_closure_receipt_validation_rejects_missing_required_facts(tmp_path: Path) -> None:
    receipt = tmp_path / "example.closure.md"
    receipt.write_text("# Work Item Closure Receipt: example\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Closure Receipt is invalid"):
        closure.validate_closure_receipt(receipt, "example")


def test_unmerged_pr_blocks_all_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGit()
    prepare(monkeypatch, fake)
    monkeypatch.setattr(
        closure,
        "_verify_pr",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("pull request is not merged")),
    )

    with pytest.raises(RuntimeError, match="not merged"):
        closure.close_work_item("example", fake)

    assert ("switch", "main") not in fake.commands
    assert not any(command[:2] == ("branch", "-D") for command in fake.commands)
    assert not any(command[:3] == ("push", "origin", "--delete") for command in fake.commands)


def test_base_branch_error_explains_that_closure_must_identify_work_item_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit()
    fake.current_branch = "main"
    prepare(monkeypatch, fake)

    with pytest.raises(RuntimeError, match="still-identifiable Work Item branch"):
        closure.close_work_item("example", fake)

    assert fake.commands == [("branch", "--show-current")]


def test_base_branch_worktree_occupancy_is_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit()
    fake.base_worktree_path = "/tmp/base-worktree"
    prepare(monkeypatch, fake)

    result = closure.close_work_item("example", fake)

    assert ("worktree", "list", "--porcelain") in fake.commands
    assert result["state"] == "closed"
    assert result["repositoryState"] == "closed_but_current_worktree_detached"
    assert result["nextWorkItemReady"] is False
    assert result["baseWorktree"] == "/tmp/base-worktree"
    assert fake.current_branch == ""
    assert ("-C", "/tmp/base-worktree", "merge", "--ff-only", "origin/main") in fake.commands


def test_incomplete_archived_evidence_blocks_before_branch_inspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit()
    monkeypatch.setattr(
        closure,
        "_verify_archived_evidence",
        lambda _task: (_ for _ in ()).throw(RuntimeError("archived Work Item evidence is invalid")),
    )

    with pytest.raises(RuntimeError, match="evidence is invalid"):
        closure.close_work_item("example", fake)

    assert fake.commands == []


def test_branch_mapping_mismatch_blocks_before_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGit()
    prepare(monkeypatch, fake)
    monkeypatch.setattr(
        closure,
        "_verify_pr",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("head branch does not match")),
    )

    with pytest.raises(RuntimeError, match="head branch"):
        closure.close_work_item("example", fake)

    assert ("switch", "main") not in fake.commands


def test_dirty_worktree_blocks_before_pr_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGit()
    prepare(monkeypatch, fake)
    monkeypatch.setattr(
        closure,
        "_require_clean_worktree",
        lambda _runner: (_ for _ in ()).throw(RuntimeError("worktree or index is not clean")),
    )

    with pytest.raises(RuntimeError, match="not clean"):
        closure.close_work_item("example", fake)

    assert ("switch", "main") not in fake.commands


def test_non_fast_forward_blocks_before_branch_deletion(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGit(fail_on=("merge", "--ff-only"))
    prepare(monkeypatch, fake)

    with pytest.raises(RuntimeError, match="forced failure"):
        closure.close_work_item("example", fake)

    assert not any(command[:2] == ("branch", "-D") for command in fake.commands)
    assert not any(command[:3] == ("push", "origin", "--delete") for command in fake.commands)


def test_remote_deletion_failure_does_not_report_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGit(
        fail_on=("push", "origin", "--delete"),
        remote_branch_exists=True,
    )
    prepare(monkeypatch, fake)

    with pytest.raises(RuntimeError, match="remote work branch still exists"):
        closure.close_work_item("example", fake)

    assert ("branch", "-D", "codex/example") not in fake.commands
    assert ("switch", "--detach", "HEAD") not in fake.commands
    assert fake.current_branch == "codex/example"


def test_linked_worktree_local_delete_failure_restores_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit(fail_on=("branch", "-D"))
    fake.base_worktree_path = "/tmp/base-worktree"
    prepare(monkeypatch, fake)

    with pytest.raises(RuntimeError, match="restored for retry"):
        closure.close_work_item("example", fake)

    detach = fake.commands.index(("switch", "--detach", "HEAD"))
    restore = fake.commands.index(("switch", "codex/example"))
    assert detach < restore
    assert fake.current_branch == "codex/example"


def test_remote_deletion_race_is_accepted_when_postcondition_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit(fail_on=("push", "origin", "--delete"))
    prepare(monkeypatch, fake)

    result = closure.close_work_item("example", fake)

    assert result["state"] == "closed"
    assert ("fetch", "origin", "--prune") in fake.commands
    remote_absence = fake.commands.index(
        ("ls-remote", "--exit-code", "--heads", "origin", "codex/example")
    )
    local_delete = fake.commands.index(("branch", "-D", "codex/example"))
    assert remote_absence < local_delete


def test_remote_deletion_failure_with_unverifiable_state_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit(
        fail_on=("push", "origin", "--delete"),
        remote_check_returncode=1,
    )
    prepare(monkeypatch, fake)

    with pytest.raises(RuntimeError, match="could not verify remote work branch deletion"):
        closure.close_work_item("example", fake)


def test_find_archived_contract_requires_exactly_one_match(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    (archive / "2026").mkdir(parents=True)
    monkeypatch.setattr(closure, "ARCHIVE_DIR", archive)

    with pytest.raises(RuntimeError, match="exactly one"):
        closure._find_archived_contract("example")

    (archive / "2026" / "example.contract.json").write_text("{}", encoding="utf-8")
    assert closure._find_archived_contract("example").name == "example.contract.json"

    (archive / "2025").mkdir()
    (archive / "2025" / "example.contract.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="exactly one"):
        closure._find_archived_contract("example")


def test_verify_pr_rejects_malformed_adapter_responses():
    with pytest.raises(RuntimeError, match="cannot verify"):
        closure._verify_pr(
            lambda _args, _check: closure.CommandResult(0, "not-json"),
            "branch",
            "main",
            "work123",
        )

    def wrong_shape(_args, _check):
        return closure.CommandResult(0, "[]")

    with pytest.raises(RuntimeError, match="non-object"):
        closure._verify_pr(wrong_shape, "branch", "main", "work123")


def test_verify_pr_requires_merged_identity_and_timestamp():
    cases = [
        ({"state": "OPEN"}, "not merged"),
        (
            {"state": "MERGED", "headRefName": "other"},
            "head branch",
        ),
        (
            {
                "state": "MERGED",
                "headRefName": "branch",
                "headRefOid": "work123",
                "baseRefName": "other",
            },
            "base branch",
        ),
        (
            {
                "state": "MERGED",
                "headRefName": "branch",
                "headRefOid": "work123",
                "baseRefName": "main",
            },
            "merge commit",
        ),
    ]
    for payload, message in cases:

        def runner(_args, _check, payload=payload):
            return closure.CommandResult(0, __import__("json").dumps(payload))

        with pytest.raises(RuntimeError, match=message):
            closure._verify_pr(runner, "branch", "main", "work123")


def test_verify_pr_requires_exact_local_head_sha() -> None:
    payload = {
        "state": "MERGED",
        "headRefName": "codex/example",
        "headRefOid": "other123",
        "baseRefName": "main",
        "mergedAt": "2026-07-28T00:00:00Z",
        "mergeCommit": {"oid": "merge123"},
        "url": "https://example.test/pr/1",
    }

    def runner(_args, _check):
        return closure.CommandResult(0, __import__("json").dumps(payload))

    with pytest.raises(RuntimeError, match="Head SHA"):
        closure._verify_pr(runner, "codex/example", "main", "work123")


def test_verify_stacked_base_requires_archived_parent_identity_remote_and_ancestry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive" / "2026"
    archive.mkdir(parents=True)
    (archive / "parent.contract.json").write_text('{"workItemId": "parent"}\n', encoding="utf-8")
    monkeypatch.setattr(closure, "ARCHIVE_DIR", tmp_path / "archive")
    monkeypatch.setattr(closure, "CLOSURE_RECEIPTS_DIR", tmp_path / "receipts")

    def runner(args, _check):
        if tuple(args[:3]) == ("ls-remote", "--exit-code", "--heads"):
            return closure.CommandResult(0, "parent-sha\trefs/heads/codex/parent\n")
        if tuple(args) == ("fetch", "origin", "codex/parent"):
            return closure.CommandResult(0, "")
        if tuple(args) == (
            "merge-base",
            "--is-ancestor",
            "merge123",
            "origin/codex/parent",
        ):
            return closure.CommandResult(0, "")
        raise AssertionError(args)

    closure._verify_stacked_base(
        runner,
        remote="origin",
        default_branch="main",
        stacked_base="codex/parent",
        merge_commit="merge123",
    )


@pytest.mark.parametrize(
    ("stacked_base", "merge_returncode", "message"),
    [
        ("release", 0, "not a Work Item branch"),
        ("codex/parent", 1, "not retained"),
    ],
)
def test_verify_stacked_base_rejects_untrusted_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stacked_base: str,
    merge_returncode: int,
    message: str,
) -> None:
    archive = tmp_path / "archive" / "2026"
    archive.mkdir(parents=True)
    (archive / "parent.contract.json").write_text('{"workItemId": "parent"}\n', encoding="utf-8")
    monkeypatch.setattr(closure, "ARCHIVE_DIR", tmp_path / "archive")
    monkeypatch.setattr(closure, "CLOSURE_RECEIPTS_DIR", tmp_path / "receipts")

    def runner(args, _check):
        if tuple(args[:3]) == ("ls-remote", "--exit-code", "--heads"):
            return closure.CommandResult(0, "parent-sha\trefs/heads/codex/parent\n")
        if tuple(args) == ("fetch", "origin", "codex/parent"):
            return closure.CommandResult(0, "")
        if tuple(args[:2]) == ("merge-base", "--is-ancestor"):
            return closure.CommandResult(merge_returncode, "", "not ancestor")
        raise AssertionError(args)

    with pytest.raises(RuntimeError, match=message):
        closure._verify_stacked_base(
            runner,
            remote="origin",
            default_branch="main",
            stacked_base=stacked_base,
            merge_commit="merge123",
        )


def test_verify_stacked_base_rejects_a_parent_that_is_already_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive" / "2026"
    archive.mkdir(parents=True)
    (archive / "parent.contract.json").write_text('{"workItemId": "parent"}\n', encoding="utf-8")
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    (receipts / "parent.closure.md").write_text("closed\n", encoding="utf-8")
    monkeypatch.setattr(closure, "ARCHIVE_DIR", tmp_path / "archive")
    monkeypatch.setattr(closure, "CLOSURE_RECEIPTS_DIR", receipts)

    with pytest.raises(RuntimeError, match="already closed"):
        closure._verify_stacked_base(
            lambda _args, _check: pytest.fail("remote checks must not run for a closed parent"),
            remote="origin",
            default_branch="main",
            stacked_base="codex/parent",
            merge_commit="merge123",
        )


def test_stacked_closure_synchronizes_the_verified_parent_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit()
    fake.base_branch = "codex/parent"
    prepare(monkeypatch, fake)
    monkeypatch.setattr(
        closure,
        "_verify_pr",
        lambda *_args, **_kwargs: {
            "url": "https://example.test/pr/2",
            "headRefOid": "work123",
            "baseRefName": "codex/parent",
            "mergeCommit": {"oid": "merge123"},
        },
    )
    monkeypatch.setattr(closure, "_verify_stacked_base", lambda *_args, **_kwargs: None)

    result = closure.close_work_item("example", fake)

    assert result["baseBranch"] == "codex/parent"
    assert ("switch", "codex/parent") in fake.commands
    assert ("merge", "--ff-only", "origin/codex/parent") in fake.commands


def test_external_runner_fails_closed_when_command_is_unavailable(monkeypatch):
    monkeypatch.setattr(closure.shutil, "which", lambda _name: None)

    with pytest.raises(RuntimeError, match="required command is unavailable"):
        closure._run_external(["missing-command"])


def test_clean_worktree_and_remote_postconditions_fail_closed():
    def dirty(_args, _check):
        return closure.CommandResult(0, " M file.py\n")

    with pytest.raises(RuntimeError, match="not clean"):
        closure._require_clean_worktree(dirty)

    def unverifiable(_args, _check):
        return closure.CommandResult(1, "", "remote unavailable")

    with pytest.raises(RuntimeError, match="could not verify"):
        closure._remote_branch_absent(unverifiable, "origin", "branch")


def test_remote_postcondition_rejects_stale_tracking_branch():
    def stale_tracking(args, _check):
        if args[:3] == ["ls-remote", "--exit-code", "--heads"]:
            return closure.CommandResult(2, "", "")
        if args[:3] == ["branch", "--remotes", "--list"]:
            return closure.CommandResult(0, "  origin/codex/example\n", "")
        return closure.CommandResult(0, "", "")

    with pytest.raises(RuntimeError, match="remote-tracking"):
        closure._remote_branch_absent(stale_tracking, "origin", "codex/example")


def test_local_postcondition_rejects_branch_residue():
    def stale_local(args, _check):
        if args[:2] == ["branch", "--list"]:
            return closure.CommandResult(0, "* codex/example\n", "")
        return closure.CommandResult(0, "", "")

    with pytest.raises(RuntimeError, match="local Work Item branch still exists"):
        closure._delete_local_branch(stale_local, "codex/example", detach_required=False)


def test_main_reports_ready_only_for_ready_on_base(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        closure,
        "parse_args",
        lambda: type("Args", (), {"task": "example"})(),
    )
    monkeypatch.setattr(
        closure,
        "close_work_item",
        lambda *_args: {
            "contract": ".ai/work-items/archive/2026/example.contract.json",
            "closureReceipt": "target/example.closure.md",
            "pullRequest": "https://example.test/pr/1",
            "workBranch": "codex/example",
            "baseRemote": "origin",
            "baseBranch": "main",
            "baseWorktree": "",
            "repositoryState": "ready_on_base",
            "nextWorkItemReady": True,
        },
    )

    assert closure.main() == 0
    output = capsys.readouterr().out
    assert "Closure Receipt: target/example.closure.md" in output
    assert "Repository state: ready for next Work Item" in output


def test_main_uses_registered_explicit_worktree(monkeypatch, capsys) -> None:
    target_runner = object()
    monkeypatch.setattr(
        closure,
        "parse_args",
        lambda: type("Args", (), {"task": "example", "worktree": "/tmp/child"})(),
    )
    monkeypatch.setattr(
        closure,
        "_registered_target_worktree",
        lambda path: target_runner if path == "/tmp/child" else None,
    )
    observed = {}

    def close(task, runner):
        observed.update({"task": task, "runner": runner})
        return {
            "state": "closed",
            "pullRequest": 474,
            "contract": ".ai/work-items/archive/2026/example.contract.json",
            "workBranch": "codex/example",
            "baseRemote": "origin",
            "baseBranch": "main",
            "baseWorktree": None,
            "receipt": ".ai/work-items/archive/example.closure.md",
            "closureReceipt": ".ai/work-items/archive/example.closure.md",
            "repositoryState": "ready_on_base",
            "nextWorkItemReady": True,
        }

    monkeypatch.setattr(closure, "close_work_item", close)

    assert closure.main() == 0
    assert observed == {"task": "example", "runner": target_runner}
    assert "Repository state: ready for next Work Item" in capsys.readouterr().out


def test_main_reports_detached_closure_as_not_ready(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        closure,
        "parse_args",
        lambda: type("Args", (), {"task": "example"})(),
    )
    monkeypatch.setattr(
        closure,
        "close_work_item",
        lambda *_args: {
            "contract": ".ai/work-items/archive/2026/example.contract.json",
            "closureReceipt": "target/example.closure.md",
            "pullRequest": "https://example.test/pr/1",
            "workBranch": "codex/example",
            "baseRemote": "origin",
            "baseBranch": "main",
            "baseWorktree": "/tmp/base-worktree",
            "repositoryState": "closed_but_current_worktree_detached",
            "nextWorkItemReady": False,
        },
    )

    assert closure.main() == 0
    output = capsys.readouterr().out
    assert "Current worktree: detached; not ready for the next Work Item" in output
    assert "Continue from synchronized base worktree: /tmp/base-worktree" in output
    assert "Repository state: ready for next Work Item" not in output


def test_real_linked_worktree_closure_is_closed_but_not_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    remote = tmp_path / "remote.git"
    repository = tmp_path / "repository"
    base_worktree = tmp_path / "base-worktree"

    run_command(tmp_path, "git", "init", "--bare", str(remote))
    run_command(tmp_path, "git", "clone", str(remote), str(repository))
    run_command(repository, "git", "config", "user.name", "Test User")
    run_command(repository, "git", "config", "user.email", "test@example.test")
    run_command(repository, "git", "switch", "-c", "main")
    (repository / "tracked.txt").write_text("base\n", encoding="utf-8")
    run_command(repository, "git", "add", "tracked.txt")
    run_command(repository, "git", "commit", "-m", "base")
    run_command(repository, "git", "push", "-u", "origin", "main")
    run_command(remote, "git", "symbolic-ref", "HEAD", "refs/heads/main")
    run_command(repository, "git", "remote", "set-head", "origin", "-a")

    run_command(repository, "git", "switch", "-c", "codex/example")
    (repository / "tracked.txt").write_text("work\n", encoding="utf-8")
    run_command(repository, "git", "commit", "-am", "work")
    work_commit = run_command(repository, "git", "rev-parse", "HEAD").stdout.strip()
    run_command(repository, "git", "push", "-u", "origin", "codex/example")
    run_command(repository, "git", "worktree", "add", str(base_worktree), "main")
    run_command(base_worktree, "git", "merge", "--no-ff", "codex/example", "-m", "merge")
    run_command(base_worktree, "git", "push", "origin", "main")

    monkeypatch.setattr(
        closure,
        "_verify_archived_evidence",
        lambda _task: closure.PROJECT_ROOT / ".ai/work-items/archive/2026/example.contract.json",
    )
    monkeypatch.setattr(
        closure,
        "_verify_pr",
        lambda _runner, _branch, _base, _head, **_kwargs: {
            "url": "https://example.test/pr/1",
            "headRefOid": work_commit,
            "baseRefName": "main",
            "mergeCommit": {"oid": "merge123"},
        },
    )
    monkeypatch.setattr(
        closure,
        "generate_closure_receipt",
        lambda *_args, **_kwargs: repository / "target/example.closure.md",
    )
    monkeypatch.setattr(closure, "validate_closure_receipt", lambda *_args, **_kwargs: None)

    result = closure.close_work_item("example", repository_runner(repository))

    assert result["repositoryState"] == "closed_but_current_worktree_detached"
    assert result["nextWorkItemReady"] is False
    assert run_command(repository, "git", "branch", "--show-current").stdout.strip() == ""
    assert run_command(base_worktree, "git", "branch", "--show-current").stdout.strip() == "main"
    assert (
        run_command(base_worktree, "git", "rev-parse", "main").stdout
        == run_command(base_worktree, "git", "rev-parse", "origin/main").stdout
    )
    assert run_command(repository, "git", "status", "--porcelain").stdout == ""
    local_branches = run_command(repository, "git", "branch", "--format=%(refname:short)").stdout
    assert "codex/example" not in local_branches.splitlines()
    remote_heads = run_command(
        repository,
        "git",
        "ls-remote",
        "--heads",
        "origin",
        "codex/example",
    ).stdout
    assert remote_heads == ""
