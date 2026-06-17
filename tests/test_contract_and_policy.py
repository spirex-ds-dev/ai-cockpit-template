from pathlib import Path

import ai_check_guards
import ai_check_agent_risk
import ai_check_scope
import ai_check_work_item


def valid_contract():
    return {
        "contractVersion": 1,
        "workItemId": "task",
        "mode": "code",
        "title": "Task",
        "baseCommit": "1234567",
        "baselineDirtyPaths": [],
        "scope": ["scripts/**", "tests/**"],
        "outOfScope": [],
        "sources": ["spec"],
        "unknowns": [],
        "notCodable": False,
        "acceptance": ["works"],
        "verification": [{"command": "python3 -m pytest", "required": True}],
        "destructiveChangePolicy": {"allowed": False, "requiresHumanApproval": True, "allowPatterns": []},
        "rollbackNote": "revert",
    }


def test_destructive_allow_patterns_require_policy_and_approval():
    contract = valid_contract()
    contract["destructiveChangePolicy"]["allowPatterns"] = ["outside/**"]
    issues = ai_check_work_item.validate_contract(contract)
    assert "destructiveChangePolicy.allowPatterns require allowed true" in issues

    contract["destructiveChangePolicy"].update({"allowed": True, "approvalEvidence": {"approved": False}})
    issues = ai_check_work_item.validate_contract(contract)
    assert "destructive changes require approvalEvidence.approved true" in issues


def test_restricted_guard_is_hard_without_approval(tmp_path, monkeypatch):
    ownership = tmp_path / "ownership.yaml"
    ownership.write_text('policy/**:\n  aiWrite: restricted\n  reason: protected\n', encoding="utf-8")
    boundary = tmp_path / "boundary.yaml"
    boundary.write_text("", encoding="utf-8")
    monkeypatch.setattr(ai_check_guards, "OWNERSHIP", ownership)
    monkeypatch.setattr(ai_check_guards, "BOUNDARY", boundary)

    assert ai_check_guards.detect(["policy/rule.yaml"])[0].severity == "error"
    assert ai_check_guards.detect(["policy/rule.yaml"], restricted_approved=True)[0].severity == "warning"


def test_dependency_scope_rules_are_parsed(tmp_path):
    policy = tmp_path / "scope.yaml"
    policy.write_text('dependencyScopeRules:\n  "scripts/ai_*.py":\n    - "tests/**"\n', encoding="utf-8")
    lists = ai_check_scope.simple_yaml_lists(policy)
    assert lists["dependencyScopeRules.scripts/ai_*.py"] == ["tests/**"]


def test_stale_checkpoint_hash_is_rejected():
    contract = valid_contract()
    contract["checkpointPolicy"] = {"requiredBeforeFinish": True, "requiredStages": ["before_finish"]}
    summary = {
        "checkpointEvidence": [{
            "stage": "before_finish", "recorded": True, "contractHash": "old",
            "acceptanceCount": 1, "unknownCount": 0, "requiredChecks": 1, "requiredChecksPassed": 0,
        }],
        "verification": [],
    }
    issues = ai_check_agent_risk.validate_agent_risks(contract, summary, expected_contract_hash="new")
    assert "checkpointEvidence[before_finish] contractHash is stale" in issues
