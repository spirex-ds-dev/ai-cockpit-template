from copy import deepcopy

from scripts.ai_uninstall_proposal import build_proposal, proposal_digest, validate_proposal


def _facts():
    return {
        "schemaVersion": 1,
        "state": "ready",
        "sessionId": "s-1",
        "installationId": "install-1",
        "repositoryIdentity": "sha256:repo",
        "runtimeFiles": [
            {"path": "runtime.py", "digest": "a" * 64, "ownership": "template", "type": "file"}
        ],
        "preservePaths": ["project.py", ".ai/work-items/archive"],
    }


def test_preserve_evidence_proposal_is_digest_bound_and_read_only():
    proposal = build_proposal(_facts(), "preserve-evidence")
    assert proposal["state"] == "needs_human_confirmation"
    assert proposal["writes"] == []
    assert proposal["deletionList"] == ["runtime.py"]
    assert proposal["proposalDigest"] == proposal_digest(proposal)
    assert validate_proposal(proposal) == []


def test_preserve_evidence_retains_governance_and_project_files():
    proposal = build_proposal(_facts())
    assert ".ai/work-items/archive" in proposal["preservePaths"]
    assert proposal["deletionList"] == ["runtime.py"]


def test_drift_or_unknown_ownership_blocks():
    assert build_proposal({**_facts(), "drift": True})["state"] == "blocked"
    assert build_proposal({**_facts(), "unknownOwnership": ["x"]})["state"] == "blocked"


def test_disable_and_purge_remain_separate_non_executable_boundaries():
    assert build_proposal(_facts(), "disable")["reason"] == "use_disable_entrypoint"
    purge = build_proposal(_facts(), "purge")
    assert purge["state"] == "blocked"
    assert purge["reason"] == "purge_not_supported_by_uninstall_executor"


def test_every_bound_proposal_field_is_covered_by_the_digest():
    proposal = build_proposal(_facts())
    mutations = [
        ("repositoryIdentity", "sha256:other"),
        ("installationId", "install-2"),
        ("sessionId", "s-2"),
        ("deletionList", ["other.py"]),
        ("preservePaths", []),
        ("receiptPath", "receipt.json"),
    ]
    for field, value in mutations:
        changed = deepcopy(proposal)
        changed[field] = value
        assert "proposal_digest_mismatch" in validate_proposal(changed), field
