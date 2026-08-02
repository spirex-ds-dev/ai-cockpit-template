"""Focused tests for the external identity evidence boundary."""

from __future__ import annotations

import copy

import ai_external_identity


def provider_approval() -> dict:
    return {
        "schemaVersion": 1,
        "approvalType": "destructive_change",
        "identityLevel": "provider_verified",
        "actor": "github-user",
        "provider": "github",
        "evidence": {
            "repository": "org/repo",
            "pullRequest": 123,
            "reviewId": 456,
            "commitSha": "0123456789abcdef0123456789abcdef01234567",
        },
        "scope": ["src/api/public.py"],
    }


def direct_user_approval() -> dict:
    return {
        "schemaVersion": 1,
        "approvalType": "destructive_change",
        "identityLevel": "direct_user_authorized",
        "actor": "repository-owner",
        "provider": None,
        "evidence": {
            "directUserInstructionRef": "conversation:2026-08-02-cleanup",
            "directUserInstructionDigest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "authorizedAt": "2026-08-02T10:00:00Z",
        },
        "scope": [".worktrees/example"],
    }


def test_repository_name_is_repository_recorded_only() -> None:
    record = {"approved": True, "approvedBy": "Ray", "reason": "approved"}

    assert ai_external_identity.identity_state(record) == "repository_recorded_only"
    assert "repository_recorded_only" in " ".join(
        ai_external_identity.high_risk_approval_issues(record)
    )


def test_self_declared_and_repository_recorded_cannot_authorize_high_risk() -> None:
    for level in ("self_declared", "repository_recorded"):
        record = provider_approval()
        record["identityLevel"] = level
        record["provider"] = None
        record["evidence"] = {}

        issues = ai_external_identity.high_risk_approval_issues(record)

        assert issues
        assert "provider_verified or enterprise_verified" in " ".join(issues)


def test_provider_verified_requires_provider_bound_review_evidence() -> None:
    record = provider_approval()
    assert ai_external_identity.approval_issues(record) == []
    assert ai_external_identity.high_risk_approval_issues(record) == []

    for field in ("repository", "pullRequest", "reviewId", "commitSha"):
        malformed = copy.deepcopy(record)
        del malformed["evidence"][field]
        issues = ai_external_identity.approval_issues(malformed)
        assert any(
            field in issue or "reviewId, environmentApprovalId, or rulesetId" in issue
            for issue in issues
        )


def test_enterprise_verified_requires_external_enterprise_reference() -> None:
    record = provider_approval()
    record.update(
        {
            "identityLevel": "enterprise_verified",
            "provider": "company-iam",
            "evidence": {
                "enterpriseSystem": "access-governance",
                "externalReference": "approval/2026/123",
            },
        }
    )
    assert ai_external_identity.approval_issues(record) == []
    assert ai_external_identity.high_risk_approval_issues(record) == []

    del record["evidence"]["externalReference"]
    assert "externalReference" in " ".join(ai_external_identity.approval_issues(record))


def test_scope_must_be_non_empty_and_exact() -> None:
    record = provider_approval()
    record["scope"] = []
    assert ai_external_identity.approval_issues(record)

    record = provider_approval()
    issues = ai_external_identity.high_risk_approval_issues(
        record, required_scope=["different/path.py"]
    )
    assert "exactly match" in " ".join(issues)


def test_provider_commit_must_be_a_real_object_id_shape() -> None:
    record = provider_approval()
    record["evidence"]["commitSha"] = "not-a-sha"
    assert "hexadecimal object ID" in " ".join(ai_external_identity.approval_issues(record))


def test_non_destructive_approval_type_is_not_high_risk_authority() -> None:
    record = provider_approval()
    record["approvalType"] = "restricted_write"
    assert "approvalType" in " ".join(ai_external_identity.high_risk_approval_issues(record))


def test_direct_user_authorization_requires_exact_scope_and_instruction_binding() -> None:
    record = direct_user_approval()

    assert ai_external_identity.identity_state(record) == "direct_user_authorized"
    assert (
        ai_external_identity.high_risk_approval_issues(
            record, required_scope=[".worktrees/example"]
        )
        == []
    )

    for field in ("directUserInstructionRef", "directUserInstructionDigest", "authorizedAt"):
        malformed = copy.deepcopy(record)
        del malformed["evidence"][field]
        assert field in " ".join(ai_external_identity.high_risk_approval_issues(malformed))

    malformed = copy.deepcopy(record)
    malformed["evidence"]["reviewId"] = 123
    assert "provider" in " ".join(ai_external_identity.high_risk_approval_issues(malformed))

    malformed = copy.deepcopy(record)
    malformed["evidence"]["directUserInstructionDigest"] = "sha256:not-a-digest"
    assert "sha256 instruction digest" in " ".join(
        ai_external_identity.high_risk_approval_issues(malformed)
    )

    malformed = copy.deepcopy(record)
    malformed["evidence"]["authorizedAt"] = "not-a-timestamp"
    assert "ISO-8601" in " ".join(ai_external_identity.high_risk_approval_issues(malformed))

    assert "exactly match" in " ".join(
        ai_external_identity.high_risk_approval_issues(
            record, required_scope=[".worktrees/another-target"]
        )
    )
