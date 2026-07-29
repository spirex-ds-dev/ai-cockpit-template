import json
from pathlib import Path

import pytest

import ai_checkpoint
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
