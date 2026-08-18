import hashlib
import json
import sys
from pathlib import Path

import ai_check_pr
import ai_post_archive_recovery as recovery
import pytest
from ai_start_receipt import build_receipt, receipt_binding, validate_receipt


def test_pr_requires_capability_matrix_when_bound_evidence_changes():
    issues = ai_check_pr.capability_truth_dependency_issues(["scripts/ai_finish.py"])

    assert issues == [
        (
            "Capability Truth evidence dependency requires a changed "
            "docs/reference/capability-truth-matrix.json: scripts/ai_finish.py is bound to "
            "capabilities [human_benefit_report, repository_governance_layer]"
        )
    ]


def test_pr_rejects_stale_capability_matrix(monkeypatch):
    monkeypatch.setattr(
        ai_check_pr,
        "validate_matrix",
        lambda *_args, **_kwargs: [
            "capabilities[3].evidenceSource does not match current evidence bytes"
        ],
    )

    assert ai_check_pr.capability_truth_dependency_issues(
        ["docs/reference/capability-truth-matrix.json"]
    ) == ["capabilities[3].evidenceSource does not match current evidence bytes"]


def write_pair(root, name, scope, changed, *, approved=False):
    archive = root / ".ai" / "work-items" / "archive" / "2026"
    archive.mkdir(parents=True, exist_ok=True)
    contract_path = archive / f"{name}.contract.json"
    summary_path = archive / f"{name}.summary.json"
    contract = {
        "contractVersion": 2,
        "workItemId": name,
        "mode": "code",
        "title": name,
        "baseCommit": "a" * 40,
        "baselineDirtyPaths": [],
        "scope": scope,
        "outOfScope": [],
        "sources": ["spec"],
        "unknowns": [],
        "notCodable": False,
        "acceptance": ["done"],
        "verification": [{"check": "projectTest", "required": False}],
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
        "restrictedWriteApproval": {
            "approved": approved,
            "approvedBy": "reviewer",
            "reason": "fixture",
        }
        if approved
        else {"approved": False},
        "rollbackNote": "revert",
    }
    summary = {
        "summaryVersion": 2,
        "workItemId": name,
        "contractPath": contract_path.relative_to(root).as_posix(),
        "changedFiles": [{"path": path, "reason": "covered"} for path in changed],
        "sourcesUsed": ["spec"],
        "verification": [{"check": "projectTest", "result": "not_run"}],
        "unknownsRemaining": [],
        "risk": {"level": "low", "detail": "none"},
        "generatedFiles": [],
        "destructiveChanges": [],
        "observedIssues": [],
    }
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    return contract_path


def patch_changes(monkeypatch, paths, *, statuses=None):
    statuses = statuses or {}
    monkeypatch.setattr(ai_check_pr, "changed_paths", lambda *args, **kwargs: paths)
    monkeypatch.setattr(
        ai_check_pr,
        "changed_name_status",
        lambda *args, **kwargs: [
            (statuses.get(path, "A" if path.startswith(".ai/work-items/archive/") else "M"), path)
            for path in paths
        ],
    )


def test_pr_bundle_accepts_only_a_receipt_declared_same_work_item_recovery_path(
    tmp_path, monkeypatch
):
    pair = write_pair(tmp_path, "recovered", [], [])
    contract_path = pair.relative_to(tmp_path).as_posix()
    summary_path = contract_path.replace(".contract", ".summary")
    receipt_path = ".ai/work-items/recovery-receipts/recovered.json"
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ai_check_pr,
        "same_work_item_recovery_paths",
        lambda _base, _entries: ({"recovered": {"scripts/ai_finish.py"}}, {receipt_path}, []),
    )
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(
        monkeypatch,
        [contract_path, summary_path, receipt_path, "scripts/ai_finish.py"],
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [pair])

    assert not any("scripts/ai_finish.py" in issue for issue in issues)


def test_pr_bundle_skips_summary_bound_generated_knowledge_before_restricted_validation(
    tmp_path, monkeypatch
):
    task = "generated-knowledge-recovery"
    knowledge_paths = [
        ".ai/knowledge/index.json",
        f".ai/knowledge/work-items/{task}.json",
    ]
    pair = write_pair(tmp_path, task, [".ai/knowledge/**"], knowledge_paths)
    contract_rel = pair.relative_to(tmp_path).as_posix()
    summary_rel = contract_rel.replace(".contract", ".summary")
    receipt_path = f".ai/work-items/recovery-receipts/{task}.json"
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ai_check_pr,
        "same_work_item_recovery_paths",
        lambda _base, _entries: ({task: set(knowledge_paths)}, {receipt_path}, []),
    )
    scope = tmp_path / "scope.yaml"
    scope.write_text("allowAlways:\n", encoding="utf-8")
    ownership = tmp_path / "ownership.yaml"
    ownership.write_text(".ai/**:\n  aiWrite: restricted\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", scope)
    monkeypatch.setattr(ai_check_pr, "OWNERSHIP_POLICY", ownership)
    patch_changes(monkeypatch, [contract_rel, summary_rel, receipt_path, *knowledge_paths])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [pair])

    assert not any("restricted path lacks approval" in issue for issue in issues)
    assert not any(path in issue for path in knowledge_paths for issue in issues)


def test_recovery_only_pr_discovers_archived_owner_from_valid_receipt(tmp_path, monkeypatch):
    contract_path = write_pair(tmp_path, "recovered-only", [], [])
    archive = contract_path.parent
    outcome_path = archive / "recovered-only.outcome.json"
    manifest_path = archive / "recovered-only.archive-manifest.json"
    outcome_path.write_text(json.dumps({"workItemId": "recovered-only"}), encoding="utf-8")
    manifest_path.write_text(json.dumps({"workItemId": "recovered-only"}), encoding="utf-8")
    receipt_dir = tmp_path / ".ai" / "work-items" / "recovery-receipts"
    receipt_dir.mkdir(parents=True)
    receipt = {
        "receiptVersion": 1,
        "kind": "same_work_item_post_archive_recovery",
        "workItemId": "recovered-only",
        "prBaseCommit": "b" * 40,
        "issue": "https://github.com/spirex-ds-dev/ai-cockpit-template/issues/901",
        "humanAuthorization": {"type": "human", "reference": "user-request"},
        "failure": {"gate": "changedCriticalCoverage"},
        "archive": {},
        "recoveryPaths": [".ai/knowledge/index.json"],
    }
    for suffix, path in {
        "contract": contract_path,
        "summary": archive / "recovered-only.summary.json",
        "outcome": outcome_path,
        "archive-manifest": manifest_path,
    }.items():
        receipt["archive"][suffix] = {
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    (receipt_dir / "recovered-only.json").write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    assert ai_check_pr.recovery_only_contract_paths("b" * 40) == [contract_path]


def test_same_work_item_recovery_ignores_receipts_for_another_pr_base(tmp_path, monkeypatch):
    task = "base-bound-recovery"
    archive = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive.mkdir(parents=True)
    receipt_dir = tmp_path / ".ai" / "work-items" / "recovery-receipts"
    receipt_dir.mkdir(parents=True)
    (receipt_dir / f"{task}.json").write_text(
        json.dumps({"workItemId": task, "prBaseCommit": "a" * 40}), encoding="utf-8"
    )
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    entries = [(archive / f"{task}.contract.json", {"workItemId": task}, {}, (74, task, task))]

    permitted, receipts, blockers = ai_check_pr.same_work_item_recovery_paths("b" * 40, entries)

    assert permitted == {}
    assert receipts == set()
    assert blockers == []


def test_pr_bundle_accepts_restricted_path_only_when_same_item_recovery_receipt_binds_it(
    tmp_path, monkeypatch
):
    pair = write_pair(tmp_path, "recovered", [], [])
    contract_path = pair.relative_to(tmp_path).as_posix()
    summary_path = contract_path.replace(".contract", ".summary")
    receipt_path = ".ai/work-items/recovery-receipts/recovered.json"
    recovery_path = ".github/workflows/compatibility.yml"
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ai_check_pr,
        "same_work_item_recovery_paths",
        lambda _base, _entries: ({"recovered": {recovery_path}}, {receipt_path}, []),
    )
    scope = tmp_path / "scope.yaml"
    scope.write_text("allowAlways:\n", encoding="utf-8")
    ownership = tmp_path / "ownership.yaml"
    ownership.write_text(f"{recovery_path}:\n  aiWrite: restricted\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", scope)
    monkeypatch.setattr(ai_check_pr, "OWNERSHIP_POLICY", ownership)
    patch_changes(monkeypatch, [contract_path, summary_path, receipt_path, recovery_path])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [pair])

    assert not any("restricted path lacks approval" in issue for issue in issues)


def test_same_work_item_hosted_recovery_validates_recorded_provider_binding_offline(
    tmp_path, monkeypatch
):
    archive = tmp_path / ".ai/work-items/archive/2026"
    archive.mkdir(parents=True)
    task = "hosted-recovered"
    for suffix, value in {
        "contract": {"workItemId": task},
        "summary": {"workItemId": task},
        "outcome": {"workItemId": task, "status": "completed"},
        "archive-manifest": {"workItemId": task},
    }.items():
        (archive / f"{task}.{suffix}.json").write_text(json.dumps(value), encoding="utf-8")

    def provider(endpoint):
        values = {
            "/repos/spirex-ds-dev/ai-cockpit-template/actions/runs/42": {
                "id": 42,
                "event": "pull_request",
                "head_sha": "b" * 40,
                "status": "completed",
                "conclusion": "failure",
                "path": ".github/workflows/smoke.yml",
                "html_url": "https://github.com/spirex-ds-dev/ai-cockpit-template/actions/runs/42",
                "pull_requests": [{"number": 716}],
                "run_attempt": 1,
            },
            "/repos/spirex-ds-dev/ai-cockpit-template/actions/jobs/84": {
                "id": 84,
                "run_id": 42,
                "name": "template-smoke",
                "status": "completed",
                "conclusion": "failure",
            },
        }
        if endpoint.endswith("/logs"):
            return b"Required test coverage of 85.1% not reached. Total coverage: 85.09%"
        return json.dumps(values[endpoint]).encode()

    receipt = recovery.open_hosted_post_archive_recovery(
        root=tmp_path,
        task=task,
        base_commit="a" * 40,
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/709",
        authority="standing authority",
        recovery_paths=["tests/test_resume.py"],
        repository="spirex-ds-dev/ai-cockpit-template",
        pull_request=716,
        failed_candidate_head="b" * 40,
        run_id=42,
        job_id=84,
        fetch_provider=provider,
        worktree_clean=lambda: True,
    )
    assert receipt["provider"]["runAttempt"] == 1
    contract_path = archive / f"{task}.contract.json"
    entries = [(contract_path, {"workItemId": task}, {}, (74, task, task))]
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    def provider_must_not_be_called(_endpoint):
        pytest.fail("the PR audit must not re-query provider evidence recorded in the receipt")

    monkeypatch.setattr(recovery, "_github_api", provider_must_not_be_called)

    result = ai_check_pr.same_work_item_recovery_paths("a" * 40, entries)
    assert len(result) == 3
    permitted, receipts, blockers = result

    assert permitted == {task: {"tests/test_resume.py"}}
    assert receipts == {".ai/work-items/recovery-receipts/hosted-recovered.json"}
    assert blockers == []

    receipt["provider"]["runUrl"] = "https://github.com/other/repository/actions/runs/42"
    receipt_path = tmp_path / ".ai/work-items/recovery-receipts/hosted-recovered.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    permitted, receipts, blockers = ai_check_pr.same_work_item_recovery_paths("a" * 40, entries)

    assert permitted == {}
    assert receipts == set()
    assert blockers == [
        (
            "BLOCKED: provider-bound recovery receipt cannot be verified: "
            "recorded provider run URL does not match its repository and run ID. Recovery: "
            "regenerate the recovery receipt from the failed hosted job."
        )
    ]


def test_pr_boundary_rejects_dirty_worktree(monkeypatch):
    monkeypatch.setattr(ai_check_pr, "run_git", lambda _args: fake_git_result(" M release.json\n"))

    assert ai_check_pr.validate_pr_boundary() == [
        "PR boundary requires a clean committed worktree; commit generated release evidence before creating the PR"
    ]


def test_pr_boundary_accepts_clean_worktree(monkeypatch):
    monkeypatch.setattr(ai_check_pr, "run_git", lambda _args: fake_git_result())

    assert ai_check_pr.validate_pr_boundary() == []


def fake_git_result(stdout="", returncode=0, stderr=""):
    return type(
        "Result",
        (),
        {"returncode": returncode, "stdout": stdout, "stderr": stderr},
    )()


def test_pr_receipt_binding_is_fail_closed():
    contract = {
        "contractVersion": 2,
        "workItemId": "pr_receipt",
        "mode": "code",
        "title": "PR receipt",
        "baseCommit": "a" * 40,
        "scope": ["scripts/**"],
    }
    receipt = build_receipt(contract, timestamp="2026-07-17T00:00:00+00:00")
    contract["startReceipt"] = receipt_binding(receipt)
    assert validate_receipt(contract, receipt) == []
    receipt["contractSkeletonDigest"] = "0" * 64
    assert "Contract startReceipt binding does not match Receipt" in validate_receipt(
        contract, receipt
    )


def test_aggregate_pr_covers_earlier_and_later_work_items(tmp_path, monkeypatch):
    first = write_pair(tmp_path, "first", ["src/first.py"], ["src/first.py"])
    second = write_pair(tmp_path, "second", ["src/second.py"], ["src/second.py"])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(
        monkeypatch,
        [
            "src/first.py",
            "src/second.py",
            first.relative_to(tmp_path).as_posix(),
            str(first.relative_to(tmp_path)).replace(".contract", ".summary"),
            second.relative_to(tmp_path).as_posix(),
            str(second.relative_to(tmp_path)).replace(".contract", ".summary"),
        ],
    )

    assert ai_check_pr.validate_pr_bundle("a" * 40, [first, second]) == []


@pytest.mark.parametrize(
    ("summary_issues", "superseded", "expected_issue"),
    [
        (
            ["required verification is not passed: quality"],
            True,
            None,
        ),
        (
            ["required verification is not passed: quality"],
            False,
            "required verification is not passed: quality",
        ),
        (
            [
                "required verification is not passed: quality",
                "summary contractHash does not match Contract",
            ],
            False,
            "summary contractHash does not match Contract",
        ),
    ],
)
def test_aggregate_pr_applies_only_bound_superseded_summary_exception(
    tmp_path, monkeypatch, summary_issues, superseded, expected_issue
):
    pair = write_pair(tmp_path, "superseded", [], [])
    contract_rel = pair.relative_to(tmp_path).as_posix()
    summary_rel = contract_rel.replace(".contract", ".summary")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    monkeypatch.setattr(ai_check_pr, "validate_contract", lambda _contract: [])
    monkeypatch.setattr(ai_check_pr, "validate_summary", lambda *_args, **_kwargs: summary_issues)
    monkeypatch.setattr(
        ai_check_pr,
        "superseded_summary_validation_exception",
        lambda **_kwargs: superseded,
        raising=False,
    )
    patch_changes(monkeypatch, [contract_rel, summary_rel])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [pair])

    if expected_issue is None:
        assert not any("required verification is not passed" in issue for issue in issues)
    else:
        assert any(expected_issue in issue for issue in issues)


def test_pr_rejects_multiple_newly_maintained_work_items(tmp_path, monkeypatch):
    first = write_pair(tmp_path, "first", ["src/first.py"], ["src/first.py"])
    second = write_pair(tmp_path, "second", ["src/second.py"], ["src/second.py"])
    for path, sequence in ((first, 75), (second, 76)):
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["archiveSequence"] = sequence
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(monkeypatch, ["src/first.py", "src/second.py"])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [first, second])

    assert any("exactly one newly maintained Work Item" in issue for issue in issues)


def test_historical_recovery_receipt_accepts_only_the_exact_consecutive_prefix(
    tmp_path, monkeypatch
):
    first = write_pair(tmp_path, "first", ["src/a.py"], ["src/a.py"])
    second = write_pair(tmp_path, "second", ["src/b.py"], ["src/b.py"])
    third = write_pair(tmp_path, "third", ["src/c.py"], ["src/c.py"])
    paths = (first, second, third)
    for path, sequence, base in zip(paths, (74, 75, 76), ("a" * 40, "b" * 40, "c" * 40)):
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["archiveSequence"] = sequence
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
        contract = json.loads(path.read_text(encoding="utf-8"))
        contract.update(
            {
                "baseCommit": base,
                "startReceipt": {"baseCommit": base, "path": f".ai/work-items/starts/{path.stem}"},
            }
        )
        path.write_text(json.dumps(contract), encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result(returncode=0))
    entries = []
    for path in paths:
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        entries.append(
            (
                path,
                json.loads(path.read_text()),
                json.loads(summary_path.read_text()),
                ai_check_pr.archive_pair_rank(path, summary_path),
            )
        )
    receipt = {
        "receiptVersion": 1,
        "prBaseCommit": "a" * 40,
        "humanAuthorization": {"type": "human", "reference": "conversation"},
        "archives": [ai_check_pr.recovery_receipt_entry(entry) for entry in entries[:2]],
    }

    assert ai_check_pr.historical_recovery_receipt_paths(entries, "a" * 40, receipt) == {second}
    receipt["archives"][1]["archiveSequence"] = 76
    assert ai_check_pr.historical_recovery_receipt_paths(entries, "a" * 40, receipt) == set()


def test_historical_recovery_receipt_requires_human_authorization(tmp_path, monkeypatch):
    first = write_pair(tmp_path, "first", ["src/a.py"], ["src/a.py"])
    second = write_pair(tmp_path, "second", ["src/b.py"], ["src/b.py"])
    entries = []
    for path, sequence in ((first, 74), (second, 75)):
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        summary = json.loads(summary_path.read_text())
        summary["archiveSequence"] = sequence
        summary_path.write_text(json.dumps(summary))
        contract = json.loads(path.read_text())
        contract["startReceipt"] = {"baseCommit": "a" * 40, "path": "receipt.json"}
        path.write_text(json.dumps(contract))
        entries.append((path, contract, summary, ai_check_pr.archive_pair_rank(path, summary_path)))
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result(returncode=0))
    receipt = {
        "receiptVersion": 1,
        "prBaseCommit": "a" * 40,
        "humanAuthorization": {"type": "agent", "reference": "forged"},
        "archives": [ai_check_pr.recovery_receipt_entry(entry) for entry in entries],
    }

    assert ai_check_pr.historical_recovery_receipt_paths(entries, "a" * 40, receipt) == set()


def test_historical_recovery_receipts_load_only_json_files(tmp_path, monkeypatch):
    directory = tmp_path / ".ai" / "work-items" / "recovery-receipts"
    directory.mkdir(parents=True)
    (directory / "chain.json").write_text('{"receiptVersion": 1}', encoding="utf-8")
    (directory / "note.txt").write_text("ignored", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    assert ai_check_pr.historical_recovery_receipts() == [
        (".ai/work-items/recovery-receipts/chain.json", {"receiptVersion": 1})
    ]


def test_historical_recovery_receipts_accepts_no_receipt_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    assert ai_check_pr.historical_recovery_receipts() == []


def test_historical_recovery_receipts_preserve_invalid_json_as_fail_closed_evidence(
    tmp_path, monkeypatch
):
    directory = tmp_path / ".ai" / "work-items" / "recovery-receipts"
    directory.mkdir(parents=True)
    (directory / "invalid.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    receipts = ai_check_pr.historical_recovery_receipts()

    assert receipts[0][0] == ".ai/work-items/recovery-receipts/invalid.json"
    assert "_loadError" in receipts[0][1]


def test_verified_merged_child_archive_requires_pair_added_on_second_merge_parent(
    tmp_path, monkeypatch
):
    contract_path = write_pair(tmp_path, "child", ["src/child.py"], ["src/child.py"])
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    receipt = build_receipt(contract, project_root=tmp_path)
    receipt_path = tmp_path / receipt["receiptPath"]
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    contract["startReceipt"] = receipt_binding(receipt)
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary_path = contract_path.with_name(contract_path.name.replace(".contract", ".summary"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["archiveSequence"] = 75
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    contract_rel = contract_path.relative_to(tmp_path).as_posix()
    summary_rel = summary_path.relative_to(tmp_path).as_posix()

    def git(args):
        if args[:3] == ["log", "--format=%H", "--diff-filter=A"]:
            return fake_git_result(stdout="archive-addition\n")
        if args == ["diff-tree", "--no-commit-id", "--name-status", "-r", "archive-addition"]:
            return fake_git_result(stdout=f"A\t{contract_rel}\nA\t{summary_rel}\n")
        if args == ["rev-list", "--merges", "--ancestry-path", "a" * 40 + "..HEAD"]:
            return fake_git_result(stdout="parent-merge\n")
        if args == ["show", "-s", "--format=%P", "parent-merge"]:
            return fake_git_result(stdout="parent-one parent-two\n")
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return fake_git_result(
                returncode=0
                if tuple(args[2:])
                in {
                    ("a" * 40, "HEAD"),
                    ("archive-addition", "parent-two"),
                }
                else 1
            )
        return fake_git_result()

    monkeypatch.setattr(ai_check_pr, "run_git", git)

    entry = (
        contract_path,
        contract,
        summary,
        ai_check_pr.archive_pair_rank(contract_path, summary_path),
    )

    assert ai_check_pr.is_verified_merged_child_archive(entry, "a" * 40)


def test_verified_merged_child_archive_rejects_archive_already_in_first_parent(
    tmp_path, monkeypatch
):
    contract_path = write_pair(tmp_path, "child", ["src/child.py"], ["src/child.py"])
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    receipt = build_receipt(contract, project_root=tmp_path)
    receipt_path = tmp_path / receipt["receiptPath"]
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    contract["startReceipt"] = receipt_binding(receipt)
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary_path = contract_path.with_name(contract_path.name.replace(".contract", ".summary"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["archiveSequence"] = 75
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    contract_rel = contract_path.relative_to(tmp_path).as_posix()
    summary_rel = summary_path.relative_to(tmp_path).as_posix()

    def git(args):
        if args[:3] == ["log", "--format=%H", "--diff-filter=A"]:
            return fake_git_result(stdout="archive-addition\n")
        if args == ["diff-tree", "--no-commit-id", "--name-status", "-r", "archive-addition"]:
            return fake_git_result(stdout=f"A\t{contract_rel}\nA\t{summary_rel}\n")
        if args == ["rev-list", "--merges", "--ancestry-path", "a" * 40 + "..HEAD"]:
            return fake_git_result(stdout="parent-merge\n")
        if args == ["show", "-s", "--format=%P", "parent-merge"]:
            return fake_git_result(stdout="parent-one parent-two\n")
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return fake_git_result(
                returncode=0
                if tuple(args[2:])
                in {
                    ("a" * 40, "HEAD"),
                    ("archive-addition", "parent-one"),
                    ("archive-addition", "parent-two"),
                }
                else 1
            )
        return fake_git_result()

    monkeypatch.setattr(ai_check_pr, "run_git", git)

    entry = (
        contract_path,
        contract,
        summary,
        ai_check_pr.archive_pair_rank(contract_path, summary_path),
    )

    assert not ai_check_pr.is_verified_merged_child_archive(entry, "a" * 40)


def test_trusted_merged_child_does_not_hide_multiple_untrusted_work_items(tmp_path, monkeypatch):
    first = write_pair(tmp_path, "first", ["src/a.py"], ["src/a.py"])
    second = write_pair(tmp_path, "second", ["src/b.py"], ["src/b.py"])
    child = write_pair(tmp_path, "child", ["src/c.py"], ["src/c.py"])
    for path, sequence in ((first, 75), (second, 76), (child, 77)):
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["archiveSequence"] = sequence
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    monkeypatch.setattr(
        ai_check_pr,
        "archive_base_is_compatible",
        lambda contract, _base: contract["workItemId"] != "child",
    )
    monkeypatch.setattr(
        ai_check_pr,
        "is_verified_merged_child_archive",
        lambda entry, _base: entry[1]["workItemId"] == "child",
    )
    patch_changes(monkeypatch, ["src/a.py", "src/b.py", "src/c.py"])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [first, second, child])

    assert any(
        "exactly one newly maintained Work Item" in issue and "first" in issue and "second" in issue
        for issue in issues
    )


def test_receipt_verified_prefix_only_extends_through_normal_adjacent_recovery(monkeypatch):
    first, second, third = Path("first"), Path("second"), Path("third")
    entries = [
        (first, {}, {}, (74, "first", "first")),
        (second, {}, {}, (75, "second", "second")),
        (third, {}, {}, (76, "third", "third")),
    ]
    monkeypatch.setattr(
        ai_check_pr, "is_documented_pr_recovery_pair", lambda *_args, **_kwargs: True
    )

    assert ai_check_pr.extend_documented_recovery_paths(entries, "base", {first}) == {
        first,
        second,
        third,
    }


def test_pr_accepts_one_documented_adjacent_recovery_pair(tmp_path, monkeypatch):
    predecessor = write_pair(tmp_path, "predecessor", ["src/a.py"], ["src/a.py"])
    recovery = write_pair(tmp_path, "recovery", ["src/b.py"], ["src/b.py"], approved=True)
    for path, sequence in ((predecessor, 75), (recovery, 76)):
        summary = json.loads(path.with_name(path.name.replace(".contract", ".summary")).read_text())
        summary["archiveSequence"] = sequence
        path.with_name(path.name.replace(".contract", ".summary")).write_text(json.dumps(summary))
    data = json.loads(recovery.read_text())
    data.update(
        {
            "baseCommit": "b" * 40,
            "sources": [{"path": predecessor.relative_to(tmp_path).as_posix()}],
            "startReceipt": {"baseCommit": "b" * 40, "path": ".ai/work-items/starts/recovery.json"},
            "rawRequestSource": {"type": "human"},
        }
    )
    recovery.write_text(json.dumps(data))
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result(returncode=0))
    entries = []
    for path in (predecessor, recovery):
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        entries.append(
            (
                path,
                json.loads(path.read_text()),
                json.loads(summary_path.read_text()),
                ai_check_pr.archive_pair_rank(path, summary_path),
            )
        )
    entries.sort(key=lambda entry: entry[3])
    assert ai_check_pr.documented_recovery_paths(entries, "a" * 40) == {recovery}


def test_recovery_source_accepts_exact_manifest_paired_summary(tmp_path, monkeypatch):
    predecessor = write_pair(tmp_path, "predecessor", ["src/a.py"], ["src/a.py"])
    recovery = {
        "sources": [
            {
                "path": predecessor.with_name("predecessor.summary.json")
                .relative_to(tmp_path)
                .as_posix()
            }
        ]
    }
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    assert ai_check_pr.source_references_archive_pair(recovery, predecessor)


def test_recovery_source_rejects_an_unrelated_summary(tmp_path, monkeypatch):
    predecessor = write_pair(tmp_path, "predecessor", ["src/a.py"], ["src/a.py"])
    recovery = {
        "sources": [
            {"path": predecessor.with_name("older.summary.json").relative_to(tmp_path).as_posix()}
        ]
    }
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    assert not ai_check_pr.source_references_archive_pair(recovery, predecessor)


def test_pr_accepts_a_fully_validated_adjacent_recovery_chain(tmp_path, monkeypatch):
    predecessor = write_pair(tmp_path, "predecessor", ["src/a.py"], ["src/a.py"])
    first_recovery = write_pair(
        tmp_path, "first-recovery", ["src/b.py"], ["src/b.py"], approved=True
    )
    second_recovery = write_pair(
        tmp_path, "second-recovery", ["src/c.py"], ["src/c.py"], approved=True
    )
    paths = (predecessor, first_recovery, second_recovery)
    for path, sequence in zip(paths, (75, 76, 77), strict=True):
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        summary = json.loads(summary_path.read_text())
        summary["archiveSequence"] = sequence
        summary_path.write_text(json.dumps(summary))
    for path, previous, base in (
        (first_recovery, predecessor, "b" * 40),
        (second_recovery, first_recovery, "c" * 40),
    ):
        data = json.loads(path.read_text())
        data.update(
            {
                "baseCommit": base,
                "sources": [{"path": previous.relative_to(tmp_path).as_posix()}],
                "startReceipt": {
                    "baseCommit": base,
                    "path": f".ai/work-items/starts/{path.stem}.json",
                },
                "rawRequestSource": {"type": "human"},
            }
        )
        path.write_text(json.dumps(data))
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    def ancestry_result(args):
        if args[:2] != ["merge-base", "--is-ancestor"]:
            return fake_git_result(returncode=0)
        ancestor, descendant = args[2:]
        valid_edges = {
            ("a" * 40, "b" * 40),
            ("b" * 40, "c" * 40),
        }
        return fake_git_result(returncode=0 if (ancestor, descendant) in valid_edges else 1)

    monkeypatch.setattr(ai_check_pr, "run_git", ancestry_result)
    entries = []
    for path in paths:
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        entries.append(
            (
                path,
                json.loads(path.read_text()),
                json.loads(summary_path.read_text()),
                ai_check_pr.archive_pair_rank(path, summary_path),
            )
        )
    entries.sort(key=lambda entry: entry[3])

    assert ai_check_pr.documented_recovery_paths(entries, "a" * 40) == {
        first_recovery,
        second_recovery,
    }


def test_pr_rejects_a_recovery_chain_with_a_broken_later_link(tmp_path, monkeypatch):
    predecessor = write_pair(tmp_path, "predecessor", ["src/a.py"], ["src/a.py"])
    first_recovery = write_pair(
        tmp_path, "first-recovery", ["src/b.py"], ["src/b.py"], approved=True
    )
    second_recovery = write_pair(
        tmp_path, "second-recovery", ["src/c.py"], ["src/c.py"], approved=True
    )
    paths = (predecessor, first_recovery, second_recovery)
    for path, sequence in zip(paths, (75, 76, 77), strict=True):
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        summary = json.loads(summary_path.read_text())
        summary["archiveSequence"] = sequence
        summary_path.write_text(json.dumps(summary))
    for path, previous, base in (
        (first_recovery, predecessor, "b" * 40),
        (second_recovery, predecessor, "c" * 40),
    ):
        data = json.loads(path.read_text())
        data.update(
            {
                "baseCommit": base,
                "sources": [{"path": previous.relative_to(tmp_path).as_posix()}],
                "startReceipt": {
                    "baseCommit": base,
                    "path": f".ai/work-items/starts/{path.stem}.json",
                },
                "rawRequestSource": {"type": "human"},
            }
        )
        path.write_text(json.dumps(data))
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result(returncode=0))
    entries = []
    for path in paths:
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        entries.append(
            (
                path,
                json.loads(path.read_text()),
                json.loads(summary_path.read_text()),
                ai_check_pr.archive_pair_rank(path, summary_path),
            )
        )

    assert ai_check_pr.documented_recovery_paths(entries, "a" * 40) == set()


def test_pr_recovery_pair_requires_predecessor_reference(tmp_path, monkeypatch):
    predecessor = write_pair(tmp_path, "predecessor", ["src/a.py"], ["src/a.py"])
    recovery = write_pair(tmp_path, "recovery", ["src/b.py"], ["src/b.py"], approved=True)
    for path, sequence in ((predecessor, 75), (recovery, 76)):
        summary = json.loads(path.with_name(path.name.replace(".contract", ".summary")).read_text())
        summary["archiveSequence"] = sequence
        path.with_name(path.name.replace(".contract", ".summary")).write_text(json.dumps(summary))
    data = json.loads(recovery.read_text())
    data.update(
        {
            "baseCommit": "b" * 40,
            "startReceipt": {"baseCommit": "b" * 40, "path": ".ai/work-items/starts/recovery.json"},
            "rawRequestSource": {"type": "human"},
        }
    )
    recovery.write_text(json.dumps(data))
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result(returncode=0))
    entries = []
    for path in (predecessor, recovery):
        summary_path = path.with_name(path.name.replace(".contract", ".summary"))
        entries.append(
            (
                path,
                json.loads(path.read_text()),
                json.loads(summary_path.read_text()),
                ai_check_pr.archive_pair_rank(path, summary_path),
            )
        )
    entries.sort(key=lambda entry: entry[3])
    assert ai_check_pr.documented_recovery_paths(entries, "a" * 40) == set()


def test_pr_rejects_work_item_based_on_different_merge_base(tmp_path, monkeypatch):
    pair = write_pair(tmp_path, "wrong_base", ["src/wrong.py"], ["src/wrong.py"])
    summary_path = pair.with_name(pair.name.replace(".contract", ".summary"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["archiveSequence"] = 75
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(
        monkeypatch,
        [
            "src/wrong.py",
            ".ai/work-items/archive/2026/wrong_base.contract.json",
            ".ai/work-items/archive/2026/wrong_base.summary.json",
        ],
    )

    issues = ai_check_pr.validate_pr_bundle("b" * 40, [pair])

    assert any("baseCommit is not compatible with the PR merge-base" in issue for issue in issues)


def test_pr_accepts_frozen_archive_on_verified_ancestor_base(monkeypatch):
    contract = {
        "baseCommit": "a" * 40,
        "startReceipt": {
            "baseCommit": "a" * 40,
            "path": ".ai/work-items/starts/frozen.json",
        },
    }
    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result(returncode=0))
    assert ai_check_pr.archive_base_is_compatible(contract, "b" * 40)


def test_pr_rejects_rebased_archive_without_receipt_binding(monkeypatch):
    contract = {"baseCommit": "a" * 40}
    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result(returncode=0))
    assert not ai_check_pr.archive_base_is_compatible(contract, "b" * 40)


def test_pr_rejects_rewriting_existing_archived_evidence(monkeypatch):
    archived_contract = ".ai/work-items/archive/2026/existing.contract.json"
    monkeypatch.setattr(
        ai_check_pr, "archive_evidence_changes", lambda _base: {archived_contract: "M"}
    )
    monkeypatch.setattr(ai_check_pr, "changed_name_status", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ai_check_pr, "changed_paths", lambda *_args, **_kwargs: [])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [])

    assert any("archive PR policy is append-only" in issue for issue in issues)


def test_pr_accepts_only_canonical_resumed_lineage(monkeypatch):
    original = "a" * 40
    resumed = "b" * 40
    contract = {
        "baseCommit": resumed,
        "startReceipt": {
            "baseCommit": original,
            "path": ".ai/work-items/starts/resumed.json",
        },
        "resumeHistory": [
            {
                "resumeVersion": 1,
                "fromBaseCommit": original,
                "toBaseCommit": resumed,
                "baseRemote": "origin",
                "baseBranch": "main",
                "workBranch": "codex/resumed",
                "recordedAt": "2026-07-28T00:00:00+00:00",
                "priorContractDigest": "c" * 64,
                "predecessorWorkItemId": "corrective",
                "predecessorMergeCommit": resumed,
                "predecessorManifestPath": (
                    ".ai/work-items/archive/2026/corrective.archive-manifest.json"
                ),
                "predecessorClosure": {
                    "statusClosed": True,
                    "prMerged": True,
                    "closureSucceeded": True,
                    "localBranchDeleted": True,
                    "remoteBranchDeleted": True,
                    "baseSynchronized": True,
                },
            }
        ],
    }
    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result(returncode=0))

    assert ai_check_pr.archive_base_is_compatible(contract, resumed)
    contract["resumeHistory"][0]["fromBaseCommit"] = "f" * 40
    assert not ai_check_pr.archive_base_is_compatible(contract, resumed)


def test_aggregate_pr_reports_missing_summary_and_invalid_json(tmp_path, monkeypatch):
    archive = tmp_path / ".ai" / "work-items" / "archive" / "2026"
    archive.mkdir(parents=True)
    missing = archive / "missing.contract.json"
    missing.write_text("{}", encoding="utf-8")
    malformed = archive / "malformed.contract.json"
    malformed.write_text("{", encoding="utf-8")
    (archive / "malformed.summary.json").write_text("{}", encoding="utf-8")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(monkeypatch, [])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [missing, malformed])

    assert any("Summary" in issue for issue in issues)
    assert any("failed to load archive pair" in issue for issue in issues)


def test_aggregate_pr_main_reports_missing_base_and_validation_issues(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(sys, "argv", ["ai_check_pr.py"])
    assert ai_check_pr.main() == 2
    assert "--base or AI_BASE_COMMIT is required" in capsys.readouterr().err

    contract = tmp_path / "fixture.contract.json"
    contract.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["ai_check_pr.py", "--base", "a" * 40, str(contract)])
    monkeypatch.setattr(ai_check_pr, "validate_pr_bundle", lambda *_args: ["fixture issue"])
    assert ai_check_pr.main() == 1
    assert "fixture issue" in capsys.readouterr().err


def test_aggregate_pr_accepts_generated_archive_index_named_by_summary(tmp_path, monkeypatch):
    archive_index = ".ai/work-items/archive/index.json"
    pair = write_pair(tmp_path, "generated_index", ["src/change.py"], [archive_index])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(
        monkeypatch,
        [
            archive_index,
            pair.relative_to(tmp_path).as_posix(),
            str(pair.relative_to(tmp_path)).replace(".contract", ".summary"),
        ],
    )

    assert ai_check_pr.validate_pr_bundle("a" * 40, [pair]) == []


def test_aggregate_pr_rejects_unclaimed_generated_archive_index(tmp_path, monkeypatch):
    pair = write_pair(tmp_path, "unclaimed_index", ["src/change.py"], ["src/change.py"])
    archive_index = ".ai/work-items/archive/index.json"
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(
        monkeypatch,
        [
            archive_index,
            pair.relative_to(tmp_path).as_posix(),
            str(pair.relative_to(tmp_path)).replace(".contract", ".summary"),
        ],
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [pair])
    assert any("lacks paired ownership" in issue and archive_index in issue for issue in issues)


def test_aggregate_pr_accepts_archive_bound_release_metadata(tmp_path, monkeypatch):
    release_paths = [
        ".ai/cockpit/release-digests.json",
        ".ai/cockpit/release-freeze.json",
        "docs/reference/capability-truth-matrix.json",
        "release-state.json",
        "release.json",
    ]
    pair = write_pair(
        tmp_path, "archive_bound", release_paths, [".ai/work-items/archive/index.json"]
    )
    freeze = tmp_path / ".ai" / "cockpit" / "release-freeze.json"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text(json.dumps({"lifecycle": {"state": "premerge_finalized"}}), encoding="utf-8")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(
        monkeypatch,
        release_paths
        + [
            pair.relative_to(tmp_path).as_posix(),
            str(pair.relative_to(tmp_path)).replace(".contract", ".summary"),
        ],
    )

    assert ai_check_pr.validate_pr_bundle("a" * 40, [pair]) == []


def test_aggregate_pr_rejects_archive_bound_metadata_without_premerge_marker(tmp_path, monkeypatch):
    path = "release.json"
    pair = write_pair(
        tmp_path,
        "archive_bound_missing_marker",
        [path],
        [".ai/work-items/archive/index.json"],
    )
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(
        monkeypatch,
        [
            path,
            pair.relative_to(tmp_path).as_posix(),
            str(pair.relative_to(tmp_path)).replace(".contract", ".summary"),
        ],
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [pair])
    assert any("lacks paired ownership" in issue and path in issue for issue in issues)


def test_aggregate_pr_rejects_capability_truth_without_contract_ownership(tmp_path, monkeypatch):
    path = "docs/reference/capability-truth-matrix.json"
    pair = write_pair(
        tmp_path,
        "archive_bound_matrix_unowned",
        ["release.json"],
        [".ai/work-items/archive/index.json"],
    )
    freeze = tmp_path / ".ai" / "cockpit" / "release-freeze.json"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text(json.dumps({"lifecycle": {"state": "premerge_finalized"}}), encoding="utf-8")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(
        monkeypatch,
        [
            path,
            pair.relative_to(tmp_path).as_posix(),
            str(pair.relative_to(tmp_path)).replace(".contract", ".summary"),
        ],
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [pair])
    assert any("lacks paired ownership" in issue and path in issue for issue in issues)


def test_aggregate_pr_rejects_uncovered_earlier_path(tmp_path, monkeypatch):
    closing = write_pair(tmp_path, "closing", ["src/closing.py"], ["src/closing.py"])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(monkeypatch, ["src/earlier.py", "src/closing.py"])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [closing])
    assert (
        "complete PR diff path lacks paired ownership (same Contract scope and Summary changedFiles): src/earlier.py"
        in issues
    )


def test_aggregate_pr_rejects_cross_pair_scope_and_summary_claims(tmp_path, monkeypatch):
    first = write_pair(tmp_path, "first", ["src/a.py"], ["src/b.py"])
    second = write_pair(tmp_path, "second", ["src/b.py"], ["src/a.py"])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(monkeypatch, ["src/a.py", "src/b.py"])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [first, second])
    assert len([issue for issue in issues if "lacks paired ownership" in issue]) == 2


def test_aggregate_pr_prefers_latest_effective_owner(tmp_path, monkeypatch):
    first = write_pair(tmp_path, "first", ["src/shared.py"], ["src/shared.py"])
    second = write_pair(tmp_path, "second", ["src/shared.py"], ["src/shared.py"])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(monkeypatch, ["src/shared.py"])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [first, second])
    assert issues == []


def test_archive_pair_rank_prefers_explicit_archive_sequence(tmp_path, monkeypatch):
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    first = write_pair(tmp_path, "z_first", ["src/shared.py"], ["src/shared.py"])
    second = write_pair(tmp_path, "a_second", ["src/shared.py"], ["src/shared.py"])
    first_summary = Path(str(first).replace(".contract.json", ".summary.json"))
    second_summary = Path(str(second).replace(".contract.json", ".summary.json"))
    for path, sequence in ((first_summary, 20), (second_summary, 21)):
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["archiveSequence"] = sequence
        path.write_text(json.dumps(summary), encoding="utf-8")

    assert ai_check_pr.archive_pair_rank(first, first_summary)[0] == 20
    assert ai_check_pr.archive_pair_rank(second, second_summary)[0] == 21


def test_new_archive_requires_sequence_evidence(tmp_path, monkeypatch):
    contract_path = write_pair(tmp_path, "new_pair", ["src/shared.py"], ["src/shared.py"])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    monkeypatch.setattr(ai_check_pr, "run_git", lambda *_args: fake_git_result())
    patch_changes(monkeypatch, ["src/shared.py"])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [contract_path])
    assert any("archiveSequence must be a positive integer" in issue for issue in issues)


def test_aggregate_pr_prefers_higher_rank_over_input_order(tmp_path, monkeypatch):
    first = write_pair(
        tmp_path, "z_unapproved", [".github/workflows/ci.yml"], [".github/workflows/ci.yml"]
    )
    second = write_pair(
        tmp_path,
        "a_approved",
        [".github/workflows/ci.yml"],
        [".github/workflows/ci.yml"],
        approved=True,
    )
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    monkeypatch.setattr(
        ai_check_pr,
        "archive_pair_rank",
        lambda contract_path, summary_path: {
            first: (
                20,
                first.relative_to(tmp_path).as_posix(),
                first.relative_to(tmp_path).as_posix().replace(".contract", ".summary"),
            ),
            second: (
                10,
                second.relative_to(tmp_path).as_posix(),
                second.relative_to(tmp_path).as_posix().replace(".contract", ".summary"),
            ),
        }[contract_path],
    )
    patch_changes(
        monkeypatch,
        [
            ".github/workflows/ci.yml",
            first.relative_to(tmp_path).as_posix(),
            first.relative_to(tmp_path).as_posix().replace(".contract", ".summary"),
            second.relative_to(tmp_path).as_posix(),
            second.relative_to(tmp_path).as_posix().replace(".contract", ".summary"),
        ],
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [second, first])
    assert any("restricted path lacks approval" in issue for issue in issues)


def test_aggregate_pr_rejects_when_higher_ranked_archive_is_unapproved(tmp_path, monkeypatch):
    first = write_pair(
        tmp_path,
        "a_approved",
        [".github/workflows/ci.yml"],
        [".github/workflows/ci.yml"],
        approved=True,
    )
    second = write_pair(
        tmp_path, "z_unapproved", [".github/workflows/ci.yml"], [".github/workflows/ci.yml"]
    )
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    monkeypatch.setattr(
        ai_check_pr,
        "archive_pair_rank",
        lambda contract_path, summary_path: {
            first: (
                10,
                first.relative_to(tmp_path).as_posix(),
                first.relative_to(tmp_path).as_posix().replace(".contract", ".summary"),
            ),
            second: (
                20,
                second.relative_to(tmp_path).as_posix(),
                second.relative_to(tmp_path).as_posix().replace(".contract", ".summary"),
            ),
        }[contract_path],
    )
    patch_changes(
        monkeypatch,
        [
            ".github/workflows/ci.yml",
            first.relative_to(tmp_path).as_posix(),
            first.relative_to(tmp_path).as_posix().replace(".contract", ".summary"),
            second.relative_to(tmp_path).as_posix(),
            second.relative_to(tmp_path).as_posix().replace(".contract", ".summary"),
        ],
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [first, second])
    assert any("restricted path lacks approval" in issue for issue in issues)


def test_aggregate_pr_preserves_discovery_order_for_default_archive_paths(tmp_path, monkeypatch):
    first = write_pair(tmp_path, "first", ["src/first.py"], ["src/first.py"])
    second = write_pair(tmp_path, "second", ["src/second.py"], ["src/second.py"])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    monkeypatch.setattr(
        ai_check_pr,
        "run_git",
        lambda args: type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": "\n".join(
                    [
                        f"A\t{second.relative_to(tmp_path).as_posix()}",
                        f"A\t{second.relative_to(tmp_path).as_posix().replace('.contract', '.summary')}",
                        f"A\t{first.relative_to(tmp_path).as_posix()}",
                        f"A\t{first.relative_to(tmp_path).as_posix().replace('.contract', '.summary')}",
                    ]
                )
                + "\n",
                "stderr": "",
            },
        )(),
    )
    monkeypatch.setattr(
        ai_check_pr, "changed_paths", lambda *args, **kwargs: ["src/second.py", "src/first.py"]
    )

    assert ai_check_pr.archived_contract_paths("a" * 40) == [second, first]


@pytest.mark.parametrize(
    ("worktree_hash", "parent_hash", "expected"),
    [
        ("dirty-worktree", "parent-blob", False),
        ("shared-blob", "shared-blob", True),
    ],
)
def test_no_op_restore_uses_current_worktree_not_head(
    tmp_path, monkeypatch, worktree_hash, parent_hash, expected
):
    base = "a" * 40
    path = ".ai/work-items/archive/2026/example.summary.json"
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    calls = []

    def fake_run_git(args):
        calls.append(tuple(args))
        if args == ["hash-object", "--no-filters", path]:
            return fake_git_result(stdout=f"{worktree_hash}\n")
        if args == ["rev-parse", f"{base}:{path}"]:
            return fake_git_result(stdout=f"{parent_hash}\n")
        if args == ["rev-parse", f"HEAD:{path}"]:
            raise AssertionError("no-op restore check must not consult HEAD")
        return fake_git_result(stdout="\n")

    monkeypatch.setattr(ai_check_pr, "run_git", fake_run_git)

    assert ai_check_pr._is_no_op_restore(base, path) is expected
    assert ["hash-object", "--no-filters", path] in [list(call) for call in calls]


def test_no_op_restore_accepts_direct_parent_of_pr_base(tmp_path, monkeypatch):
    base = "a" * 40
    path = ".ai/work-items/archive/2026/example.summary.json"
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    def fake_run_git(args):
        if args == ["hash-object", "--no-filters", path]:
            return fake_git_result(stdout="parent-blob\n")
        if args == ["rev-parse", f"{base}:{path}"]:
            return fake_git_result(stdout="bad-base-blob\n")
        if args == ["rev-parse", f"{base}^:{path}"]:
            return fake_git_result(stdout="parent-blob\n")
        return fake_git_result(stdout="\n")

    monkeypatch.setattr(ai_check_pr, "run_git", fake_run_git)

    assert ai_check_pr._is_no_op_restore(base, path) is True


def test_pr_bundle_does_not_exempt_dirty_archive_restore_from_ownership(tmp_path, monkeypatch):
    new = write_pair(tmp_path, "new", ["src/new.py"], ["src/new.py"])
    new_contract = new.relative_to(tmp_path).as_posix()
    new_summary = new_contract.replace(".contract", ".summary")
    restored_summary = ".ai/work-items/archive/2026/restored.summary.json"
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)

    def fake_run_git(args):
        if args == ["diff", "--name-status", "-z", "a" * 40 + "...HEAD"]:
            return fake_git_result(
                stdout="\0".join([f"A\t{new_contract}", f"A\t{new_summary}"]) + "\0"
            )
        if args == ["hash-object", "--no-filters", restored_summary]:
            return fake_git_result(stdout="dirty-worktree\n")
        if args == ["rev-parse", f"{'a' * 40}:{restored_summary}"]:
            return fake_git_result(stdout="parent-blob\n")
        return fake_git_result(stdout="\n")

    monkeypatch.setattr(ai_check_pr, "run_git", fake_run_git)
    patch_changes(
        monkeypatch,
        [new_contract, new_summary, restored_summary],
        statuses={restored_summary: "M"},
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [new])

    assert any(
        "complete PR diff path lacks paired ownership" in issue and restored_summary in issue
        for issue in issues
    )
    assert not any(
        "archive PR policy is append-only" in issue and restored_summary in issue
        for issue in issues
    )


def test_pr_bundle_still_exempts_clean_archive_restore_from_ownership(tmp_path, monkeypatch):
    new = write_pair(tmp_path, "new", ["src/new.py"], ["src/new.py"])
    new_contract = new.relative_to(tmp_path).as_posix()
    new_summary = new_contract.replace(".contract", ".summary")
    restored_summary = ".ai/work-items/archive/2026/restored.summary.json"
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)

    def fake_run_git(args):
        if args == ["diff", "--name-status", "-z", "a" * 40 + "...HEAD"]:
            return fake_git_result(
                stdout="\0".join([f"A\t{new_contract}", f"A\t{new_summary}"]) + "\0"
            )
        if args == ["hash-object", "--no-filters", restored_summary]:
            return fake_git_result(stdout="shared-blob\n")
        if args == ["rev-parse", f"{'a' * 40}:{restored_summary}"]:
            return fake_git_result(stdout="shared-blob\n")
        return fake_git_result(stdout="\n")

    monkeypatch.setattr(ai_check_pr, "run_git", fake_run_git)
    patch_changes(
        monkeypatch,
        [new_contract, new_summary, restored_summary],
        statuses={restored_summary: "M"},
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [new])

    assert not any(
        "complete PR diff path lacks paired ownership" in issue and restored_summary in issue
        for issue in issues
    )


def test_pr_bundle_ignores_clean_archive_restore_as_archive_evidence(tmp_path, monkeypatch):
    new = write_pair(tmp_path, "new", ["src/new.py"], ["src/new.py"])
    new_contract = new.relative_to(tmp_path).as_posix()
    new_summary = new_contract.replace(".contract", ".summary")
    restored_summary = ".ai/work-items/archive/2026/restored.summary.json"
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)

    def fake_run_git(args):
        if args == ["diff", "--name-status", "-z", "a" * 40 + "...HEAD"]:
            return fake_git_result(
                stdout="\0".join(
                    [f"A\t{new_contract}", f"A\t{new_summary}", f"M\t{restored_summary}"]
                )
                + "\0"
            )
        if args == ["hash-object", "--no-filters", restored_summary]:
            return fake_git_result(stdout="shared-blob\n")
        if args == ["rev-parse", f"{'a' * 40}:{restored_summary}"]:
            return fake_git_result(stdout="shared-blob\n")
        return fake_git_result(stdout="\n")

    monkeypatch.setattr(ai_check_pr, "run_git", fake_run_git)
    patch_changes(
        monkeypatch,
        [new_contract, new_summary, restored_summary],
        statuses={restored_summary: "M"},
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [new])

    assert not any(restored_summary in issue for issue in issues)


def test_aggregate_pr_rejects_contract_v1_downgrade(tmp_path, monkeypatch):
    legacy = write_pair(tmp_path, "legacy", ["src/a.py"], ["src/a.py"])
    contract = json.loads(legacy.read_text(encoding="utf-8"))
    contract["contractVersion"] = 1
    contract["verification"] = [{"command": "sh -c 'true'", "required": True}]
    legacy.write_text(json.dumps(contract), encoding="utf-8")
    summary_path = Path(str(legacy).replace(".contract.json", ".summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["verification"] = [{"command": "sh -c 'true'", "result": "passed"}]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(monkeypatch, ["src/a.py"])

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [legacy])
    assert any("PR archive evidence requires contractVersion 2" in issue for issue in issues)


def test_aggregate_pr_accepts_v2_summary_without_digest_before_migration(tmp_path, monkeypatch):
    legacy = write_pair(tmp_path, "legacy", ["src/a.py"], ["src/a.py"])
    contract = json.loads(legacy.read_text(encoding="utf-8"))
    contract["baseCommit"] = "b" * 40
    legacy.write_text(json.dumps(contract), encoding="utf-8")
    summary_path = Path(str(legacy).replace(".contract.json", ".summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["verification"] = [{"check": "projectTest", "result": "passed"}]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    monkeypatch.setattr(
        ai_check_pr,
        "run_git",
        lambda args: type("Result", (), {"returncode": 1, "stdout": "", "stderr": ""})(),
    )
    patch_changes(
        monkeypatch,
        [
            ".ai/work-items/archive/2026/legacy.contract.json",
            ".ai/work-items/archive/2026/legacy.summary.json",
            "src/a.py",
        ],
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [legacy])

    assert not any("worktreeDigest" in issue for issue in issues)


def test_pr_rejects_summary_only_tampering_even_when_new_work_item_claims_it(tmp_path, monkeypatch):
    old = write_pair(tmp_path, "old", ["src/old.py"], ["src/old.py"])
    old_summary = str(old.relative_to(tmp_path)).replace(".contract", ".summary")
    new = write_pair(tmp_path, "new", [".ai/work-items/archive/**"], [old_summary])
    new_summary = str(new.relative_to(tmp_path)).replace(".contract", ".summary")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    paths = [old_summary, new.relative_to(tmp_path).as_posix(), new_summary]
    patch_changes(monkeypatch, paths, statuses={old_summary: "M"})

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [new])

    assert any(
        "archive PR policy is append-only" in issue and old_summary in issue for issue in issues
    )


def test_pr_rejects_contract_only_archive_modification(tmp_path, monkeypatch):
    contract = write_pair(tmp_path, "old", ["src/old.py"], ["src/old.py"])
    contract_rel = contract.relative_to(tmp_path).as_posix()
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    patch_changes(monkeypatch, [contract_rel], statuses={contract_rel: "M"})

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [])

    assert any("archive PR policy is append-only" in issue for issue in issues)


def test_pr_rejects_archive_delete_and_rename(tmp_path, monkeypatch):
    old = write_pair(tmp_path, "old", ["src/old.py"], ["src/old.py"])
    old_contract = old.relative_to(tmp_path).as_posix()
    old_summary = old_contract.replace(".contract", ".summary")
    renamed = write_pair(tmp_path, "renamed", ["src/old.py"], ["src/old.py"])
    renamed_contract = renamed.relative_to(tmp_path).as_posix()
    renamed_summary = renamed_contract.replace(".contract", ".summary")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    paths = [old_contract, old_summary, renamed_contract, renamed_summary]
    patch_changes(
        monkeypatch,
        paths,
        statuses={old_contract: "D", old_summary: "D"},
    )

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [])

    assert sum("archive PR policy is append-only" in issue for issue in issues) == 2


def test_pr_rejects_archive_restoration_even_when_it_looks_like_a_restore(tmp_path, monkeypatch):
    new = write_pair(tmp_path, "new", ["src/new.py"], ["src/new.py"])
    new_contract = new.relative_to(tmp_path).as_posix()
    new_summary = new_contract.replace(".contract", ".summary")
    old = write_pair(tmp_path, "old", ["src/old.py"], ["src/old.py"])
    old_summary = old.relative_to(tmp_path).as_posix().replace(".contract", ".summary")
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    paths = ["src/new.py", new_contract, new_summary, old_summary]
    patch_changes(monkeypatch, paths, statuses={old_summary: "M"})

    issues = ai_check_pr.validate_pr_bundle("a" * 40, [new])

    assert any(
        "archive PR policy is append-only" in issue and old_summary in issue for issue in issues
    )


def test_pr_keeps_non_archive_modified_paths_valid(tmp_path, monkeypatch):
    pair = write_pair(tmp_path, "task", ["src/shared.py"], ["src/shared.py"])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    changed = pair.relative_to(tmp_path).as_posix()
    patch_changes(
        monkeypatch,
        ["src/shared.py", changed, changed.replace(".contract", ".summary")],
        statuses={"src/shared.py": "M"},
    )

    assert ai_check_pr.validate_pr_bundle("a" * 40, [pair]) == []


def test_pr_bundle_accepts_only_valid_current_archive_report_pair(tmp_path, monkeypatch):
    task = "report-owner"
    archive = f".ai/work-items/archive/2026/{task}"
    contract = write_pair(
        tmp_path,
        task,
        ["scripts/ai_archive_work_item.py", ".ai/work-items/archive/**"],
        [
            f"{archive}.outcome.json",
            ".ai/cockpit/task_report.json",
            ".ai/cockpit/task_report.md",
        ],
    )
    contract_rel = contract.relative_to(tmp_path).as_posix()
    summary_rel = contract_rel.replace(".contract", ".summary")
    outcome_rel = f"{archive}.outcome.json"
    changed = [
        contract_rel,
        summary_rel,
        outcome_rel,
        ".ai/cockpit/task_report.json",
        ".ai/cockpit/task_report.md",
    ]
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    monkeypatch.setattr(
        ai_check_pr,
        "archive_evidence_changes",
        lambda _base: {contract_rel: "A", summary_rel: "A"},
    )
    monkeypatch.setattr(ai_check_pr, "validate_contract", lambda _contract: [])
    monkeypatch.setattr(ai_check_pr, "validate_summary", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ai_check_pr, "human_benefit_report_issues", lambda _contract: [])
    patch_changes(monkeypatch, changed)

    assert ai_check_pr.validate_pr_bundle("a" * 40, [contract]) == []

    monkeypatch.setattr(
        ai_check_pr, "human_benefit_report_issues", lambda _contract: ["report is stale"]
    )
    issues = ai_check_pr.validate_pr_bundle("a" * 40, [contract])
    assert any("task_report.json" in issue for issue in issues)
    assert any("task_report.md" in issue for issue in issues)


def test_pr_bundle_accepts_summary_bound_generated_archive_artifacts_outside_scope(
    tmp_path, monkeypatch
):
    task = "generated-archive"
    archive = f".ai/work-items/archive/2026/{task}"
    generated = [
        f"{archive}.outcome.json",
        f"{archive}.outcome.md",
        f"{archive}.archive-manifest.json",
    ]
    contract = write_pair(
        tmp_path,
        task,
        ["scripts/ai_archive_work_item.py"],
        generated,
    )
    contract_rel = contract.relative_to(tmp_path).as_posix()
    summary_rel = contract_rel.replace(".contract", ".summary")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ai_check_pr,
        "archive_evidence_changes",
        lambda _base: {contract_rel: "A", summary_rel: "A"},
    )
    monkeypatch.setattr(ai_check_pr, "validate_contract", lambda _contract: [])
    monkeypatch.setattr(ai_check_pr, "validate_summary", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ai_check_pr, "human_benefit_report_issues", lambda _contract: [])
    policy = tmp_path / "scope.yaml"
    policy.write_text("allowAlways:\n", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "SCOPE_POLICY", policy)
    changed = [contract_rel, summary_rel, *generated]
    patch_changes(monkeypatch, changed)

    assert ai_check_pr.validate_pr_bundle("a" * 40, [contract]) == []


def test_human_benefit_report_issues_rejects_stale_review_report(tmp_path, monkeypatch):
    from ai_generate_human_report import generate_human_report, render_human_report

    contract_path = tmp_path / ".ai/work-items/archive/2026/example.contract.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text("{}", encoding="utf-8")
    outcome_path = contract_path.with_name("example.outcome.json")
    sections = {
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
    }
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
        "sections": sections,
    }
    outcome_path.write_text(json.dumps(outcome), encoding="utf-8")
    cockpit = tmp_path / ".ai/cockpit"
    cockpit.mkdir(parents=True)
    report = generate_human_report(outcome)
    (cockpit / "task_report.json").write_text(json.dumps(report), encoding="utf-8")
    (cockpit / "task_report.md").write_text(render_human_report(report), encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    assert ai_check_pr.human_benefit_report_issues(contract_path) == []
    report["issues"]["detected"] = 9
    (cockpit / "task_report.json").write_text(json.dumps(report), encoding="utf-8")
    assert ai_check_pr.human_benefit_report_issues(contract_path) == [
        "report is stale or inconsistent with Task Outcome"
    ]


def test_human_benefit_report_issues_rejects_non_green_current_outcome(tmp_path, monkeypatch):
    task = "current-green-gate"
    archive_dir = tmp_path / ".ai/work-items/archive/2026"
    archive_dir.mkdir(parents=True)
    contract_path = archive_dir / f"{task}.contract.json"
    summary_path = archive_dir / f"{task}.summary.json"
    outcome_path = archive_dir / f"{task}.outcome.json"
    contract_path.write_text(
        json.dumps({"contractVersion": 2, "workItemId": task, "baseCommit": "a" * 40}),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps({"workItemId": task}), encoding="utf-8")
    outcome_path.write_text(
        json.dumps(
            {"workItemId": task, "status": "needs_human_confirmation", "humanStatusColor": "yellow"}
        ),
        encoding="utf-8",
    )
    outcome_path.with_suffix(".md").write_text("# Task Outcome\n", encoding="utf-8")
    cockpit = tmp_path / ".ai/cockpit"
    cockpit.mkdir(parents=True)
    (cockpit / "task_report.json").write_text("{}", encoding="utf-8")
    (cockpit / "task_report.md").write_text("", encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)

    issues = ai_check_pr.human_benefit_report_issues(contract_path)

    assert any("completed" in issue for issue in issues)
    assert any("green" in issue for issue in issues)


@pytest.mark.parametrize(
    ("superseded", "expected_issues"),
    [
        (True, []),
        (False, ["report is stale or inconsistent with Task Outcome"]),
    ],
)
def test_human_benefit_report_uses_archive_projection_only_for_valid_supersession(
    tmp_path, monkeypatch, superseded, expected_issues
):
    from ai_generate_human_report import generate_human_report, render_human_report

    task = "superseded-report"
    archive_dir = tmp_path / ".ai/work-items/archive/2026"
    archive_dir.mkdir(parents=True)
    contract_path = archive_dir / f"{task}.contract.json"
    contract_path.write_text(json.dumps({"workItemId": task}), encoding="utf-8")
    active_outcome = f".ai/work-items/active/{task}.outcome.json"
    archived_outcome = f".ai/work-items/archive/2026/{task}.outcome.json"
    outcome = {
        "format": "ai-cockpit-task-outcome",
        "schemaVersion": 1,
        "workItemId": task,
        "status": "blocked",
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
        "sections": {
            "outcomeSummary": "Blocked.",
            "taskOverview": "Superseded predecessor.",
            "deliveredChanges": [active_outcome],
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
            "evidence": [{"source": active_outcome, "subject": "Outcome"}],
        },
    }
    (archive_dir / f"{task}.outcome.json").write_text(json.dumps(outcome), encoding="utf-8")
    projected = json.loads(json.dumps(outcome).replace(active_outcome, archived_outcome))
    cockpit = tmp_path / ".ai/cockpit"
    cockpit.mkdir(parents=True)
    report = generate_human_report(projected, phase="review")
    (cockpit / "task_report.json").write_text(json.dumps(report), encoding="utf-8")
    (cockpit / "task_report.md").write_text(render_human_report(report), encoding="utf-8")
    monkeypatch.setattr(ai_check_pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ai_check_pr,
        "is_valid_superseded_transition",
        lambda **_kwargs: superseded,
        raising=False,
    )

    assert ai_check_pr.human_benefit_report_issues(contract_path) == expected_issues
