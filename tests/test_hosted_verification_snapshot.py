import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

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


def test_json_and_git_helpers_fail_closed(tmp_path, monkeypatch):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(hosted.HostedVerificationError, match="cannot read JSON evidence"):
        hosted.load_object(invalid)
    array = tmp_path / "array.json"
    array.write_text("[]\n", encoding="utf-8")
    with pytest.raises(hosted.HostedVerificationError, match="must be an object"):
        hosted.load_object(array)
    with pytest.raises(hosted.HostedVerificationError, match="not a git repository"):
        hosted.git(tmp_path, "rev-parse", "HEAD")

    monkeypatch.setenv("GIT_DIR", "/must/not/escape")
    monkeypatch.setenv("AI_BASE_COMMIT", "must-not-leak")
    environment = hosted.git_environment()
    assert "GIT_DIR" not in environment
    assert "AI_BASE_COMMIT" not in environment


@pytest.mark.parametrize(
    ("contract_change", "summary_change", "message"),
    [
        ({"acceptance": []}, {}, "explicitly require hosted"),
        ({"riskAssessment": {"riskTypes": []}}, {}, "risk does not declare hosted"),
        ({}, {"hostedPerformanceEvidence": None}, "evidence is missing"),
        (
            {},
            {"hostedPerformanceEvidence": {"status": "complete", "scenarios": []}},
            "already complete",
        ),
        (
            {},
            {"hostedPerformanceEvidence": {"status": "unexpected", "scenarios": []}},
            "status is invalid",
        ),
        (
            {},
            {"hostedPerformanceEvidence": {"status": "partial", "scenarios": []}},
            "pending hosted scenario",
        ),
    ],
)
def test_hosted_requirement_rejects_incomplete_evidence(contract_change, summary_change, message):
    contract = {
        "acceptance": ["Collect hosted evidence."],
        "riskAssessment": {"riskTypes": ["hosted_verification"]},
    }
    summary = {
        "hostedPerformanceEvidence": {
            "status": "partial",
            "scenarios": [{"status": "not_run", "reason": "Pending hosted CI."}],
        }
    }
    contract.update(contract_change)
    summary.update(summary_change)

    with pytest.raises(hosted.HostedVerificationError, match=message):
        hosted.validate_hosted_requirement(contract, summary)


def test_release_intent_requires_an_explicit_non_release_operation():
    with pytest.raises(hosted.HostedVerificationError, match="requestedOperation is required"):
        hosted.validate_no_release_intent({})
    with pytest.raises(hosted.HostedVerificationError, match="publication intent"):
        hosted.validate_no_release_intent(
            {"requestedOperation": {"target": "repository", "action": "deploy"}}
        )


def test_cli_reports_a_fail_closed_snapshot_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai_prepare_hosted_verification.py",
            "--root",
            str(tmp_path),
            "--contract",
            ".ai/work-items/active/missing.contract.json",
        ],
    )

    assert hosted.main() == 1
    assert "hosted verification snapshot rejected" in capsys.readouterr().err


def test_default_quality_runner_binds_the_current_session(tmp_path, monkeypatch):
    session_id = "commit-run-attempt"
    session = tmp_path / "target" / "quality" / "sessions" / session_id
    session.mkdir(parents=True)
    (tmp_path / "target" / "quality" / "current-session.txt").write_text(
        session_id + "\n", encoding="utf-8"
    )
    write_json(session / "summary.json", {"decision": "PASS"})
    inherited = {
        "MAKEFLAGS": "-- CONTRACT=/template/active.contract.json",
        "MAKEOVERRIDES": "CONTRACT",
        "MFLAGS": "--",
        "GNUMAKEFLAGS": "--warn-undefined-variables",
        "CONTRACT": "/template/active.contract.json",
        "SUMMARY": "/template/active.summary.json",
        "TASK": "template-task",
    }
    for key, value in inherited.items():
        monkeypatch.setenv(key, value)
    (tmp_path / "Makefile.ai").write_text("quality:\n\t@true\n", encoding="utf-8")
    monkeypatch.setenv("AI_COCKPIT_MAKE_ENTRYPOINT", "Makefile.ai")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs["env"])
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(hosted.subprocess, "run", fake_run)

    result = hosted.default_quality_runner(tmp_path)

    assert result["sessionId"] == session_id
    assert result["decision"] == "PASS"
    assert result["summaryDigest"].startswith("sha256:")
    assert captured["command"] == ["make", "-f", "Makefile.ai", "quality"]
    assert inherited.keys().isdisjoint(captured)


def test_default_quality_runner_rejects_failed_or_unbound_quality(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_COCKPIT_MAKE_ENTRYPOINT", raising=False)
    monkeypatch.setattr(
        hosted.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1),
    )
    assert hosted.default_quality_runner(tmp_path) == {
        "sessionId": "unknown",
        "decision": "FAIL",
        "summaryDigest": "",
    }

    monkeypatch.setattr(
        hosted.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    with pytest.raises(hosted.HostedVerificationError, match="session pointer is missing"):
        hosted.default_quality_runner(tmp_path)


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


def test_prepare_snapshot_ignores_codex_turn_diff_audit_refs(tmp_path):
    root, contract_path = fixture_repository(tmp_path)

    def quality_with_codex_audit_ref(candidate: Path) -> dict[str, str]:
        git(candidate, "update-ref", "refs/codex/turn-diffs/captures/test/base", "HEAD")
        return passing_quality(candidate)

    receipt = hosted.prepare_snapshot(
        root=root,
        contract_path=contract_path,
        output=root / "target" / "receipt.json",
        quality_runner=quality_with_codex_audit_ref,
    )

    assert receipt["quality"]["decision"] == "PASS"


def test_prepare_snapshot_rejects_project_ref_churn_from_quality(tmp_path):
    root, contract_path = fixture_repository(tmp_path)

    def quality_with_project_ref(candidate: Path) -> dict[str, str]:
        git(candidate, "update-ref", "refs/heads/codex/unauthorized-quality-ref", "HEAD")
        return passing_quality(candidate)

    with pytest.raises(hosted.HostedVerificationError, match="local quality mutated Git refs"):
        hosted.prepare_snapshot(
            root=root,
            contract_path=contract_path,
            output=root / "target" / "receipt.json",
            quality_runner=quality_with_project_ref,
        )


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


def test_prepare_snapshot_rejects_invalid_identity_base_and_quality_receipt(tmp_path):
    root, contract_path = fixture_repository(tmp_path)
    summary_path = Path(str(contract_path).replace(".contract.json", ".summary.json"))
    output = root / "target" / "receipt.json"

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["contractVersion"] = 1
    write_json(contract_path, contract)
    git(root, "add", ".")
    git(root, "commit", "-qm", "invalid identity")
    with pytest.raises(hosted.HostedVerificationError, match="identity is invalid"):
        hosted.prepare_snapshot(
            root=root,
            contract_path=contract_path,
            output=output,
            quality_runner=passing_quality,
        )

    contract["contractVersion"] = 2
    contract["baseCommit"] = "short"
    write_json(contract_path, contract)
    git(root, "add", ".")
    git(root, "commit", "-qm", "invalid base")
    with pytest.raises(hosted.HostedVerificationError, match="baseCommit is invalid"):
        hosted.prepare_snapshot(
            root=root,
            contract_path=contract_path,
            output=output,
            quality_runner=passing_quality,
        )

    contract["baseCommit"] = git(root, "rev-parse", "HEAD~2")
    write_json(contract_path, contract)
    git(root, "add", ".")
    git(root, "commit", "-qm", "valid base")
    with pytest.raises(hosted.HostedVerificationError, match="quality evidence is incomplete"):
        hosted.prepare_snapshot(
            root=root,
            contract_path=contract_path,
            output=output,
            quality_runner=lambda _root: {
                "sessionId": "",
                "decision": "PASS",
                "summaryDigest": "",
            },
        )
    assert summary_path.is_file()


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
