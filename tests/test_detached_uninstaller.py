from pathlib import Path

from scripts.ai_detached_uninstaller import execute_proposal
from scripts.ai_install_facts import write_fact_bundle
from scripts.ai_uninstall_facts import collect_uninstall_facts
from scripts.ai_uninstall_proposal import build_proposal


def _installed(tmp_path: Path):
    source = tmp_path / "source"
    root = tmp_path / "adopter"
    for base in (source, root):
        (base / "scripts").mkdir(parents=True)
    for name in ("one.py", "two.py"):
        (source / "scripts" / name).write_text(name, encoding="utf-8")
        (root / "scripts" / name).write_text(name, encoding="utf-8")
    (root / "README.md").write_text("project", encoding="utf-8")
    write_fact_bundle(
        source=source,
        target=root,
        distribution_version={
            "distributionVersion": "test",
            "releaseVersion": "test",
            "contractSchema": 2,
        },
    )
    facts = collect_uninstall_facts(root, "s-1")
    return root, build_proposal(facts)


def test_missing_or_wrong_confirmation_has_zero_runtime_writes(tmp_path):
    root, proposal = _installed(tmp_path)
    before = (root / "scripts/one.py").read_bytes()
    result = execute_proposal(root, proposal, "", detached_execution=True)
    wrong = execute_proposal(
        root,
        proposal,
        "sha256:" + "0" * 64,
        detached_execution=True,
    )
    assert result["state"] == "blocked"
    assert wrong["reason"] == "confirmation_digest_mismatch"
    assert (root / "scripts/one.py").read_bytes() == before


def test_toc_tou_drift_blocks_before_first_deletion(tmp_path):
    root, proposal = _installed(tmp_path)
    (root / "scripts/two.py").write_text("changed", encoding="utf-8")
    result = execute_proposal(
        root,
        proposal,
        proposal["proposalDigest"],
        detached_execution=True,
    )
    assert result["state"] == "blocked"
    assert result["reason"] == "current_facts_mismatch"
    assert (root / "scripts/one.py").is_file()


def test_confirmed_removal_preserves_project_and_evidence_and_verifies_post_state(tmp_path):
    root, proposal = _installed(tmp_path)
    result = execute_proposal(
        root,
        proposal,
        proposal["proposalDigest"],
        detached_execution=True,
    )
    assert result["state"] == "completed"
    assert result["detachedExecution"] is True
    assert result["runtimeRemovalVerified"] is True
    assert result["removed"] == ["scripts/one.py", "scripts/two.py"]
    assert (root / "README.md").read_text(encoding="utf-8") == "project"
    assert (root / ".ai/install/manifest.json").is_file()
    assert (root / proposal["receiptPath"]).is_file()


def test_existing_receipt_blocks_replay(tmp_path):
    root, proposal = _installed(tmp_path)
    receipt = root / proposal["receiptPath"]
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text("{}\n", encoding="utf-8")
    result = execute_proposal(
        root,
        proposal,
        proposal["proposalDigest"],
        detached_execution=True,
    )
    assert result["state"] == "blocked"
    assert result["reason"] == "receipt_already_exists"
    assert (root / "scripts/one.py").is_file()


def test_partial_failure_receipt_reports_actual_state_and_never_claims_success(tmp_path):
    root, proposal = _installed(tmp_path)
    calls = []

    def remove(path):
        calls.append(path.name)
        if path.name == "two.py":
            raise PermissionError("injected")
        path.unlink()

    result = execute_proposal(
        root,
        proposal,
        proposal["proposalDigest"],
        remove_file=remove,
        detached_execution=True,
    )
    assert result["state"] == "partial_failure"
    assert result["runtimeRemovalVerified"] is False
    assert result["removed"] == ["scripts/one.py"]
    assert result["failed"] == [{"path": "scripts/two.py", "error": "PermissionError"}]
    assert "reconcile" in result["recovery"]
    assert (root / proposal["receiptPath"]).is_file()


def test_internal_non_detached_call_cannot_remove_runtime(tmp_path):
    root, proposal = _installed(tmp_path)

    result = execute_proposal(root, proposal, proposal["proposalDigest"])

    assert result == {
        "state": "blocked",
        "reason": "detached_execution_required",
        "writes": [],
    }
    assert (root / "scripts/one.py").is_file()
    assert not (root / proposal["receiptPath"]).exists()


def test_symlinked_receipt_parent_blocks_before_first_deletion(tmp_path):
    root, proposal = _installed(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    receipt_parent = root / ".ai/upgrade/uninstall-evidence"
    receipt_parent.parent.mkdir(parents=True, exist_ok=True)
    receipt_parent.symlink_to(outside, target_is_directory=True)

    result = execute_proposal(
        root,
        proposal,
        proposal["proposalDigest"],
        detached_execution=True,
    )

    assert result == {
        "state": "blocked",
        "reason": "unsafe_receipt_path",
        "writes": [],
    }
    assert (root / "scripts/one.py").is_file()
    assert list(outside.iterdir()) == []
