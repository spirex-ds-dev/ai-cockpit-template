import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts import determine_governance_profile as routing
from scripts import determine_quality_scope as quality_scope

POLICY = """\
schemaVersion: 1
profileOrder:
  - light
  - standard
  - strict
unknownProfile: standard
evidenceOnlyPatterns:
  - .ai/cockpit/current_status.md
  - .ai/work-items/starts/**
  - .ai/work-items/active/*.outcome.json
  - .ai/work-items/active/*.outcome.md
profiles:
  light:
    patterns:
      - docs/**
      - README*
    requiredGroups:
      - quality-fast
    dispatchTarget: quality-fast
    verificationDepth: focused
    requiredEvidence:
      - scope
      - trust
      - lifecycle
      - evidence_integrity
    optionalChecks:
      - project-test
    mandatoryControls:
      - scope
      - trust
      - lifecycle
      - evidence_integrity
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
    verificationDepth: project
    requiredEvidence:
      - scope
      - trust
      - lifecycle
      - evidence_integrity
      - project-test
    optionalChecks:
      - quality-heavy
    mandatoryControls:
      - scope
      - trust
      - lifecycle
      - evidence_integrity
  strict:
    patterns:
      - .ai/**
      - scripts/ai_*.py
      - Makefile
    requiredGroups:
      - quality-full
    dispatchTarget: quality-full
    verificationDepth: full
    requiredEvidence:
      - scope
      - trust
      - lifecycle
      - evidence_integrity
      - project-test
      - quality-heavy
    optionalChecks:
      - quality-project-consistency
    mandatoryControls:
      - scope
      - trust
      - lifecycle
      - evidence_integrity
releaseOwnedPatterns:
  - release.json
  - .github/workflows/release*.yml
"""


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_EVIDENCE_PATHS = [
    ".ai/work-items/active/docs-only-42.contract.json",
    ".ai/work-items/active/docs-only-42.summary.json",
    ".ai/work-items/starts/docs-only-42.json",
    ".ai/work-items/active/docs-only-42.outcome.json",
    ".ai/work-items/active/docs-only-42.outcome.md",
    ".ai/cockpit/current_status.md",
    ".ai/cockpit/task_report.json",
    ".ai/cockpit/task_report.md",
    ".ai/work-items/archive/2026/docs-only-42.contract.json",
    ".ai/work-items/archive/index.json",
]


@pytest.fixture
def policy_path(tmp_path):
    path = tmp_path / "governance-routing.yaml"
    path.write_text(POLICY, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (["docs/guide.md"], "light"),
        (["src/service.py"], "standard"),
        ([".ai/guards/policy.yaml"], "strict"),
        (["release.json"], "strict"),
        (["unclassified.file"], "standard"),
        ([], "standard"),
        (["docs/guide.md", "src/service.py"], "standard"),
        (["docs/guide.md", "Makefile", "release.json"], "strict"),
    ],
)
def test_selects_highest_profile_conservatively(policy_path, paths, expected):
    policy = routing.load_policy(policy_path)

    receipt = routing.determine(paths, policy)

    assert receipt["automaticProfile"] == expected
    assert receipt["selectedProfile"] == expected
    assert receipt["changedPaths"] == sorted(paths)
    assert receipt["dispatchTarget"] == policy["profiles"][expected]["dispatchTarget"]


def test_profile_projection_declares_depth_evidence_and_optional_checks(policy_path):
    policy = routing.load_policy(policy_path)

    projections = {
        name: routing.determine(["docs/guide.md"], policy, requested=name)["profileProjection"]
        for name in routing.PROFILE_ORDER
    }

    assert [projections[name]["verificationDepth"] for name in routing.PROFILE_ORDER] == [
        "focused",
        "project",
        "full",
    ]
    assert set(projections["light"]["requiredEvidence"]).issubset(
        projections["standard"]["requiredEvidence"]
    )
    assert set(projections["standard"]["requiredEvidence"]).issubset(
        projections["strict"]["requiredEvidence"]
    )
    assert projections["light"]["optionalChecks"]
    assert projections["standard"]["optionalChecks"]
    assert projections["strict"]["optionalChecks"]
    assert (
        projections["light"]["mandatoryControls"]
        == projections["standard"]["mandatoryControls"]
        == projections["strict"]["mandatoryControls"]
    )


def test_profile_projection_never_disables_mandatory_controls(policy_path):
    policy = routing.load_policy(policy_path)

    for name in routing.PROFILE_ORDER:
        projection = routing.determine(["docs/guide.md"], policy, requested=name)[
            "profileProjection"
        ]
        assert set(projection["mandatoryControls"]) >= {
            "scope",
            "trust",
            "lifecycle",
            "evidence_integrity",
        }
        assert not set(projection["optionalChecks"]) & set(projection["mandatoryControls"])


def test_policy_rejects_optional_check_that_overlaps_mandatory_control(tmp_path):
    path = tmp_path / "governance-routing.yaml"
    path.write_text(
        POLICY.replace(
            "      - project-test\n    mandatoryControls:",
            "      - scope\n    mandatoryControls:",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="cannot disable mandatory controls"):
        routing.load_policy(path)


def test_release_escalation_is_separate_from_profile_projection(policy_path):
    policy = routing.load_policy(policy_path)

    non_release = routing.determine(["Makefile"], policy)
    release = routing.determine(["release.json"], policy)

    assert non_release["selectedProfile"] == "strict"
    assert non_release["verificationEscalations"] == []
    assert release["selectedProfile"] == "strict"
    assert release["verificationEscalations"] == ["release_preflight", "distribution"]
    assert "release_preflight" not in non_release["profileProjection"]["optionalChecks"]
    assert (
        release["profileProjection"]["optionalChecks"]
        != non_release["profileProjection"]["optionalChecks"]
    )


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

    assert docs["selectedProfile"] == "light"
    assert evidence_only["selectedProfile"] == "standard"
    assert docs["pathDecisions"][0]["profile"] == "evidence_only"


def test_repository_policy_routes_docs_plus_all_lifecycle_evidence_to_light():
    policy = routing.load_policy(REPOSITORY_ROOT / ".ai/quality/governance-routing.yaml")

    result = routing.determine(["docs/guide.md", *LIFECYCLE_EVIDENCE_PATHS], policy)

    assert result["automaticProfile"] == "light"
    assert result["selectedProfile"] == "light"
    assert result["dispatchTarget"] == "quality-fast"
    decisions = {item["path"]: item for item in result["pathDecisions"]}
    for path in LIFECYCLE_EVIDENCE_PATHS:
        assert decisions[path]["profile"] == "evidence_only"
        assert decisions[path]["reasons"]


def test_repository_policy_keeps_strict_and_release_precedence_over_lifecycle_evidence():
    policy = routing.load_policy(REPOSITORY_ROOT / ".ai/quality/governance-routing.yaml")
    paths = ["docs/guide.md", *LIFECYCLE_EVIDENCE_PATHS, "scripts/ai_finish.py"]

    strict = routing.determine(paths, policy)
    release = routing.determine(
        ["docs/guide.md", *LIFECYCLE_EVIDENCE_PATHS, "release.json"], policy
    )

    assert strict["selectedProfile"] == "strict"
    assert strict["dispatchTarget"] == "quality-full"
    assert release["selectedProfile"] == "strict"
    assert release["verificationEscalations"] == ["release_preflight", "distribution"]


def test_repository_policy_uses_targeted_strict_route_for_automatic_governance_code():
    policy = routing.load_policy(REPOSITORY_ROOT / ".ai/quality/governance-routing.yaml")

    result = routing.determine(["scripts/ai_check_reference_impact.py"], policy)

    assert result["selectedProfile"] == "strict"
    assert result["dispatchTarget"] == "quality-strict-targeted"
    assert result["qualityRouting"]["reason"]
    assert "quality-project-consistency-group" in result["requiredGroups"]


def test_repository_policy_keeps_explicit_strict_route_full():
    policy = routing.load_policy(REPOSITORY_ROOT / ".ai/quality/governance-routing.yaml")

    result = routing.determine(["scripts/ai_check_reference_impact.py"], policy, requested="strict")

    assert result["dispatchTarget"] == "quality-full"


def test_repository_policy_keeps_unknown_and_evidence_only_diffs_conservative():
    policy = routing.load_policy(REPOSITORY_ROOT / ".ai/quality/governance-routing.yaml")

    unknown = routing.determine(["unclassified.file"], policy)
    evidence_only = routing.determine(LIFECYCLE_EVIDENCE_PATHS, policy)

    assert unknown["selectedProfile"] == "standard"
    assert evidence_only["selectedProfile"] == "standard"


def test_release_resource_adds_release_escalation_without_fourth_profile(policy_path):
    policy = routing.load_policy(policy_path)

    result = routing.determine(["release.json"], policy)

    assert result["selectedProfile"] == "strict"
    assert result["operationClasses"] == ["release"]
    assert result["verificationEscalations"] == ["release_preflight", "distribution"]


def test_non_release_strict_resource_does_not_add_release_graph(policy_path):
    policy = routing.load_policy(policy_path)

    result = routing.determine(["Makefile"], policy)

    assert result["selectedProfile"] == "strict"
    assert result["operationClasses"] == []
    assert result["verificationEscalations"] == []


def test_legacy_release_input_is_rejected(policy_path):
    policy = routing.load_policy(policy_path)

    with pytest.raises(ValueError, match="unsupported governance profile"):
        routing.determine(["docs/guide.md"], policy, requested="release")


def test_release_capability_claim_adds_escalation_without_release_scope(policy_path):
    policy = routing.load_policy(policy_path)

    result = routing.determine(
        ["docs/guide.md"],
        policy,
        contract={"capabilityClaims": ["release_ready"]},
    )

    assert result["selectedProfile"] == "strict"
    assert result["verificationEscalations"] == ["release_preflight", "distribution"]


def test_tag_operation_adds_release_escalation_without_release_named_profile(policy_path):
    policy = routing.load_policy(policy_path)

    result = routing.determine(
        ["docs/guide.md"],
        policy,
        contract={"requestedOperation": {"action": "create_tag"}},
    )

    assert result["selectedProfile"] == "strict"
    assert result["operationClasses"] == ["release"]
    assert result["verificationEscalations"] == ["release_preflight", "distribution"]


def test_legacy_quality_scope_mode_is_rejected():
    with pytest.raises(ValueError, match="unsupported quality scope mode"):
        quality_scope.determine(["docs/guide.md"], explicit="release")


@pytest.mark.parametrize(
    "content",
    [
        "schemaVersion: 2\n",
        POLICY.replace("  - strict\n", "  - mystery\n", 1),
        POLICY.replace("unknownProfile: standard", "unknownProfile: light"),
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
            "selected": "light",
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
    assert receipt["selectedProfile"] == "light"
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
