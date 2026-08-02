import ai_check_work_item


def valid_contract():
    return {
        "contractVersion": 1,
        "workItemId": "task",
        "mode": "code",
        "title": "Task",
        "problemStatement": "Describe the problem this task solves, or state that no product context was provided for a mechanical change.",
        "baseCommit": "1234567",
        "baselineDirtyPaths": [],
        "scope": ["scripts/**", "tests/**"],
        "outOfScope": [],
        "sources": ["spec"],
        "unknowns": [],
        "notCodable": False,
        "acceptance": ["works"],
        "verification": [{"command": "python3 -m pytest", "required": True}],
        "destructiveChangePolicy": {
            "allowed": False,
            "requiresHumanApproval": True,
            "allowPatterns": [],
        },
        "rollbackNote": "revert",
    }


def test_problem_statement_is_optional_but_must_not_be_empty():
    contract = valid_contract()
    contract.pop("problemStatement")
    assert ai_check_work_item.validate_contract(contract) == []

    contract["problemStatement"] = ""
    issues = ai_check_work_item.validate_contract(contract)
    assert "problemStatement must be a non-empty string" in issues


def test_contract_schema_accepts_resume_writer_field_and_rejects_unrelated_unknowns():
    contract = valid_contract()
    contract["resumeHistory"] = []

    issues = ai_check_work_item.validate_contract(contract)

    assert "unknown field: resumeHistory" not in issues

    contract["unexpectedField"] = True
    assert "unknown field: unexpectedField" in ai_check_work_item.validate_contract(contract)


def test_required_evidence_context_requires_normalized_structured_inputs():
    contract = valid_contract()
    contract["requiredEvidenceContext"] = {
        "destructiveLevel": "delete",
        "availableEvidence": ["usage_analysis", "reference_search"],
        "externalSystem": "provider",
    }

    assert ai_check_work_item.validate_contract(contract) == []

    contract["requiredEvidenceContext"]["availableEvidence"] = ["usage_analysis", ""]
    assert "requiredEvidenceContext.availableEvidence must be a list of non-empty strings" in (
        ai_check_work_item.validate_contract(contract)
    )


def test_contract_accepts_required_governance_metadata_for_a_work_item():
    contract = valid_contract()
    contract.update(
        {
            "requiredEvidence": ["focused regression receipt"],
            "humanDecisionPoints": ["A reviewer accepts any high residual risk."],
            "documentationImpact": "No standalone documentation change is required.",
            "performanceImpact": "Focused validation adds no runtime dependency.",
            "residualRiskExpectation": "Open high risks require an owner and acceptance state.",
            "predecessorClosureEvidence": "No predecessor exists for the first Work Item.",
            "rollbackPlan": "Revert the Work Item commit and rerun focused validation.",
        }
    )

    assert ai_check_work_item.validate_contract(contract) == []


def test_v2_code_contract_requires_governance_metadata():
    contract = valid_contract()
    contract.update(
        {
            "contractVersion": 2,
            "governanceMetadataVersion": 1,
            "baseCommit": "1234567890abcdef",
            "scope": [".ai/work-items/active/task.contract.json"],
            "verification": [{"check": "quality", "required": True}],
            "rawUserRequest": "Enforce Work Item metadata.",
            "rawRequestSource": {
                "type": "human",
                "reference": "test:metadata",
                "capturedAt": "2026-08-01",
                "digest": "sha256:test",
            },
            "requestedOperation": {
                "target": "repository_governance",
                "action": "modify",
                "environment": "repository",
                "effect": "enforce",
                "authorityRequired": False,
            },
        }
    )

    issues = ai_check_work_item.validate_contract(contract)

    assert "governanceMetadataVersion 1 requires field: requiredEvidence" in issues
    assert "governanceMetadataVersion 1 requires field: rollbackPlan" in issues


def test_v2_code_work_item_requires_sourced_raw_request():
    contract = valid_contract()
    contract.update(
        {
            "contractVersion": 2,
            "scope": [".ai/work-items/active/task.contract.json"],
            "baseCommit": "1234567890abcdef",
            "verification": [{"check": "quality", "required": True}],
        }
    )
    issues = ai_check_work_item.validate_contract(contract)
    assert any("rawUserRequest" in issue for issue in issues)

    contract["rawUserRequest"] = "Add a deterministic governance guard."
    contract["rawRequestSource"] = {
        "type": "human",
        "reference": "user-request:test",
        "capturedAt": "2026-07-21",
        "digest": "sha256:test",
    }
    issues = ai_check_work_item.validate_contract(contract)
    assert not any("rawUserRequest" in issue or "rawRequestSource" in issue for issue in issues)


def test_code_work_item_requires_requested_operation():
    contract = valid_contract()
    contract.update(
        {
            "contractVersion": 2,
            "scope": [".ai/work-items/active/task.contract.json"],
            "baseCommit": "1234567890abcdef",
            "verification": [{"check": "quality", "required": True}],
            "rawUserRequest": "Change governance policy.",
            "rawRequestSource": {
                "type": "human",
                "reference": "test:operation",
                "capturedAt": "2026-07-21",
                "digest": "sha256:test",
            },
            "declaredIntent": {
                "summary": "Change governance policy.",
                "requestedCapabilities": ["ai_governance"],
            },
        }
    )
    issues = ai_check_work_item.validate_contract(contract)
    assert any("requestedOperation" in issue for issue in issues)


def test_destructive_approval_requires_provider_or_enterprise_identity() -> None:
    contract = valid_contract()
    contract["destructiveChangePolicy"] = {
        "allowed": True,
        "requiresHumanApproval": True,
        "allowPatterns": ["src/api/public.py"],
        "approvalEvidence": {
            "approved": True,
            "approvedBy": "Ray",
            "reason": "Approved in repository text.",
        },
    }

    issues = ai_check_work_item.validate_contract(contract)

    assert any("repository_recorded_only" in issue for issue in issues)


def test_destructive_approval_accepts_provider_bound_identity_evidence() -> None:
    contract = valid_contract()
    contract["destructiveChangePolicy"] = {
        "allowed": True,
        "requiresHumanApproval": True,
        "allowPatterns": ["src/api/public.py"],
        "approvalEvidence": {
            "approved": True,
            "approvedBy": "github-user",
            "reason": "Approved by a provider review bound to the target commit.",
            "identityEvidence": {
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
            },
        },
    }

    assert ai_check_work_item.validate_contract(contract) == []


def test_destructive_approval_accepts_exact_direct_user_authorization() -> None:
    contract = valid_contract()
    contract["destructiveChangePolicy"] = {
        "allowed": True,
        "requiresHumanApproval": True,
        "allowPatterns": [".worktrees/example"],
        "approvalEvidence": {
            "approved": True,
            "approvedBy": "repository-owner",
            "reason": "Direct user instruction authorizes this exact cleanup.",
            "identityEvidence": {
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
            },
        },
    }

    assert ai_check_work_item.validate_contract(contract) == []


def test_v2_code_work_item_rejects_skeleton_placeholders():
    contract = valid_contract()
    contract.update(
        {
            "contractVersion": 2,
            "baseCommit": "1234567890abcdef",
            "scope": [".ai/work-items/active/task.contract.json"],
            "verification": [{"check": "quality", "required": True}],
            "rawUserRequest": "Harden governance.",
            "rawRequestSource": {
                "type": "human",
                "reference": "test:placeholder",
                "capturedAt": "2026-07-22",
                "digest": "sha256:test",
            },
            "declaredIntent": {
                "summary": "Harden governance.",
                "requestedCapabilities": ["ai_governance"],
            },
            "requestedOperation": {
                "target": "repository_governance",
                "action": "modify",
                "environment": "repository",
                "effect": "enforce",
                "authorityRequired": False,
            },
            "intent": {
                "problem": "Initial skeleton; replace this.",
                "constraints": ["Replace with task-specific constraints."],
                "rationale": "Initial skeleton; replace with rationale.",
            },
            "acceptance": ["The new feature is implemented according to requirements."],
            "sources": [{"path": "spec", "reason": "Initial Work Item skeleton."}],
            "scenarioCoverage": [
                {
                    "scenario": "Replace this scenario.",
                    "required": True,
                    "status": "verified",
                    "evidence": ["spec"],
                }
            ],
        }
    )
    issues = ai_check_work_item.validate_contract(contract)
    assert any("placeholder" in issue for issue in issues)


def test_governance_profile_rejects_invalid_automatic_and_override_evidence():
    assert ai_check_work_item.validate_governance_profile({"governanceProfile": "lite"}) == [
        "governanceProfile must be an object"
    ]

    automatic = {
        "governanceProfile": {
            "selected": "unknown",
            "source": "automatic",
            "reasons": [""],
            "override": {},
        }
    }
    issues = ai_check_work_item.validate_governance_profile(automatic)
    assert any("selected must be one of" in issue for issue in issues)
    assert any("reasons must contain" in issue for issue in issues)
    assert "governanceProfile.override must be null when source is automatic" in issues

    override = {
        "governanceProfile": {
            "selected": "lite",
            "source": "human_override",
            "reasons": ["Bounded exception"],
            "override": {
                "approvalEvidence": "",
                "reason": "",
                "risks": [],
                "notRunChecks": [""],
                "workItemId": "",
            },
        }
    }
    issues = ai_check_work_item.validate_governance_profile(override)
    assert any("approvalEvidence" in issue for issue in issues)
    assert any("override.reason" in issue for issue in issues)
    assert any("override.risks" in issue for issue in issues)
    assert any("override.notRunChecks" in issue for issue in issues)
    assert any("requires expiresAt or workItemOnly true" in issue for issue in issues)
    assert any("override.workItemId" in issue for issue in issues)


def test_optional_readiness_reports_each_malformed_evidence_group():
    issues = ai_check_work_item.validate_optional_readiness(
        {
            "contractVersion": 2,
            "riskAssessment": {"level": "urgent", "riskTypes": [""], "reason": ""},
            "agentCapability": {
                "canImplement": "yes",
                "canVerify": None,
                "needsHumanDecision": 0,
                "blockedReason": False,
            },
            "executionDecision": {"status": "run", "reason": ""},
            "archiveIndexRepair": "no",
            "preReviewWarnings": [""],
            "checkpointPolicy": {
                "requiredBeforeFinish": "yes",
                "requiredStages": [""],
                "reason": "",
            },
            "scenarioCoverage": [],
        }
    )
    expected_fragments = (
        "riskAssessment.level",
        "riskAssessment.riskTypes",
        "riskAssessment.reason",
        "agentCapability.canImplement",
        "agentCapability.canVerify",
        "agentCapability.needsHumanDecision",
        "agentCapability.blockedReason",
        "executionDecision.status",
        "executionDecision.reason",
        "archiveIndexRepair",
        "preReviewWarnings",
        "checkpointPolicy.requiredBeforeFinish",
        "checkpointPolicy.requiredStages",
        "checkpointPolicy.reason",
    )
    for fragment in expected_fragments:
        assert any(fragment in issue for issue in issues)


def test_baseline_and_approval_validation_rejects_incomplete_records():
    issues = ai_check_work_item.validate_baseline_and_approvals(
        {
            "contractVersion": 2,
            "workItemId": "task",
            "baseCommit": "short",
            "baselineDirtyPaths": ["file", {"path": "", "status": "", "fingerprint": ""}],
            "adoptionBootstrapPaths": [],
            "destructiveChangePolicy": {
                "allowed": False,
                "requiresHumanApproval": "yes",
                "allowPatterns": ["src/**"],
            },
            "restrictedWriteApproval": {"approved": True, "approvedBy": "", "reason": ""},
        }
    )
    expected_fragments = (
        "baseCommit",
        "baselineDirtyPaths[0]",
        "baselineDirtyPaths[1].path",
        "adoptionBootstrapPaths is only allowed",
        "adoptionBootstrapPaths must be a non-empty list",
        "destructiveChangePolicy.requiresHumanApproval",
        "allowPatterns require allowed true",
        "approved restrictedWriteApproval",
    )
    for fragment in expected_fragments:
        assert any(fragment in issue for issue in issues)


def test_intent_validation_rejects_unknown_empty_and_malformed_fields():
    assert ai_check_work_item.validate_intent({"intent": []}) == ["intent must be an object"]

    issues = ai_check_work_item.validate_intent(
        {
            "intent": {
                "unknown": "value",
                "problem": "",
                "constraints": ["valid", ""],
                "nonGoals": "none",
            }
        }
    )
    assert "intent.unknown is not a recognized field" in issues
    assert "intent.problem must be a non-empty string when provided" in issues
    assert "intent.constraints must be a list of non-empty strings when provided" in issues
    assert "intent.nonGoals must be a list of non-empty strings when provided" in issues


def test_raw_request_validation_rejects_invalid_exemption_and_source():
    contract = {
        "contractVersion": 2,
        "mode": "code",
        "scope": [".ai/work-items/active/task.contract.json"],
        "riskAssessment": {"level": "high"},
        "rawRequestExemption": {
            "exemption": "internal_governance",
            "policyRef": "raw-request-exemptions.v1",
            "triggerRef": "internal-governance",
            "applicability": ["repository"],
            "approvedBy": "policy",
        },
    }
    issues = ai_check_work_item.validate_raw_request_requirement(contract)
    assert any("cannot exempt high-risk work" in issue for issue in issues)

    contract["rawUserRequest"] = " "
    contract["rawRequestSource"] = {
        "type": "chat",
        "reference": "",
        "capturedAt": "",
        "digest": "",
    }
    issues = ai_check_work_item.validate_raw_request_requirement(contract)
    assert "rawUserRequest must be a non-empty string" in issues
    assert any("rawRequestSource.type" in issue for issue in issues)
    for field in ("reference", "capturedAt", "digest"):
        assert any(f"rawRequestSource.{field}" in issue for issue in issues)
