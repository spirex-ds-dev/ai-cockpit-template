from ai_required_evidence import EvidenceContext, derive_required_evidence


def test_deletion_derives_missing_evidence_without_contract_unknowns():
    result = derive_required_evidence(
        EvidenceContext(
            requested_operation="modify",
            changed_paths=("scripts/legacy_api.py",),
            risk_types=("destructive_change",),
            capability_claims=(),
            environment="repository",
            external_system="",
            destructive_level="delete",
            governance_profile="standard",
            available_evidence=("usage_analysis", "reference_search"),
        )
    )

    assert result.required_evidence == (
        "usage_analysis",
        "reference_search",
        "public_api_impact",
        "test_impact",
        "migration_impact",
        "rollback_plan",
    )
    assert result.missing_evidence == (
        "public_api_impact",
        "test_impact",
        "migration_impact",
        "rollback_plan",
    )
    assert result.owner_by_evidence["public_api_impact"] == "repository_maintainer"
    assert result.blocking_level == "block"
    assert result.human_decision_required is False
    assert result.forbidden_claims == (
        "Do not claim deletion safety or compatibility preservation.",
    )


def test_publication_requires_human_decision_and_release_evidence():
    result = derive_required_evidence(
        EvidenceContext(
            requested_operation="publish",
            changed_paths=("release.json",),
            risk_types=(),
            capability_claims=("release_available",),
            environment="repository",
            external_system="provider",
            destructive_level="none",
            governance_profile="release",
            available_evidence=("tag", "commit", "digest"),
        )
    )

    assert result.matched_rules == ("publication",)
    assert result.missing_evidence == (
        "sbom",
        "provenance",
        "provider_release_receipt",
        "asset_availability",
    )
    assert result.human_decision_required is True
    assert result.owner_by_evidence["provider_release_receipt"] == "release_manager"


def test_mobile_fixture_evidence_does_not_imply_unobserved_lifecycle_stages():
    result = derive_required_evidence(
        EvidenceContext(
            requested_operation="mobile_validate",
            changed_paths=("examples/flutter/lib/main.dart",),
            risk_types=(),
            capability_claims=(),
            environment="repository",
            external_system="",
            destructive_level="none",
            governance_profile="standard",
            available_evidence=("source_compiles", "unit_tests"),
        )
    )

    assert result.missing_evidence == ("simulator", "device", "signing", "store_submission")
    assert result.forbidden_claims == ("Do not claim unobserved mobile lifecycle stages.",)


def test_permission_context_requires_identity_scope_approval_and_audit_receipt():
    result = derive_required_evidence(
        EvidenceContext(
            requested_operation="modify",
            changed_paths=(".github/branch-protection.json",),
            risk_types=("permission_operation",),
            capability_claims=("provider_verified",),
            environment="repository",
            external_system="provider",
            destructive_level="none",
            governance_profile="strict",
            available_evidence=("resource_id",),
        )
    )

    assert result.missing_evidence == (
        "provider_identity",
        "authorization_scope",
        "approval_evidence",
        "audit_receipt",
    )
    assert result.human_decision_required is True
    assert result.owner_by_evidence["audit_receipt"] == "repository_administrator"


def test_unmatched_context_is_explicitly_non_blocking():
    result = derive_required_evidence(
        EvidenceContext(
            requested_operation="modify",
            changed_paths=("docs/guide.md",),
            risk_types=(),
            capability_claims=(),
            environment="repository",
            external_system="",
            destructive_level="none",
            governance_profile="lite",
            available_evidence=(),
        )
    )

    assert result.required_evidence == ()
    assert result.missing_evidence == ()
    assert result.blocking_level == "none"
