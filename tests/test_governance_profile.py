import json
import subprocess
import sys
from datetime import UTC, datetime

import pytest

from scripts import determine_governance_profile as routing

POLICY = """\
schemaVersion: 1
profileOrder:
  - lite
  - standard
  - strict
  - release
unknownProfile: standard
evidenceOnlyPatterns:
  - .ai/cockpit/current_status.md
  - .ai/work-items/starts/**
  - .ai/work-items/active/*.outcome.json
  - .ai/work-items/active/*.outcome.md
profiles:
  lite:
    patterns:
      - docs/**
      - README*
    requiredGroups:
      - quality-fast
    dispatchTarget: quality-fast
  standard:
    patterns:
      - src/**
      - tests/**
    requiredGroups:
      - quality-fast
      - project-test
      - check-ai-reference-impact
      - check-ai-test-weakening
    dispatchTarget: quality-standard
  strict:
    patterns:
      - .ai/**
      - scripts/ai_*.py
      - Makefile
    requiredGroups:
      - quality-full
    dispatchTarget: quality-full
  release:
    patterns:
      - release.json
      - .github/workflows/release*.yml
    requiredGroups:
      - quality-release
    dispatchTarget: quality-release
"""


@pytest.fixture
def policy_path(tmp_path):
    path = tmp_path / "governance-routing.yaml"
    path.write_text(POLICY, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (["docs/guide.md"], "lite"),
        (["src/service.py"], "standard"),
        ([".ai/guards/policy.yaml"], "strict"),
        (["release.json"], "release"),
        (["unclassified.file"], "standard"),
        ([], "standard"),
        (["docs/guide.md", "src/service.py"], "standard"),
        (["docs/guide.md", "Makefile", "release.json"], "release"),
    ],
)
def test_selects_highest_profile_conservatively(policy_path, paths, expected):
    policy = routing.load_policy(policy_path)

    receipt = routing.determine(paths, policy)

    assert receipt["automaticProfile"] == expected
    assert receipt["selectedProfile"] == expected
    assert receipt["changedPaths"] == sorted(paths)
    assert receipt["dispatchTarget"] == policy["profiles"][expected]["dispatchTarget"]


def test_receipt_is_independent_of_input_order(policy_path):
    policy = routing.load_policy(policy_path)
    left = routing.determine(["src/b.py", "docs/a.md"], policy)
    right = routing.determine(["docs/a.md", "src/b.py"], policy)

    assert json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def test_generated_work_item_evidence_does_not_force_strict(policy_path):
    policy = routing.load_policy(policy_path)

    docs = routing.determine(["docs/guide.md", ".ai/work-items/starts/wi-3.json"], policy)
    evidence_only = routing.determine(
        [
            ".ai/cockpit/current_status.md",
            ".ai/work-items/starts/wi-3.json",
            ".ai/work-items/active/wi-3.outcome.json",
        ],
        policy,
    )

    assert docs["selectedProfile"] == "lite"
    assert evidence_only["selectedProfile"] == "standard"
    assert docs["pathDecisions"][0]["profile"] == "evidence_only"


@pytest.mark.parametrize(
    "content",
    [
        "schemaVersion: 2\n",
        POLICY.replace("  - release\n", "  - mystery\n", 1),
        POLICY.replace("unknownProfile: standard", "unknownProfile: lite"),
        POLICY.replace("dispatchTarget: quality-full", "dispatchTarget: quality-fast"),
    ],
)
def test_policy_validation_fails_closed(tmp_path, content):
    path = tmp_path / "bad.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        routing.load_policy(path)


@pytest.mark.parametrize("path", ["../outside", "/absolute/path", "docs/../../escape"])
def test_rejects_unsafe_paths(policy_path, tmp_path, path):
    policy = routing.load_policy(policy_path)

    with pytest.raises(ValueError, match="unsafe changed path"):
        routing.determine([path], policy, repository=tmp_path)


def test_rejects_symlink_escape(policy_path, tmp_path):
    outside = tmp_path.parent / "outside-routing.txt"
    outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "src" / "escape.py"
    link.parent.mkdir()
    link.symlink_to(outside)
    policy = routing.load_policy(policy_path)

    with pytest.raises(ValueError, match="escapes repository"):
        routing.determine(["src/escape.py"], policy, repository=tmp_path)


def test_explicit_profile_can_raise_but_not_lower(policy_path):
    policy = routing.load_policy(policy_path)
    assert (
        routing.determine(["docs/a.md"], policy, requested="strict")["selectedProfile"] == "strict"
    )

    with pytest.raises(ValueError, match="cannot lower"):
        routing.determine(["Makefile"], policy, requested="standard")


def test_valid_work_item_override_can_lower_automatic_profile(policy_path):
    policy = routing.load_policy(policy_path)
    contract = {
        "workItemId": "wi-3",
        "governanceProfile": {
            "selected": "standard",
            "source": "human_override",
            "reasons": ["bounded exception"],
            "override": {
                "approvalEvidence": "maintainer-approval:42",
                "reason": "generated governance fixture only",
                "risks": ["reduced full-suite coverage"],
                "notRunChecks": ["quality-full"],
                "workItemOnly": True,
                "workItemId": "wi-3",
            },
        },
    }

    result = routing.determine(["Makefile"], policy, contract=contract)

    assert result["automaticProfile"] == "strict"
    assert result["selectedProfile"] == "standard"
    assert result["source"] == "human_override"
    assert result["override"]["applied"] is True


@pytest.mark.parametrize(
    "override",
    [
        {"approvalEvidence": "x"},
        {
            "approvalEvidence": "x",
            "reason": "x",
            "risks": ["x"],
            "notRunChecks": ["quality-full"],
            "workItemOnly": True,
            "workItemId": "another-item",
        },
        {
            "approvalEvidence": "x",
            "reason": "x",
            "risks": ["x"],
            "notRunChecks": ["quality-full"],
            "expiresAt": "2026-07-31T23:59:59Z",
        },
    ],
)
def test_invalid_or_expired_override_restores_automatic(policy_path, override):
    policy = routing.load_policy(policy_path)
    contract = {
        "workItemId": "wi-3",
        "governanceProfile": {
            "selected": "lite",
            "source": "human_override",
            "reasons": ["exception"],
            "override": override,
        },
    }

    result = routing.determine(
        ["Makefile"],
        policy,
        contract=contract,
        now=datetime(2026, 8, 1, tzinfo=UTC),
    )

    assert result["selectedProfile"] == "strict"
    assert result["source"] == "automatic"
    assert result["override"]["applied"] is False
    assert result["override"]["issues"]


def test_changed_paths_reports_invalid_git_base(tmp_path):
    with pytest.raises(RuntimeError, match="unable to determine changed paths"):
        routing.changed_paths("missing-base", "HEAD", tmp_path)


def test_changed_paths_includes_committed_worktree_and_untracked_changes(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    tracked = tmp_path / "docs" / "tracked.md"
    tracked.parent.mkdir()
    tracked.write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True, capture_output=True, check=True
    ).stdout.strip()
    tracked.write_text("after\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "untracked.py").write_text("pass\n", encoding="utf-8")

    assert routing.changed_paths(base, "HEAD", tmp_path) == [
        "docs/tracked.md",
        "src/untracked.py",
    ]


def test_cli_writes_receipt_for_complete_worktree_diff(tmp_path, policy_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    guide = tmp_path / "docs" / "guide.md"
    guide.parent.mkdir()
    guide.write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True, capture_output=True, check=True
    ).stdout.strip()
    guide.write_text("after\n", encoding="utf-8")
    output = tmp_path / "target" / "profile.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "determine_governance_profile.py",
            "--repository",
            str(tmp_path),
            "--policy",
            str(policy_path),
            "--base",
            base,
            "--output",
            str(output),
        ],
    )

    assert routing.main() == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["selectedProfile"] == "lite"
    assert receipt["changedPaths"] == ["docs/guide.md"]


def test_cli_defaults_to_head_for_installed_adopter_without_contract(
    tmp_path, policy_path, monkeypatch
):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("adopter\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)
    policy = tmp_path / ".ai" / "quality" / "governance-routing.yaml"
    policy.parent.mkdir(parents=True)
    policy.write_text(policy_path.read_text(encoding="utf-8"), encoding="utf-8")
    output = tmp_path / "target" / "profile.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "determine_governance_profile.py",
            "--repository",
            str(tmp_path),
            "--output",
            str(output),
        ],
    )

    assert routing.main() == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["base"] == "HEAD"
    assert receipt["selectedProfile"] == "strict"
    assert receipt["changedPaths"] == [".ai/quality/governance-routing.yaml"]
