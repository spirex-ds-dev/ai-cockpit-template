"""RED contracts for the converged lifecycle truth core (#677)."""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

from ai_common import simple_yaml_lists


def _runtime():
    """Load the new single-source runtime; absence is the intentional RED state."""
    spec = importlib.util.find_spec("ai_lifecycle_truth")
    assert spec is not None, "#677 must provide the ai_lifecycle_truth runtime"
    return importlib.import_module("ai_lifecycle_truth")


def _identity(task: str = "lifecycle-truth-core-677") -> dict[str, str]:
    return {
        "workItemId": task,
        "branch": f"codex/{task}",
        "baseCommit": "b" * 40,
        "contractDigest": "c" * 64,
        "summaryDigest": "d" * 64,
        "candidateDigest": "e" * 64,
    }


def test_early_finish_failures_persist_red_outcome_and_keep_archive_closed(tmp_path: Path) -> None:
    runtime = _runtime()

    for gate in ("aiWorkItem", "aiPreflight", "aiCheckpoint"):
        result = runtime.finish_failure(
            root=tmp_path / gate,
            identity=_identity(),
            failedGate=gate,
            message=f"{gate} rejected the Work Item",
            archiveRequested=True,
        )
        assert result.exitCode != 0
        assert result.archivePermitted is False
        assert result.outcome["status"] == "blocked"
        assert result.outcome["humanStatusColor"] == "red"
        assert result.outcome["failedGate"] == gate
        assert result.outcome["recoveryCondition"]
        assert result.outcomePath.is_file()


def test_before_edit_is_immutable_and_pre_quality_amendment_is_append_only(tmp_path: Path) -> None:
    runtime = _runtime()
    contract = tmp_path / "task.contract.json"
    summary = tmp_path / "task.summary.json"
    contract.write_text(json.dumps({"scope": ["scripts/**"]}), encoding="utf-8")
    baseline = runtime.record_before_edit(contract=contract, summary=summary, identity=_identity())

    contract.write_text(json.dumps({"scope": ["scripts/**", "tests/**"]}), encoding="utf-8")
    amendment = runtime.revalidate_contract(
        contract=contract,
        summary=summary,
        reason="full lifecycle regression needs a test boundary",
    )
    persisted = json.loads(summary.read_text(encoding="utf-8"))
    assert persisted["beforeEdit"] == baseline
    assert persisted["contractAmendments"] == [amendment]

    duplicate = runtime.record_before_edit(contract=contract, summary=summary, identity=_identity())
    assert duplicate.accepted is False
    assert duplicate.reason == "before_edit_immutable"


def test_source_bound_quality_attempt_locks_amendment_even_when_summary_claims_not_run(
    tmp_path: Path,
) -> None:
    runtime = _runtime()
    identity = _identity()
    for result in ("passed", "failed"):
        receipt = runtime.record_quality_attempt(
            root=tmp_path / result,
            identity=identity,
            result=result,
            command=["make", "quality"],
            output=f"quality {result}",
        )
        decision = runtime.quality_attempt_state(
            receipt=receipt,
            identity=identity,
            summary={"verification": [{"check": "quality", "result": "not_run"}]},
        )
        assert decision.sourceBound is True
        assert decision.result == result
        assert decision.verificationStarted is True
        assert decision.summarySpoofed is False
        assert runtime.can_amend_contract(decision) is False


def test_same_active_scope_evidence_correction_retries_in_place_and_keeps_blocked_outcome(
    tmp_path: Path,
) -> None:
    runtime = _runtime()
    blocked = runtime.finish_failure(
        root=tmp_path,
        identity=_identity(),
        failedGate="aiCheckpoint",
        message="missing before_finish checkpoint",
        archiveRequested=False,
    )

    decision = runtime.retry_or_successor_decision(
        sameActiveContract=True,
        sameScope=True,
        baseChanged=False,
        immutableDelivery=False,
    )

    assert decision.action == "retry_in_place"
    assert decision.successorRequired is False
    assert json.loads(blocked.outcomePath.read_text(encoding="utf-8"))["status"] == "blocked"


def test_changed_base_invalidated_scope_or_immutable_delivery_requires_successor():
    runtime = _runtime()

    for facts in (
        {
            "sameActiveContract": True,
            "sameScope": True,
            "baseChanged": True,
            "immutableDelivery": False,
        },
        {
            "sameActiveContract": True,
            "sameScope": False,
            "baseChanged": False,
            "immutableDelivery": False,
        },
        {
            "sameActiveContract": False,
            "sameScope": True,
            "baseChanged": False,
            "immutableDelivery": False,
        },
        {
            "sameActiveContract": True,
            "sameScope": True,
            "baseChanged": False,
            "immutableDelivery": True,
        },
    ):
        decision = runtime.retry_or_successor_decision(**facts)

        assert decision.action == "governed_successor_or_quarantine"
        assert decision.successorRequired is True
        assert decision.reason


def test_only_a_bound_blocked_predecessor_can_be_quarantined_or_superseded_for_its_successor(
    tmp_path: Path,
) -> None:
    runtime = _runtime()
    predecessor = _identity("blocked-predecessor")
    blocked = runtime.finish_failure(
        root=tmp_path / "predecessor",
        identity=predecessor,
        failedGate="quality",
        message="quality failed",
        archiveRequested=False,
    )
    transition = runtime.transition_to_successor(
        predecessorOutcome=blocked.outcomePath,
        predecessor=predecessor,
        successor=_identity("exact-successor"),
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/677",
        authority="user-authorized-convergence",
        mode="quarantined",
        reason="current-main integrated repair",
    )
    assert transition.accepted is True
    assert transition.receipt["predecessorOutcomeDigest"]
    assert transition.receipt["successorWorkItemId"] == "exact-successor"
    assert json.loads(blocked.outcomePath.read_text(encoding="utf-8"))["status"] == "blocked"

    foreign = runtime.transition_to_successor(
        predecessorOutcome=blocked.outcomePath,
        predecessor=predecessor,
        successor=_identity("unrelated-successor"),
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/999",
        authority="",
        mode="superseded",
        reason="unbound transition",
    )
    assert foreign.accepted is False
    assert foreign.reason in {"missing_authority", "foreign_issue", "unbound_successor"}


def test_public_transition_cli_writes_only_a_bound_receipt_and_rejects_foreign_issue(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    runtime = _runtime()
    predecessor = _identity("blocked-predecessor")
    outcome = runtime.finish_failure(
        root=tmp_path,
        identity=predecessor,
        failedGate="quality",
        message="quality failed",
        archiveRequested=False,
    ).outcomePath
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai_lifecycle_truth.py",
            "--transition-to-successor",
            "--root",
            str(tmp_path),
            "--predecessor-task",
            "blocked-predecessor",
            "--successor-task",
            "corrective-704",
            "--successor-branch",
            "codex/corrective-704",
            "--successor-base",
            "a" * 40,
            "--issue",
            "https://github.com/spirex-ds-dev/ai-cockpit-template/issues/682",
            "--authority",
            "RayIori",
            "--mode",
            "quarantined",
            "--reason",
            "corrective route",
        ],
    )
    assert runtime.main() == 0
    receipt = outcome.with_name("blocked-predecessor.successor-receipt.json")
    assert receipt.is_file()
    assert json.loads(receipt.read_text(encoding="utf-8"))["predecessorOutcomeDigest"]
    assert json.loads(outcome.read_text(encoding="utf-8"))["status"] == "blocked"

    receipt.unlink()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai_lifecycle_truth.py",
            "--transition-to-successor",
            "--root",
            str(tmp_path),
            "--predecessor-task",
            "blocked-predecessor",
            "--successor-task",
            "corrective-704",
            "--successor-branch",
            "codex/corrective-704",
            "--successor-base",
            "a" * 40,
            "--issue",
            "https://example.invalid/issues/682",
            "--authority",
            "RayIori",
            "--mode",
            "quarantined",
            "--reason",
            "foreign",
        ],
    )
    assert runtime.main() == 1
    assert not receipt.exists()
    assert "foreign_issue" in capsys.readouterr().err


def test_transition_rejects_unbound_successors_and_receipt_tampering_before_writing(
    tmp_path: Path,
) -> None:
    runtime = _runtime()
    predecessor = _identity("blocked-predecessor")
    outcome = runtime.finish_failure(
        root=tmp_path,
        identity=predecessor,
        failedGate="quality",
        message="quality failed",
        archiveRequested=False,
    ).outcomePath
    invalid = runtime.transition_to_successor(
        predecessorOutcome=outcome,
        predecessor={"workItemId": "blocked-predecessor"},
        successor={"workItemId": "corrective-704", "branch": "other", "baseCommit": "a" * 40},
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/682/extra",
        authority="RayIori",
        mode="quarantined",
        reason="corrective route",
    )
    assert invalid.accepted is False
    assert invalid.reason == "foreign_issue"
    assert not outcome.with_name("blocked-predecessor.successor-receipt.json").exists()

    accepted = runtime.transition_to_successor(
        predecessorOutcome=outcome,
        predecessor={"workItemId": "blocked-predecessor"},
        successor={
            "workItemId": "corrective-704",
            "branch": "codex/corrective-704",
            "baseCommit": "a" * 40,
        },
        issue="https://github.com/spirex-ds-dev/ai-cockpit-template/issues/682",
        authority="RayIori",
        mode="quarantined",
        reason="corrective route",
    )
    assert accepted.accepted is True
    receipt = dict(accepted.receipt)
    receipt["predecessorOutcomeDigest"] = "0" * 64
    assert (
        runtime.validate_successor_receipt(
            predecessor_outcome=outcome,
            predecessor_work_item_id="blocked-predecessor",
            receipt=receipt,
        )
        == "outcome_digest_mismatch"
    )


def test_installer_catalog_template_and_isolated_adopter_require_full_lifecycle_runtime(
    tmp_path: Path,
) -> None:
    runtime = _runtime()
    source = Path(__file__).resolve().parents[1]
    catalog = json.loads(
        (source / "scripts" / "ai_installer_catalog.json").read_text(encoding="utf-8")
    )
    complete = runtime.installer_parity(
        source=source, catalog=catalog, adopter=tmp_path / "adopter"
    )
    assert complete.ready is True
    assert complete.missing == []

    incomplete = runtime.installer_parity(
        source=source, catalog={"scripts": []}, adopter=tmp_path / "missing"
    )
    assert incomplete.ready is False
    assert incomplete.reason == "missing_catalog_runtime"


def test_status_doctor_and_outcome_share_one_traffic_light_diagnostic_model(tmp_path: Path) -> None:
    runtime = _runtime()
    outcome = runtime.finish_failure(
        root=tmp_path,
        identity=_identity(),
        failedGate="aiPreflight",
        message="preflight evidence is stale",
        archiveRequested=True,
    ).outcome
    projections = runtime.project_lifecycle_truth(outcome=outcome, languages=("en", "ja"))
    assert projections.status["humanStatusColor"] == "red"
    assert projections.doctor["failedGate"] == "aiPreflight"
    assert projections.status["recoveryCondition"] == outcome["recoveryCondition"]
    assert projections.japanese["humanStatusColor"] == "red"
    assert projections.japanese["failedGate"] == "aiPreflight"


def test_lifecycle_truth_runtime_has_a_declared_coverage_guard_association() -> None:
    policy = simple_yaml_lists(
        Path(__file__).resolve().parents[1] / ".ai/guards/coverage_policy.yaml"
    )

    assert policy["associations.lifecycleTruthCore.production"] == ["scripts/ai_lifecycle_truth.py"]
    assert policy["associations.lifecycleTruthCore.tests"] == [
        "tests/test_lifecycle_truth_core_677.py",
        "tests/test_ai_archive_work_item.py",
        "tests/test_work_item_lifecycle_closure.py",
    ]
