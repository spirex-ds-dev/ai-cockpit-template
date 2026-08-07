import hashlib
import json

import ai_check_diff_ownership as ownership
import ai_check_status_consistency as status_consistency
import ai_generate_human_report as human


def contract(scope, *, excluded=(), approved=False):
    return {
        "scope": list(scope),
        "outOfScope": list(excluded),
        "restrictedWriteApproval": {"approved": approved},
    }


def test_classify_active_archived_and_unowned_paths():
    active = ownership.Owner("active", "active", contract(["src/**"]), None)
    archived = ownership.Owner(
        "archived", "archive", contract(["docs/**"]), {"changedFiles": [{"path": "docs/a.md"}]}
    )
    policy = {}
    assert ownership.classify("src/a.py", [active], policy).state == "active_owned"
    assert ownership.classify("docs/a.md", [archived], policy).state == "archived_owned"
    assert ownership.classify("ci/a.yml", [active, archived], policy).state == "unowned"


def test_start_receipt_binding_implicitly_owns_receipt_path():
    owner = ownership.Owner(
        "active",
        "receipt",
        contract(["scripts/ai_start.py"])
        | {"startReceipt": {"path": ".ai/work-items/starts/receipt.json"}},
        None,
    )
    assert ownership.covers(owner, ".ai/work-items/starts/receipt.json") == (True, False)


def test_active_owner_implicitly_owns_its_outcome_paths():
    owner = ownership.Owner("active", "task", contract([]), None)

    assert ownership.covers(owner, ".ai/work-items/active/task.outcome.json") == (True, False)
    assert ownership.covers(owner, ".ai/work-items/active/task.outcome.md") == (True, False)
    assert ownership.covers(owner, ".ai/work-items/active/other.outcome.json") == (False, False)


def test_covers_requires_archived_summary_and_approval_is_explicit():
    archived_without_summary = ownership.Owner(
        "archived", "missing-summary", contract(["docs/**"]), None
    )
    assert ownership.covers(archived_without_summary, "docs/readme.md") == (False, False)
    archived_missing_path = ownership.Owner(
        "archived", "missing-path", contract(["docs/**"]), {"changedFiles": []}
    )
    assert ownership.covers(archived_missing_path, "docs/readme.md") == (False, False)
    assert ownership.approved(
        ownership.Owner("active", "approved", contract([], approved=True), None)
    )
    assert not ownership.approved(ownership.Owner("active", "unapproved", contract([]), None))


def test_owners_discovers_active_contracts_without_pr_base(monkeypatch, tmp_path):
    active_path = tmp_path / "task.contract.json"
    active_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(ownership, "ACTIVE_DIR", tmp_path)
    monkeypatch.setattr(ownership, "ARCHIVE_DIR", tmp_path / "archive")
    discovered = ownership.Owner("active", "task", contract(["docs/**"]), None)
    monkeypatch.setattr(ownership, "load_pair", lambda _path, _kind: discovered)
    owners = ownership.owners(active_contract=None, base="")
    assert owners == [discovered]


def test_owners_uses_active_contract_and_covers_exclusions():
    active_contract = contract(["docs/**"], excluded=["docs/private/**"])
    owners = ownership.owners(active_contract=active_contract, base="")
    assert owners[0].kind == "active"
    assert ownership.covers(owners[0], "docs/private/secret.md") == (False, True)


def test_active_follow_up_overrides_archived_path_evidence():
    active = ownership.Owner("active", "follow-up", contract(["docs/**"]), None)
    archived = ownership.Owner(
        "archived", "old", contract(["docs/**"]), {"changedFiles": [{"path": "docs/a.md"}]}
    )
    result = ownership.classify("docs/a.md", [active, archived], {})
    assert result.state == "active_owned"
    assert result.owners == ["active:follow-up"]


def test_classify_ambiguous_out_of_scope_and_restricted_paths():
    first = ownership.Owner("active", "first", contract(["docs/**"]), None)
    second = ownership.Owner("active", "second", contract(["docs/**"]), None)
    assert ownership.classify("docs/a.md", [first, second], {}).state == "ambiguous"
    excluded = ownership.Owner(
        "active", "excluded", contract(["docs/**"], excluded=["docs/private/**"]), None
    )
    assert ownership.classify("docs/private/a.md", [excluded], {}).state == "out_of_scope"


def test_declared_test_effect_cannot_claim_runtime_code():
    contract = {"requestedOperation": {"effect": "test", "environment": "repository"}}
    result = ownership.declared_operation_conflict(
        "scripts/runtime.py", contract["requestedOperation"]
    )
    assert result == "declared test effect conflicts with runtime code diff"


def test_sandbox_workflow_change_fails_closed():
    operation = {"effect": "enforce", "environment": "sandbox"}
    assert "workflow Diff" in ownership.declared_operation_conflict(
        ".github/workflows/ci.yml", operation
    )
    restricted = {
        ".github/**": {
            "aiWrite": "restricted",
            "reviewFocus": "CI",
            "requiredTests": "workflow tests",
        }
    }
    result = ownership.classify(
        ".github/a.yml",
        [ownership.Owner("active", "ci", contract([".github/**"]), None)],
        restricted,
    )
    assert result.state == "approval_required"
    assert "review focus: CI" in result.detail
    assert "required tests: workflow tests" in result.detail


def test_classify_forbidden_paths_are_not_owned():
    active = ownership.Owner("active", "local", contract([".env"]), None)
    policy = {".env": {"aiWrite": "forbidden"}}
    result = ownership.classify(".env", [active], policy)
    assert result.state == "unowned"
    assert "forbidden ownership cannot be claimed" in result.detail


def test_preview_uses_local_and_pr_diff_modes(monkeypatch):
    active = ownership.Owner("active", "active", contract(["src/**", "tests/**", ".env"]), None)
    archived = ownership.Owner(
        "archived", "docs", contract(["docs/**"]), {"changedFiles": [{"path": "docs/guide.md"}]}
    )
    calls = []

    def fake_changed_name_status(contract_data, *, ignore_baseline_dirty):
        calls.append((contract_data, ignore_baseline_dirty))
        return [
            ("M", path)
            for path in [
                "src/app.py",
                "tests/test_app.py",
                "docs/guide.md",
                ".github/workflows/ci.yml",
                "config/new.yaml",
                ".env",
            ]
        ]

    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [active, archived])
    monkeypatch.setattr(ownership, "changed_name_status", fake_changed_name_status)
    monkeypatch.setattr(
        ownership,
        "parse_simple_manifest",
        lambda _path: {".github/**": {"aiWrite": "restricted"}, ".env": {"aiWrite": "forbidden"}},
    )

    local = ownership.preview(contract={"baseCommit": "base", "baselineDirtyPaths": []})
    pr = ownership.preview(base="base")
    assert [item.state for item in local] == [
        "unowned",
        "unowned",
        "unowned",
        "archived_owned",
        "active_owned",
        "active_owned",
    ]
    assert [item.state for item in pr] == [
        "unowned",
        "unowned",
        "unowned",
        "archived_owned",
        "active_owned",
        "active_owned",
    ]
    assert calls[0][1] is False
    assert calls[1][1] is True
    assert ownership.counts(local)["unowned"] == 3


def test_unchanged_dirty_baseline_is_not_claimed_by_new_active_contract(monkeypatch):
    active = ownership.Owner(
        "active",
        "new-task",
        {
            **contract(["docs/**"]),
            "baselineDirtyPaths": [{"path": "docs/old.md", "fingerprint": "same"}],
        },
        None,
    )
    monkeypatch.setattr("ai_common.path_fingerprint", lambda _path: "same")
    assert ownership.classify("docs/old.md", [active], {}).state == "unowned"


def test_preview_rejects_modification_of_existing_archive_evidence(monkeypatch):
    monkeypatch.setattr(
        ownership,
        "changed_name_status",
        lambda *_args, **_kwargs: [
            ("M", ".ai/work-items/archive/2026/old.summary.json"),
            ("A", ".ai/work-items/archive/2026/new.summary.json"),
        ],
    )
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})
    values = ownership.preview(contract={"baseCommit": "base", "baselineDirtyPaths": []})
    old = next(item for item in values if item.path.endswith("old.summary.json"))
    assert old.state == "unowned"
    assert "append-only" in old.detail


def test_pr_preview_accepts_generated_archive_index_declared_by_summary(monkeypatch):
    index_path = ".ai/work-items/archive/index.json"
    monkeypatch.setattr(
        ownership,
        "changed_name_status",
        lambda *_args, **_kwargs: [("M", index_path)],
    )
    monkeypatch.setattr(
        ownership,
        "archive_evidence_changes",
        lambda _base: {
            ".ai/work-items/archive/2026/task.contract.json": "A",
            ".ai/work-items/archive/2026/task.summary.json": "A",
        },
    )
    monkeypatch.setattr(
        ownership,
        "load_json",
        lambda path: (
            {"changedFiles": [{"path": index_path}]}
            if str(path).endswith("task.summary.json")
            else {}
        ),
    )
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})

    assert ownership.preview(base="merge-base") == []


def test_active_preview_accepts_explicit_approved_archive_index_repair(monkeypatch):
    index_path = ".ai/work-items/archive/index.json"
    monkeypatch.setattr(
        ownership,
        "changed_name_status",
        lambda *_args, **_kwargs: [("M", index_path)],
    )
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})

    contract = {
        "archiveIndexRepair": True,
        "restrictedWriteApproval": {"approved": True},
        "baselineDirtyPaths": [],
    }

    assert ownership.preview(contract=contract) == []


def test_preview_skips_generated_no_active_status(monkeypatch, tmp_path):
    status_path = tmp_path / "current_status.md"
    status_path.write_text(
        "---\n"
        "generated: true\n"
        "---\n\n"
        "This file is generated by `scripts/ai_generate_status.py`. Do not update it by hand.\n\n"
        "- Task: `none`\n"
        "- State: `no_active_work_item`\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ownership, "CURRENT_STATUS", status_path)
    monkeypatch.setattr(
        ownership,
        "changed_name_status",
        lambda *_args, **_kwargs: [("M", ".ai/cockpit/current_status.md")],
    )
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})

    assert ownership.preview(contract={"baselineDirtyPaths": []}) == []


def test_preview_does_not_skip_malformed_or_manual_status(monkeypatch, tmp_path):
    status_path = tmp_path / "current_status.md"
    status_path.write_text(
        "This file is generated by `scripts/ai_generate_status.py`. Do not update it by hand.\n"
        "- Task: `none`\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ownership, "CURRENT_STATUS", status_path)
    monkeypatch.setattr(
        ownership,
        "changed_name_status",
        lambda *_args, **_kwargs: [("M", ".ai/cockpit/current_status.md")],
    )
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})

    values = ownership.preview(contract={"baselineDirtyPaths": []})
    assert len(values) == 1
    assert values[0].state == "unowned"


def test_preview_owns_only_exact_generated_human_report_pair(monkeypatch, tmp_path):
    active_dir = tmp_path / "active"
    active_dir.mkdir()
    source = {
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
            "taskOverview": "Example",
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
    outcome_path = active_dir / "example.outcome.json"
    outcome_path.write_text(json.dumps(source), encoding="utf-8")
    report = human.generate_human_report(source)
    report_json = tmp_path / "task_report.json"
    report_md = tmp_path / "task_report.md"
    report_json.write_text(json.dumps(report), encoding="utf-8")
    report_md.write_text(human.render_human_report(report), encoding="utf-8")
    monkeypatch.setattr(ownership, "ACTIVE_DIR", active_dir)
    monkeypatch.setattr(ownership, "HUMAN_REPORT_JSON", report_json)
    monkeypatch.setattr(ownership, "HUMAN_REPORT_MARKDOWN", report_md)
    monkeypatch.setattr(
        ownership,
        "changed_name_status",
        lambda *_args, **_kwargs: [
            ("M", ".ai/cockpit/task_report.json"),
            ("M", ".ai/cockpit/task_report.md"),
        ],
    )
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})

    values = ownership.preview(contract={"workItemId": "example", "baselineDirtyPaths": []})

    assert [item.state for item in values] == ["active_owned", "active_owned"]

    report_md.write_text("tampered\n", encoding="utf-8")
    values = ownership.preview(contract={"workItemId": "example", "baselineDirtyPaths": []})
    assert [item.state for item in values] == ["unowned", "unowned"]

    # A valid report for a different active Outcome is not an ownership
    # substitute for this Work Item's exact current Outcome.
    other = json.loads(json.dumps(source))
    other["workItemId"] = "other"
    other["bindings"]["taskId"] = "other"
    cross_task_report = human.generate_human_report(other)
    report_json.write_text(json.dumps(cross_task_report), encoding="utf-8")
    report_md.write_text(human.render_human_report(cross_task_report), encoding="utf-8")
    values = ownership.preview(contract={"workItemId": "example", "baselineDirtyPaths": []})
    assert [item.state for item in values] == ["unowned", "unowned"]

    report_md.unlink()
    values = ownership.preview(contract={"workItemId": "example", "baselineDirtyPaths": []})
    assert [item.state for item in values] == ["unowned", "unowned"]


def test_pr_preview_uses_only_archive_pairs_from_the_pr(monkeypatch):
    pr_owner = ownership.Owner(
        "archived", "in-pr", contract(["docs/**"]), {"changedFiles": [{"path": "docs/guide.md"}]}
    )
    historical_overlap = ownership.Owner(
        "archived", "old", contract(["docs/**"]), {"changedFiles": [{"path": "docs/guide.md"}]}
    )
    monkeypatch.setattr(
        ownership, "changed_name_status", lambda *_args, **_kwargs: [("M", "docs/guide.md")]
    )
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})
    monkeypatch.setattr(
        ownership,
        "owners",
        lambda **kwargs: [pr_owner] if kwargs["base"] else [pr_owner, historical_overlap],
    )

    assert ownership.preview(base="merge-base")[0].state == "archived_owned"
    assert (
        ownership.preview(contract={"baseCommit": "merge-base", "baselineDirtyPaths": []})[0].state
        == "archived_owned"
    )
    assert ownership.preview(contract={"baselineDirtyPaths": []})[0].state == "ambiguous"


def test_pr_preview_owns_only_a_complete_current_archive_transaction(monkeypatch, tmp_path):
    task = "exact"
    archive = f".ai/work-items/archive/2026/{task}"
    paths = {
        ".ai/work-items/archive/index.json",
        f".ai/work-items/starts/{task}.json",
        f"{archive}.archive-manifest.json",
        f"{archive}.contract.json",
        f"{archive}.summary.json",
        "docs/owned.md",
    }
    changed_paths = set(paths)
    contract_path = tmp_path / f"{archive}.contract.json"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps({"contractVersion": 2, "workItemId": task}), encoding="utf-8"
    )
    summary_path = tmp_path / f"{archive}.summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "summaryVersion": 2,
                "workItemId": task,
                "changedFiles": [{"path": path, "reason": "fixture"} for path in paths],
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / f"{archive}.archive-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "format": "ai-cockpit-archive-manifest",
                "manifestVersion": 1,
                "workItemId": task,
                "contractPath": f"{archive}.contract.json",
                "summaryPath": f"{archive}.summary.json",
                "contractSha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
                "summarySha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(status_consistency, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ownership, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        ownership,
        "changed_name_status",
        lambda *_args, **_kwargs: [("A", path) for path in changed_paths],
    )
    monkeypatch.setattr(ownership, "archive_evidence_changes", lambda _base: {})
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})

    values = ownership.preview(base="merge-base")

    assert {item.path for item in values} == changed_paths
    assert {item.state for item in values} == {"archived_owned"}

    paths.remove("docs/owned.md")
    summary_path.write_text(
        json.dumps(
            {
                "summaryVersion": 2,
                "workItemId": task,
                "changedFiles": [{"path": path, "reason": "fixture"} for path in paths],
            }
        ),
        encoding="utf-8",
    )
    values = ownership.preview(base="merge-base")
    assert any(item.path == "docs/owned.md" and item.state == "unowned" for item in values)


def test_pr_preview_coalesces_multiple_effective_archive_owners(monkeypatch):
    first = ownership.Owner(
        "archived", "first", contract(["docs/**"]), {"changedFiles": [{"path": "docs/guide.md"}]}
    )
    second = ownership.Owner(
        "archived", "second", contract(["docs/**"]), {"changedFiles": [{"path": "docs/guide.md"}]}
    )
    monkeypatch.setattr(
        ownership, "changed_name_status", lambda *_args, **_kwargs: [("M", "docs/guide.md")]
    )
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [first, second])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})
    item = ownership.preview(base="merge-base")[0]
    assert item.state == "archived_owned"
    assert "latest archive pair wins" in item.detail


def test_pr_archive_owner_candidates_are_ranked_by_history(monkeypatch, tmp_path):
    first = tmp_path / ".ai" / "work-items" / "archive" / "2026" / "first.contract.json"
    second = tmp_path / ".ai" / "work-items" / "archive" / "2026" / "second.contract.json"

    def fake_load_pair(contract_path, kind):
        name = contract_path.name.removesuffix(".contract.json")
        return ownership.Owner(
            kind, name, contract(["docs/**"]), {"changedFiles": [{"path": "docs/guide.md"}]}
        )

    monkeypatch.setattr(
        "ai_check_pr.archived_contract_paths",
        lambda _base: [first, second],
    )
    monkeypatch.setattr(ownership, "load_pair", fake_load_pair)
    monkeypatch.setattr(
        ownership,
        "archive_pair_rank",
        lambda contract_path, _summary_path: 20 if contract_path == first else 10,
    )

    ordered = ownership.owners(base="merge-base")
    assert [owner.work_item_id for owner in ordered] == ["second", "first"]


def test_pr_preview_reports_archive_audit_paths_as_append_only(monkeypatch):
    active = ownership.Owner("active", "task", contract(["docs/**"]), None)
    changed = [
        ("M", ".ai/work-items/archive/2026/task.contract.json"),
        ("M", ".ai/work-items/archive/2026/task.summary.json"),
        ("M", "docs/guide.md"),
    ]
    monkeypatch.setattr(ownership, "changed_name_status", lambda *_args, **_kwargs: changed)
    monkeypatch.setattr(
        ownership,
        "archive_evidence_changes",
        lambda _base: {
            ".ai/work-items/archive/2026/task.contract.json": "A",
            ".ai/work-items/archive/2026/task.summary.json": "A",
        },
    )
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [active])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})

    items = ownership.preview(base="merge-base")
    assert [item.path for item in items] == [
        ".ai/work-items/archive/2026/task.contract.json",
        ".ai/work-items/archive/2026/task.summary.json",
        "docs/guide.md",
    ]
    assert [item.state for item in items] == ["unowned", "unowned", "active_owned"]
    assert "append-only" in items[0].detail


def test_pr_preview_skips_clean_no_op_archive_restore(monkeypatch):
    active = ownership.Owner("active", "task", contract(["docs/**"]), None)
    restored = ".ai/work-items/archive/2026/task.summary.json"
    changed = [("M", restored), ("M", "docs/guide.md")]
    monkeypatch.setattr(ownership, "changed_name_status", lambda *_args, **_kwargs: changed)
    monkeypatch.setattr(ownership, "archive_evidence_changes", lambda _base: {})
    monkeypatch.setattr(ownership, "_is_no_op_restore", lambda _base, path: path == restored)
    monkeypatch.setattr(ownership, "owners", lambda **_kwargs: [active])
    monkeypatch.setattr(ownership, "parse_simple_manifest", lambda _path: {})

    items = ownership.preview(base="merge-base")

    assert [item.path for item in items] == ["docs/guide.md"]
    assert items[0].state == "active_owned"


def test_document_effect_rejects_runtime_code_diff():
    owner = ownership.Owner("active", "task", contract(["scripts/**"]), None)
    result = ownership.classify(
        "scripts/runtime.py",
        [owner],
        {},
        contract={"requestedOperation": {"effect": "document"}},
    )
    assert result.state == "out_of_scope"
    assert "runtime code" in result.detail
