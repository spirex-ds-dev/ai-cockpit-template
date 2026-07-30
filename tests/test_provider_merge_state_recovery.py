from __future__ import annotations

import copy

import ai_provider_merge_state_recovery as recovery
import pytest


def valid_evidence() -> dict[str, object]:
    return {
        "task": "python-311-compatibility-migration-20260730",
        "pullRequest": {
            "number": 470,
            "url": "https://github.com/example/repo/pull/470",
            "state": "OPEN",
            "headRefName": "codex/python-311-compatibility-migration-20260730",
            "headRefOid": "a" * 40,
            "baseRefName": "main",
            "mergedAt": None,
            "mergeCommit": None,
        },
        "base": {"remote": "origin", "branch": "main", "observedHead": "c" * 40},
        "mergeCommit": {
            "oid": "b" * 40,
            "parents": ["c" * 40, "a" * 40],
            "reachableOnBase": True,
            "githubVerification": {"verified": True, "reason": "valid"},
        },
        "hostedEvidence": {
            "headSha": "a" * 40,
            "requiredJobs": ["template-smoke", "compatibility-gate"],
            "jobs": [
                {"name": "template-smoke", "conclusion": "success"},
                {"name": "compatibility-gate", "conclusion": "success"},
            ],
        },
    }


def test_valid_provider_inconsistency_requires_confirmation_and_renders_truthful_receipt(
    tmp_path,
) -> None:
    evidence = valid_evidence()

    with pytest.raises(recovery.RecoveryEvidenceError, match="explicit human confirmation"):
        recovery.validate_recovery_evidence(evidence, human_confirmed=False)

    result = recovery.validate_recovery_evidence(evidence, human_confirmed=True)
    receipt = recovery.render_recovery_receipt(result)

    assert result.provider_state == "OPEN"
    assert result.merge_commit == "b" * 40
    assert "Provider PR state observed: `OPEN`" in receipt
    assert "Normal mergedAt: `unavailable`" in receipt
    assert "This is not normal PR-merged closure evidence." in receipt


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda item: item["pullRequest"].update({"state": "MERGED"}), "provider state OPEN"),
        (
            lambda item: item["mergeCommit"]["githubVerification"].update({"verified": False}),
            "GitHub-verified",
        ),
        (
            lambda item: item["mergeCommit"].update({"parents": ["a" * 40, "c" * 40]}),
            "parent order",
        ),
        (lambda item: item["mergeCommit"].update({"reachableOnBase": False}), "not reachable"),
        (lambda item: item["hostedEvidence"].update({"headSha": "d" * 40}), "Head SHA"),
        (
            lambda item: item["hostedEvidence"]["jobs"].__setitem__(
                1, {"name": "compatibility-gate", "conclusion": "failure"}
            ),
            "did not succeed",
        ),
        (
            lambda item: item["hostedEvidence"].update(
                {"requiredJobs": ["template-smoke", "missing"]}
            ),
            "missing",
        ),
    ],
)
def test_recovery_rejects_incomplete_or_contradictory_evidence(mutation, message: str) -> None:
    evidence = copy.deepcopy(valid_evidence())
    mutation(evidence)

    with pytest.raises(recovery.RecoveryEvidenceError, match=message):
        recovery.validate_recovery_evidence(evidence, human_confirmed=True)


def test_normal_closure_remains_separate_from_exceptional_recovery() -> None:
    evidence = valid_evidence()
    evidence["pullRequest"]["state"] = "CLOSED"

    with pytest.raises(recovery.RecoveryEvidenceError, match="provider state OPEN"):
        recovery.validate_recovery_evidence(evidence, human_confirmed=True)
