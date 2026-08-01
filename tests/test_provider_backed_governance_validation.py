"""Focused regression tests for GitHub provider-receipt boundaries."""

from __future__ import annotations

import copy

import provider_backed_governance_validation as validation
import pytest

SHA = "0123456789abcdef0123456789abcdef01234567"
MERGE_SHA = "fedcba9876543210fedcba9876543210fedcba98"


class StaticClient:
    """Offline API fixture; the production command always uses GitHubClient."""

    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses

    def get(self, path: str) -> object:
        response = self.responses[path]
        if isinstance(response, Exception):
            raise response
        return copy.deepcopy(response)


def responses() -> dict[str, object]:
    repository = "org/repo"
    return {
        f"repos/{repository}/pulls/7": {
            "id": 70,
            "merged": True,
            "merge_commit_sha": MERGE_SHA,
            "head": {"sha": SHA, "ref": "codex/closed"},
        },
        f"repos/{repository}/branches/main/protection": validation.ProviderUnavailable(
            "HTTP 404: Branch not protected"
        ),
        f"repos/{repository}/contents/CODEOWNERS": validation.ProviderUnavailable(
            "HTTP 404: Not Found"
        ),
        f"repos/{repository}/pulls/7/reviews": [],
        f"repos/{repository}/commits/{SHA}/check-runs": {
            "check_runs": [{"id": 1, "conclusion": "success"}]
        },
        f"repos/{repository}/git/ref/heads/codex/closed": validation.ProviderUnavailable(
            "HTTP 404: Not Found"
        ),
        f"repos/{repository}/git/ref/tags/v1.2.3": {"object": {"type": "commit", "sha": SHA}},
        f"repos/{repository}/releases/tags/v1.2.3": {
            "id": 90,
            "assets": [{"id": 91, "digest": "sha256:abc"}],
        },
        "user": {"id": 42, "login": "governance-user"},
    }


def facts(receipt: dict) -> dict[str, dict]:
    return {fact["capability"]: fact for fact in receipt["facts"]}


def test_receipt_records_a_real_route_without_upgrading_missing_configuration() -> None:
    receipt = validation.collect_receipt(
        StaticClient(responses()), repository="org/repo", pr_number=7, tag="v1.2.3"
    )
    result = facts(receipt)

    assert result["pr_creation"]["state"] == "provider_verified"
    assert result["merge_sha"]["sha"] == MERGE_SHA
    assert result["remote_branch_cleanup"]["state"] == "provider_verified"
    assert result["branch_protection"]["state"] == "not_run"
    assert result["required_checks"]["state"] == "not_claimed"
    assert result["codeowners"]["state"] == "not_run"
    assert result["review_approval"]["state"] == "not_claimed"
    assert result["release_asset"]["state"] == "provider_verified"
    assert result["release_asset"]["assetDigest"] == "sha256:abc"


def test_local_lookalikes_are_not_provider_evidence() -> None:
    receipt = validation.collect_receipt(
        StaticClient(responses()), repository="org/repo", pr_number=7, tag="v1.2.3"
    )
    result = facts(receipt)

    assert "git username" not in result["provider_identity"].get("resourceId", "")
    assert result["review_approval"]["state"] != "provider_verified"  # PR prose is not approval.
    assert result["pr_creation"]["resourceId"].startswith("pull_request:")  # branch is not a PR.
    assert result["tag"]["resourceId"].startswith("git_ref:tags/")
    assert result["release"]["resourceId"].startswith("release:")  # tag is not a release.
    assert result["release_asset"]["resourceId"].startswith(
        "release_asset:"
    )  # page is not digest evidence.


def test_provider_verified_facts_require_provider_binding_and_applicable_sha() -> None:
    receipt = validation.collect_receipt(
        StaticClient(responses()), repository="org/repo", pr_number=7, tag="v1.2.3"
    )
    malformed = copy.deepcopy(receipt)
    facts(malformed)["merge_sha"].pop("sha")

    with pytest.raises(ValueError, match="merge_sha requires applicable SHA"):
        validation.validate_receipt(malformed)

    malformed = copy.deepcopy(receipt)
    facts(malformed)["provider_identity"].pop("resourceId")
    with pytest.raises(ValueError, match="provider_identity requires provider resource ID"):
        validation.validate_receipt(malformed)

    malformed = copy.deepcopy(receipt)
    facts(malformed)["release_asset"].pop("assetDigest")
    with pytest.raises(ValueError, match="release_asset requires provider asset digest"):
        validation.validate_receipt(malformed)


def test_release_without_asset_digest_is_not_a_release_asset_claim() -> None:
    fixture = responses()
    fixture["repos/org/repo/releases/tags/v1.2.3"] = {
        "id": 90,
        "assets": [{"id": 91, "name": "asset.tgz"}],
    }

    result = facts(
        validation.collect_receipt(
            StaticClient(fixture), repository="org/repo", pr_number=7, tag="v1.2.3"
        )
    )

    assert result["release"]["state"] == "provider_verified"
    assert result["release_asset"]["state"] == "not_claimed"


def test_exactly_one_fact_is_required_for_every_capability() -> None:
    receipt = validation.collect_receipt(
        StaticClient(responses()), repository="org/repo", pr_number=7, tag="v1.2.3"
    )
    receipt["facts"].pop()

    with pytest.raises(ValueError, match="exactly one fact"):
        validation.validate_receipt(receipt)
