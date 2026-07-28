import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts import ai_prepare_hosted_verification as hosted


TASK = "performance-task"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def fixture_repository(tmp_path: Path, *, branch: str = "codex/performance") -> tuple[Path, Path]:
    root = tmp_path / "repository"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    (root / ".gitignore").write_text("target/\n", encoding="utf-8")
    (root / "README.md").write_text("baseline\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "baseline")
    base = git(root, "rev-parse", "HEAD")
    if branch != "main":
        git(root, "switch", "-qc", branch)
    contract_path = root / ".ai" / "work-items" / "active" / f"{TASK}.contract.json"
    summary_path = root / ".ai" / "work-items" / "active" / f"{TASK}.summary.json"
    write_json(
        contract_path,
        {
            "contractVersion": 2,
            "workItemId": TASK,
            "mode": "code",
            "baseCommit": base,
            "acceptance": ["Collect at least three comparable hosted quality runs before Finish."],
            "riskAssessment": {
                "level": "medium",
                "riskTypes": ["performance_evidence"],
                "unknownsReviewComplete": True,
            },
            "requestedOperation": {
                "target": "repository_governance",
                "action": "modify",
                "environment": "repository",
                "effect": "enforce",
                "authorityRequired": False,
            },
        },
    )
    write_json(
        summary_path,
        {
            "summaryVersion": 2,
            "workItemId": TASK,
            "hostedPerformanceEvidence": {
                "schemaVersion": 1,
                "baselineWorkItem": "baseline",
                "comparisonRule": "Use like-for-like hosted runs.",
                "status": "partial",
                "scenarios": [
                    {
                        "scenario": "pull_request_quality_gate",
                        "status": "not_run",
                        "reason": "The committed snapshot has not run in hosted CI.",
                        "evidence": [],
                    }
                ],
            },
        },
    )
    (root / "implementation.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "snapshot")
    return root, contract_path


def passing_quality(_root: Path) -> dict[str, str]:
    return {
        "sessionId": "commit-run-attempt",
        "decision": "PASS",
        "summaryDigest": "sha256:" + "a" * 64,
    }


def test_active_summary_path_rejects_a_non_contract_filename(tmp_path):
    with pytest.raises(hosted.HostedVerificationError, match="must end with .contract.json"):
        hosted.active_summary_path(tmp_path / "not-a-contract.json")


def test_prepare_snapshot_binds_evidence_without_mutating_governed_state(tmp_path):
    root, contract_path = fixture_repository(tmp_path)
    summary_path = Path(str(contract_path).replace(".contract.json", ".summary.json"))
    output = root / "target" / "hosted-verification.json"
    refs_before = git(root, "show-ref")
    contract_before = contract_path.read_bytes()
    summary_before = summary_path.read_bytes()

    receipt = hosted.prepare_snapshot(
        root=root,
        contract_path=contract_path,
        output=output,
        quality_runner=passing_quality,
    )

    assert receipt["schemaVersion"] == 1
    assert receipt["workItemId"] == TASK
    assert receipt["branch"] == "codex/performance"
    assert receipt["commitSha"] == git(root, "rev-parse", "HEAD")
    assert receipt["treeSha"] == git(root, "rev-parse", "HEAD^{tree}")
    assert receipt["contractDigest"] == hashlib.sha256(contract_before).hexdigest()
    assert receipt["summaryDigest"] == hashlib.sha256(summary_before).hexdigest()
    assert receipt["quality"]["decision"] == "PASS"
    assert receipt["onlyEligibleNextAction"] == "push_this_branch_for_hosted_verification_only"
    assert receipt["authorizationClaim"] == "not_provided_by_receipt"
    assert "pull_request" in receipt["forbiddenActions"]
    assert json.loads(output.read_text(encoding="utf-8")) == receipt
    assert git(root, "show-ref") == refs_before
    assert contract_path.read_bytes() == contract_before
    assert summary_path.read_bytes() == summary_before
    assert git(root, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("dirty", "worktree must be clean"),
        ("base", "dedicated non-base branch"),
        ("detached", "detached HEAD"),
        ("archived", "already archived"),
        ("complete", "hosted evidence is already complete"),
        ("release", "release or publication intent"),
    ],
)
def test_prepare_snapshot_rejects_unsafe_lifecycle_states(tmp_path, mutation, message):
    root, contract_path = fixture_repository(
        tmp_path, branch="main" if mutation == "base" else "codex/performance"
    )
    summary_path = Path(str(contract_path).replace(".contract.json", ".summary.json"))
    if mutation == "dirty":
        (root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    elif mutation == "detached":
        git(root, "switch", "--detach", "-q")
    elif mutation == "archived":
        archived = root / ".ai" / "work-items" / "archive" / "2026" / contract_path.name
        archived.parent.mkdir(parents=True)
        archived.write_text("{}\n", encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "archive")
    elif mutation == "complete":
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["hostedPerformanceEvidence"]["status"] = "complete"
        write_json(summary_path, summary)
        git(root, "add", ".")
        git(root, "commit", "-qm", "complete")
    elif mutation == "release":
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["requestedOperation"]["target"] = "production_release"
        contract["requestedOperation"]["action"] = "publish"
        write_json(contract_path, contract)
        git(root, "add", ".")
        git(root, "commit", "-qm", "release")

    with pytest.raises(hosted.HostedVerificationError, match=message):
        hosted.prepare_snapshot(
            root=root,
            contract_path=contract_path,
            output=root / "target" / "receipt.json",
            quality_runner=passing_quality,
        )
    assert not (root / "target" / "receipt.json").exists()


def test_prepare_snapshot_rejects_failed_quality_and_malformed_hosted_evidence(tmp_path):
    root, contract_path = fixture_repository(tmp_path)
    output = root / "target" / "receipt.json"

    with pytest.raises(hosted.HostedVerificationError, match="local quality did not pass"):
        hosted.prepare_snapshot(
            root=root,
            contract_path=contract_path,
            output=output,
            quality_runner=lambda _root: {
                "sessionId": "failed",
                "decision": "FAIL",
                "summaryDigest": "sha256:" + "b" * 64,
            },
        )
    assert not output.exists()

    summary_path = Path(str(contract_path).replace(".contract.json", ".summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["hostedPerformanceEvidence"]["scenarios"] = []
    write_json(summary_path, summary)
    git(root, "add", ".")
    git(root, "commit", "-qm", "malformed")
    with pytest.raises(hosted.HostedVerificationError, match="pending hosted scenario"):
        hosted.prepare_snapshot(
            root=root,
            contract_path=contract_path,
            output=output,
            quality_runner=passing_quality,
        )


def test_repository_exposes_and_documents_the_narrow_make_target():
    makefile = Path("Makefile").read_text(encoding="utf-8")
    assert "ai-prepare-hosted-verification-snapshot:" in makefile
    assert "scripts/ai_prepare_hosted_verification.py" in makefile
    for path in [
        Path("AGENTS.md"),
        Path(".ai/cockpit/README.md"),
        Path(".ai/cockpit/README.ja.md"),
        Path("docs/reference/repository-workflow.md"),
        Path("docs/reference/ai-cockpit-work-item-lifecycle.md"),
    ]:
        text = path.read_text(encoding="utf-8")
        assert "ai-prepare-hosted-verification-snapshot" in text
        assert "PR" in text
        assert "release" in text
