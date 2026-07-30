from pathlib import Path

import ai_finish


def summary(*, verification="passed", unknowns=None, residual_risks=None):
    return {
        "verification": [
            {"check": "quality", "result": verification},
        ],
        "unknownsRemaining": [] if unknowns is None else unknowns,
        "residualRisks": [] if residual_risks is None else residual_risks,
        "reviewReadiness": {
            "status": "not_ready",
            "reason": "Initial skeleton.",
            "expectedReviewFocus": ["review"],
        },
    }


def test_promote_review_readiness_marks_fully_verified_summary_ready():
    result = ai_finish.promote_review_readiness(summary())

    assert result["status"] == "ready"
    assert "required verification" in result["reason"]
    assert result["expectedReviewFocus"] == ["review"]


def test_promote_review_readiness_preserves_residual_risk_signal():
    result = ai_finish.promote_review_readiness(
        summary(residual_risks=[{"level": "medium", "area": "review", "detail": "focus"}])
    )

    assert result["status"] == "ready_with_risks"
    assert "residual risk" in result["reason"]


def test_promote_review_readiness_remains_not_ready_for_incomplete_evidence():
    failed = ai_finish.promote_review_readiness(summary(verification="failed"))
    unknown = ai_finish.promote_review_readiness(summary(unknowns=["external review"]))

    assert failed["status"] == "not_ready"
    assert unknown["status"] == "not_ready"


def test_promote_review_readiness_allows_only_contract_optional_not_run_checks():
    candidate = summary()
    candidate["verification"] = [
        {"check": "scope", "result": "passed"},
        {"check": "quality", "result": "not_run"},
    ]
    contract = {
        "contractVersion": 2,
        "acceptance": ["Optional verification is declared in the Contract."],
        "verification": [
            {"check": "scope", "required": True},
            {"check": "quality", "required": False},
        ],
    }

    result = ai_finish.promote_review_readiness(candidate, contract)

    assert result["status"] == "ready"


def test_promote_review_readiness_requires_acceptance_evidence_for_v2():
    result = ai_finish.promote_review_readiness(
        summary(),
        {
            "contractVersion": 2,
            "acceptance": ["A1: behavior is mapped"],
            "riskAssessment": {"level": "low"},
        },
    )

    assert result["status"] == "not_ready"
    assert "Acceptance evidence" in result["reason"]


def test_finish_archive_message_is_not_lifecycle_closure():
    output = ai_finish.archive_next_steps("example")

    assert "lifecycle is not closed" in output
    assert "make ai-close-work-item TASK=example" in output


def test_source_bound_evidence_gate_is_fail_closed_before_finish(monkeypatch, tmp_path):
    summary_path = tmp_path / "summary.json"
    summary_path.write_text("{}", encoding="utf-8")
    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        return 1, 1, "source-bound evidence is stale"

    monkeypatch.setattr(ai_finish, "run", fake_run)
    code = ai_finish.run_mandatory_evidence_checks(
        contract="contract.json",
        summary="summary.json",
        contract_data={"scope": []},
        contract_path=Path("contract.json"),
        summary_path=summary_path,
        contract_hash="a" * 64,
        commit_sha="b" * 40,
        obs=type(
            "Observation",
            (),
            {
                "check_started": lambda *_a, **_k: None,
                "check_failed": lambda *_a, **_k: None,
                "check_passed": lambda *_a, **_k: None,
            },
        )(),
    )

    assert code == 1
    assert calls == [["make", "check-source-bound-evidence"]]
    assert ai_finish.load_json(summary_path)["verification"][0]["check"] == "sourceBoundEvidence"
    assert ai_finish.load_json(summary_path)["verification"][0]["result"] == "failed"


def test_promote_review_readiness_does_not_override_failed_stabilization_evidence():
    result = ai_finish.promote_review_readiness(
        summary(verification="failed"),
        {"contractVersion": 2, "acceptance": []},
    )

    assert result["status"] == "not_ready"
