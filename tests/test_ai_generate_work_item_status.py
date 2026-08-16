import json
from pathlib import Path

import scripts.ai_generate_work_item_status as status


def contract(task: str = "wi-a") -> dict:
    return {
        "contractVersion": 2,
        "workItemId": task,
        "mode": "code",
        "baseCommit": "a" * 40,
        "executionDecision": {"status": "continue"},
        "agentCapability": {"needsHumanDecision": False},
        "verification": [{"check": "quality", "required": True}],
        "intent": {
            "problem": "status is not machine-readable",
            "constraints": ["local"],
            "rationale": "safe queries",
        },
        "acceptance": ["A schema-validated status is emitted for each active Work Item."],
        "unknowns": [],
        "riskAssessment": {"level": "low"},
        "guidelines": ["Keep status evidence-derived."],
    }


def summary(task: str = "wi-a", *, commit: str | None = None) -> dict:
    record = {
        "check": "quality",
        "result": "passed",
        "executedAt": "2026-08-16T03:00:00Z",
        "executionContractPath": f".ai/work-items/active/{task}.contract.json",
        "executionSummaryPath": f".ai/work-items/active/{task}.summary.json",
    }
    if commit is not None:
        record["commitSha"] = commit
    return {
        "summaryVersion": 2,
        "workItemId": task,
        "verification": [record],
        "reviewReadiness": {"status": "ready"},
        "guidelinesCompliance": [{"guideline": "Keep status evidence-derived.", "compliant": True}],
        "unknownsRemaining": [],
        "intentAlignment": {
            "problemResolved": True,
            "constraintsRespected": True,
            "nonGoalsAvoided": True,
            "rationaleValidated": True,
        },
        "risk": {"level": "low", "detail": "fixture"},
        "residualRisks": [],
    }


def test_complete_status_projects_required_fields_as_green(tmp_path: Path) -> None:
    value = status.build_status(
        contract(),
        summary(commit="b" * 40),
        branch="codex/wi-a",
        current_commit="b" * 40,
        now="2026-08-16T03:01:00Z",
    )

    assert value["workItem"] == "wi-a"
    assert value["state"] == "green"
    assert value["phase"] == "review"
    assert value["blocking"] is False
    assert value["baseCommit"] == "a" * 40
    assert value["branch"] == "codex/wi-a"
    assert value["lastVerificationAt"] == "2026-08-16T03:00:00Z"
    assert value["evidenceFreshness"]["state"] == "fresh"
    assert value["safeActions"] == ["review_evidence", "refresh_status"]


def test_stale_evidence_never_projects_green(tmp_path: Path) -> None:
    value = status.build_status(
        contract(),
        summary(commit="b" * 40),
        branch="codex/wi-a",
        current_commit="c" * 40,
        now="2026-08-16T03:01:00Z",
    )

    assert value["state"] == "unknown"
    assert value["blocking"] is True
    assert value["evidenceFreshness"]["state"] == "stale"
    assert "stale_verification" in value["diagnostics"]
    assert "refresh_status" in value["safeActions"]


def test_cross_work_item_evidence_is_explicitly_rejected() -> None:
    value = status.build_status(
        contract("wi-a"),
        summary("wi-b", commit="b" * 40),
        branch="codex/wi-a",
        current_commit="b" * 40,
        now="2026-08-16T03:01:00Z",
    )

    assert value["state"] == "unknown"
    assert "cross_work_item_evidence" in value["diagnostics"]
    assert value["humanDecisionRequired"] is False


def test_generate_projects_two_active_items_and_preserves_current_status(tmp_path: Path) -> None:
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    for task in ("wi-a", "wi-b"):
        (active / f"{task}.contract.json").write_text(json.dumps(contract(task)), encoding="utf-8")
        (active / f"{task}.summary.json").write_text(
            json.dumps(summary(task, commit="b" * 40)), encoding="utf-8"
        )
        start_dir = tmp_path / ".ai" / "work-items" / "starts"
        start_dir.mkdir(parents=True, exist_ok=True)
        (start_dir / f"{task}.json").write_text(
            json.dumps({"baseBranch": f"codex/{task}"}), encoding="utf-8"
        )
    current_status = tmp_path / ".ai" / "cockpit" / "current_status.md"
    current_status.parent.mkdir(parents=True)
    current_status.write_text("human-facing status\n", encoding="utf-8")

    index = status.generate(
        root=tmp_path,
        current_commit="b" * 40,
        now="2026-08-16T03:01:00Z",
    )

    assert [item["workItem"] for item in index["items"]] == ["wi-a", "wi-b"]
    assert (tmp_path / ".ai/cockpit/work-items/wi-a.status.json").exists()
    assert current_status.read_text(encoding="utf-8") == "human-facing status\n"


def test_malformed_summary_returns_unknown_status(tmp_path: Path) -> None:
    contract_path = tmp_path / "wi-a.contract.json"
    contract_path.write_text(json.dumps(contract()), encoding="utf-8")
    value = status.project_status(
        contract_path,
        tmp_path / "wi-a.summary.json",
        root=tmp_path,
        current_commit="b" * 40,
        branch="codex/wi-a",
        now="2026-08-16T03:01:00Z",
    )

    assert value["state"] == "unknown"
    assert "malformed_summary" in value["diagnostics"]
