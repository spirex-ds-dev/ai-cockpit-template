import json
from pathlib import Path

import ai_checkpoint
import pytest
from ai_check_diff_ownership import Ownership


def test_intent_context_defaults_when_intent_is_missing():
    assert ai_checkpoint.intent_context({"workItemId": "task"}) == [
        "problem: not provided",
        "constraint: not provided",
        "rationale: not provided",
    ]


def test_intent_context_keeps_values_and_default_placeholders():
    assert ai_checkpoint.intent_context(
        {
            "intent": {
                "problem": "Resolve optional intent compatibility.",
                "constraints": ["Keep V2 backward compatible."],
            }
        }
    ) == [
        "problem: Resolve optional intent compatibility.",
        "constraint: Keep V2 backward compatible.",
        "rationale: not provided",
    ]


def test_checkpoint_ownership_preview_keeps_unresolved_state_visible():
    rendered = ai_checkpoint.format_preview(
        [
            Ownership("docs/guide.md", "unowned", [], "no archive evidence"),
        ]
    )
    assert "[unowned] `docs/guide.md`" in "\n".join(rendered)


def _checkpoint_contract(*, resume_times: list[str] | None = None) -> dict:
    contract = {
        "verification": [
            {"check": "aiWorkItem", "required": True},
            {"check": "aiScope", "required": True},
        ],
        "acceptance": ["Use only current-generation evidence."],
        "unknowns": [],
    }
    if resume_times is not None:
        contract["resumeHistory"] = [{"recordedAt": recorded_at} for recorded_at in resume_times]
    return contract


def _record_before_edit(tmp_path: Path, contract: dict, verification: list[dict]) -> dict:
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary = {"verification": verification, "checkpointEvidence": []}
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    ai_checkpoint.record_checkpoint(summary, contract, "before_edit", contract_path, summary_path)

    return json.loads(summary_path.read_text(encoding="utf-8"))["checkpointEvidence"][0]


def test_before_edit_ignores_verification_from_before_latest_resume(tmp_path):
    record = _record_before_edit(
        tmp_path,
        _checkpoint_contract(resume_times=["2026-07-29T07:30:00+00:00"]),
        [
            {
                "check": "aiWorkItem",
                "result": "passed",
                "executedAt": "2026-07-29T07:00:00+00:00",
            },
            {
                "check": "aiScope",
                "result": "failed",
                "executedAt": "2026-07-29T07:01:00+00:00",
            },
        ],
    )

    assert record["requiredChecksPassed"] == 0


def test_before_edit_ignores_verification_started_after_latest_resume(tmp_path):
    record = _record_before_edit(
        tmp_path,
        _checkpoint_contract(resume_times=["2026-07-29T07:30:00+00:00"]),
        [
            {
                "check": "aiWorkItem",
                "result": "passed",
                "executedAt": "2026-07-29T07:31:00+00:00",
            }
        ],
    )

    assert record["requiredChecksPassed"] == 0


def test_checkpoint_uses_only_latest_resume_transition(tmp_path):
    record = _record_before_edit(
        tmp_path,
        _checkpoint_contract(
            resume_times=[
                "2026-07-29T07:30:00+00:00",
                "2026-07-29T08:00:00+00:00",
            ]
        ),
        [
            {
                "check": "aiWorkItem",
                "result": "passed",
                "executedAt": "2026-07-29T07:45:00+00:00",
            },
            {
                "check": "aiScope",
                "result": "passed",
                "executedAt": "2026-07-29T08:01:00+00:00",
            },
        ],
    )

    assert record["requiredChecksPassed"] == 0


def test_checkpoint_rejects_invalid_latest_resume_timestamp(tmp_path):
    with pytest.raises(ValueError, match="latest resumeHistory.recordedAt is invalid"):
        _record_before_edit(
            tmp_path,
            _checkpoint_contract(resume_times=["not-a-timestamp"]),
            [
                {
                    "check": "aiWorkItem",
                    "result": "passed",
                    "executedAt": "2026-07-29T08:01:00+00:00",
                }
            ],
        )


def test_before_edit_never_inherits_existing_verification_without_resume_history(tmp_path):
    record = _record_before_edit(
        tmp_path,
        _checkpoint_contract(),
        [{"check": "aiWorkItem", "result": "passed"}],
    )

    assert record["requiredChecksPassed"] == 0


def test_before_edit_checkpoint_is_immutable_after_implementation_preparation(tmp_path):
    """Break caught: rerunning preparation silently replaces phase-boundary evidence."""
    contract = _checkpoint_contract()
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary = {"verification": [], "checkpointEvidence": []}
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    ai_checkpoint.record_checkpoint(summary, contract, "before_edit", contract_path, summary_path)
    original = summary_path.read_bytes()

    with pytest.raises(
        ValueError, match="before_edit.*already exists.*revalidate-contract-amendment"
    ):
        ai_checkpoint.record_checkpoint(
            summary, contract, "before_edit", contract_path, summary_path
        )

    assert summary_path.read_bytes() == original


def test_duplicate_before_edit_is_rejected_without_replacing_original_evidence(tmp_path):
    """A changed Contract cannot replace the original phase-boundary record."""
    contract = _checkpoint_contract()
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    first = {
        "stage": "before_edit",
        "recorded": True,
        "contractHash": ai_checkpoint.contract_hash(contract_path),
        "acceptanceCount": len(contract["acceptance"]),
        "unknownCount": 0,
        "requiredChecks": 2,
        "requiredChecksPassed": 0,
    }
    summary = {"verification": [], "checkpointEvidence": [first]}
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    contract["acceptance"].append("Keep the initial evidence immutable.")
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(
        ValueError, match="before_edit.*already exists.*revalidate-contract-amendment"
    ):
        ai_checkpoint.record_checkpoint(
            summary, contract, "before_edit", contract_path, summary_path
        )

    assert json.loads(summary_path.read_text(encoding="utf-8"))["checkpointEvidence"] == [first]


def test_contract_amendment_revalidation_appends_without_replacing_before_edit(tmp_path):
    """Break caught: an amended Contract replaces the original authorization-to-edit proof."""
    contract = _checkpoint_contract()
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary = {
        "verification": [],
        "checkpointEvidence": [
            {
                "stage": "before_edit",
                "recorded": True,
                "contractHash": "original-contract-hash",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": 2,
                "requiredChecksPassed": 0,
            }
        ],
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    record = ai_checkpoint.record_contract_amendment_revalidation(
        summary,
        contract,
        contract_path,
        summary_path,
        previous_contract_hash="original-contract-hash",
        reason="Expand scope to include the required regression.",
    )

    persisted = json.loads(summary_path.read_text(encoding="utf-8"))["checkpointEvidence"]
    assert persisted[0] == summary["checkpointEvidence"][0]
    assert [item["stage"] for item in persisted] == [
        "before_edit",
        "contract_amendment_revalidation",
    ]
    assert record["originalBeforeEditContractHash"] == "original-contract-hash"
    assert record["previousContractHash"] == "original-contract-hash"
    assert record["verificationStarted"] is False


def test_contract_amendment_after_verification_invalidates_every_required_gate(tmp_path):
    """Break caught: a post-verification amendment retains an old green gate."""
    contract = _checkpoint_contract()
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary = {
        "verification": [{"check": "aiWorkItem", "result": "passed"}],
        "checkpointEvidence": [
            {
                "stage": "before_edit",
                "recorded": True,
                "contractHash": "original-contract-hash",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": 2,
                "requiredChecksPassed": 0,
            }
        ],
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    record = ai_checkpoint.record_contract_amendment_revalidation(
        summary,
        contract,
        contract_path,
        summary_path,
        previous_contract_hash="original-contract-hash",
        reason="Add the regression exposed by full verification.",
    )

    assert record["verificationStarted"] is True
    assert record["invalidatedRequiredChecks"] == ["aiWorkItem", "aiScope"]
    assert record["requiredChecksPassedAtAmendment"] == 1


def test_contract_amendment_revalidation_binds_the_immediately_preceding_amendment(tmp_path):
    """Break caught: a second governed amendment can only name before_edit, not its predecessor."""
    contract = _checkpoint_contract()
    contract_path = tmp_path / "contract.json"
    summary_path = tmp_path / "summary.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    summary = {
        "verification": [],
        "checkpointEvidence": [
            {
                "stage": "before_edit",
                "recorded": True,
                "contractHash": "original-contract-hash",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": 2,
                "requiredChecksPassed": 0,
            },
            {
                "stage": "contract_amendment_revalidation",
                "recorded": True,
                "originalBeforeEditContractHash": "original-contract-hash",
                "previousContractHash": "original-contract-hash",
                "contractHash": "first-amendment-hash",
                "acceptanceCount": 1,
                "unknownCount": 0,
                "requiredChecks": 2,
                "requiredChecksPassed": 0,
                "reason": "First governed amendment.",
                "verificationStarted": False,
            },
        ],
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    record = ai_checkpoint.record_contract_amendment_revalidation(
        summary,
        contract,
        contract_path,
        summary_path,
        previous_contract_hash="first-amendment-hash",
        reason="Second governed amendment.",
    )

    assert record["originalBeforeEditContractHash"] == "original-contract-hash"
    assert record["previousContractHash"] == "first-amendment-hash"
