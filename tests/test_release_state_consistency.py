import hashlib
import json

from scripts import check_release_state_consistency


def write_metadata(tmp_path, *, state=None, published=None, candidate=None):
    published = published or {
        "releaseTag": "v0.5.33",
        "releaseEvidenceAuthority": "release-assets-v1",
        "publicContract": {},
        "capabilities": {},
        "supplyChain": {},
    }
    candidate = candidate or {
        "releaseTag": "v0.5.34",
        "releaseState": "candidate",
        "published": False,
        "basedOnReleaseTag": "v0.5.33",
        "releaseEvidenceAuthority": "release-assets-v1",
        "publicContract": {},
        "capabilities": {},
        "supplyChain": {},
    }
    (tmp_path / "release.json").write_text(json.dumps(published), encoding="utf-8")
    (tmp_path / "next-release.json").write_text(json.dumps(candidate), encoding="utf-8")
    state = state or {
        "schemaVersion": 1,
        "canonical": True,
        "projections": {"published": "release.json", "candidate": "next-release.json"},
        "state": "candidate_prepared",
        "releaseTag": "v0.5.34",
        "sourceBinding": "deferred_to_release_finalization",
        "sourceCommit": None,
        "previousRelease": "v0.5.33",
        "reservedTags": [],
        "unavailableTags": [],
        "evidenceStatus": "pending_provider_assets",
        "evidenceBundleDigest": None,
    }
    state["metadataDigests"] = {
        "published": hashlib.sha256((tmp_path / "release.json").read_bytes()).hexdigest(),
        "candidate": hashlib.sha256((tmp_path / "next-release.json").read_bytes()).hexdigest(),
    }
    (tmp_path / "release-state.json").write_text(json.dumps(state), encoding="utf-8")


def test_consistent_canonical_state_passes(tmp_path):
    write_metadata(tmp_path)
    assert check_release_state_consistency.check_repository(tmp_path) == []


def test_previous_release_and_candidate_conflicts_are_rejected(tmp_path):
    write_metadata(
        tmp_path,
        state={
            "schemaVersion": 1,
            "canonical": True,
            "projections": {"published": "release.json", "candidate": "next-release.json"},
            "state": "candidate_prepared",
            "releaseTag": "v0.5.35",
            "sourceCommit": "not-a-sha",
            "sourceBinding": "deferred_to_release_finalization",
            "previousRelease": "v0.5.34",
            "reservedTags": [],
            "unavailableTags": [],
            "evidenceStatus": "pending_provider_assets",
            "evidenceBundleDigest": None,
        },
    )
    issues = check_release_state_consistency.check_repository(tmp_path)
    assert any("previousRelease" in issue for issue in issues)
    assert any("candidate releaseTag" in issue for issue in issues)
    assert any("sourceCommit" in issue for issue in issues)


def test_duplicate_candidate_and_digest_drift_are_rejected(tmp_path):
    candidate = {
        "releaseTag": "v0.5.33",
        "releaseState": "candidate",
        "published": False,
        "basedOnReleaseTag": "v0.5.33",
        "releaseEvidenceAuthority": "release-assets-v1",
        "publicContract": {},
        "capabilities": {},
        "supplyChain": {},
    }
    write_metadata(tmp_path, candidate=candidate)
    state = json.loads((tmp_path / "release-state.json").read_text(encoding="utf-8"))
    state["metadataDigests"]["candidate"] = "0" * 64
    (tmp_path / "release-state.json").write_text(json.dumps(state), encoding="utf-8")
    issues = check_release_state_consistency.check_repository(tmp_path)
    assert any("published and candidate tags must be distinct" in issue for issue in issues)
    assert any("metadata digest" in issue for issue in issues)


def test_verified_state_rejects_placeholder_and_accepts_real_digest(tmp_path):
    write_metadata(
        tmp_path,
        state={
            "schemaVersion": 1,
            "canonical": True,
            "projections": {"published": "release.json", "candidate": "next-release.json"},
            "state": "candidate_verified",
            "releaseTag": "v0.5.34",
            "sourceCommit": "c2022fa1d0c2d94ed3edf6c1d16a89260d3fd68f",
            "sourceBinding": "exact",
            "previousRelease": "v0.5.33",
            "reservedTags": [],
            "unavailableTags": [],
            "evidenceStatus": "verified",
            "evidenceBundleDigest": "pending-provider-assets",
            "ciEvidence": {
                "evidenceSource": "github_api",
                "workflowRunId": "12345",
                "headSha": "c2022fa1d0c2d94ed3edf6c1d16a89260d3fd68f",
                "requiredJobNames": ["smoke"],
                "conclusion": "success",
                "failureReasons": [],
                "artifactDigests": {"sbom.json": "a" * 64, "provenance.json": "b" * 64},
                "headToMergeRelationship": "pull_request_merge_ref",
            },
        },
    )
    issues = check_release_state_consistency.check_repository(tmp_path)
    assert any("candidate_verified" in issue for issue in issues)

    state = json.loads((tmp_path / "release-state.json").read_text(encoding="utf-8"))
    state["evidenceBundleDigest"] = "a" * 64
    (tmp_path / "release-state.json").write_text(json.dumps(state), encoding="utf-8")
    assert check_release_state_consistency.check_repository(tmp_path) == []


def test_noncanonical_state_record_is_rejected(tmp_path):
    write_metadata(tmp_path)
    state = json.loads((tmp_path / "release-state.json").read_text(encoding="utf-8"))
    state["canonical"] = False
    state["projections"]["candidate"] = "legacy-candidate.json"
    (tmp_path / "release-state.json").write_text(json.dumps(state), encoding="utf-8")
    issues = check_release_state_consistency.check_repository(tmp_path)
    assert any("canonical marker" in issue for issue in issues)
    assert any("projections" in issue for issue in issues)


def test_projections_do_not_author_the_canonical_state_machine(tmp_path):
    write_metadata(tmp_path)
    published = json.loads((tmp_path / "release.json").read_text(encoding="utf-8"))
    candidate = json.loads((tmp_path / "next-release.json").read_text(encoding="utf-8"))
    assert "state" not in published
    assert "evidenceStatus" not in published
    assert "state" not in candidate
    assert "evidenceStatus" not in candidate
    assert check_release_state_consistency.check_repository(tmp_path) == []


def test_candidate_prepared_rejects_a_false_exact_source_claim(tmp_path):
    write_metadata(tmp_path)
    state = json.loads((tmp_path / "release-state.json").read_text(encoding="utf-8"))
    state["sourceBinding"] = "exact"
    state["sourceCommit"] = "a" * 40
    (tmp_path / "release-state.json").write_text(json.dumps(state), encoding="utf-8")

    issues = check_release_state_consistency.check_repository(tmp_path)

    assert any("candidate_prepared source binding must be deferred" in issue for issue in issues)


def test_reserved_sequence_requires_exact_next_patch_and_explanations(tmp_path):
    published = {
        "releaseTag": "v0.5.42",
        "releaseEvidenceAuthority": "release-assets-v1",
        "publicContract": {},
        "capabilities": {},
        "supplyChain": {},
    }
    candidate = {
        "releaseTag": "v0.5.45",
        "releaseState": "candidate",
        "published": False,
        "basedOnReleaseTag": "v0.5.42",
        "releaseEvidenceAuthority": "release-assets-v1",
        "publicContract": {},
        "capabilities": {},
        "supplyChain": {},
    }
    state = {
        "schemaVersion": 1,
        "canonical": True,
        "projections": {"published": "release.json", "candidate": "next-release.json"},
        "state": "candidate_prepared",
        "releaseTag": "v0.5.45",
        "sourceBinding": "deferred_to_release_finalization",
        "sourceCommit": None,
        "previousRelease": "v0.5.42",
        "reservedTags": ["v0.5.43", "v0.5.44"],
        "unavailableTags": [
            {
                "tag": "v0.5.43",
                "kind": "stable_release_unverified",
                "reason": "public evidence is not a valid install authority",
                "evidence": "https://github.com/example/releases/tag/v0.5.43",
            },
            {
                "tag": "v0.5.44",
                "kind": "tag_only",
                "reason": "immutable tag exists without a stable Release",
                "evidence": "https://github.com/example/tree/v0.5.44",
            },
        ],
        "evidenceStatus": "pending_provider_assets",
        "evidenceBundleDigest": None,
    }
    write_metadata(tmp_path, state=state, published=published, candidate=candidate)
    assert check_release_state_consistency.check_repository(tmp_path) == []

    state = json.loads((tmp_path / "release-state.json").read_text(encoding="utf-8"))
    state["reservedTags"] = ["v0.5.44", "v0.5.44"]
    state["unavailableTags"] = state["unavailableTags"][:1]
    (tmp_path / "release-state.json").write_text(json.dumps(state), encoding="utf-8")
    issues = check_release_state_consistency.check_repository(tmp_path)
    assert any("reservedTags must be sorted unique" in issue for issue in issues)
    assert any("unavailableTags must explain every reserved tag" in issue for issue in issues)


def test_candidate_must_not_reuse_or_skip_reserved_version(tmp_path):
    candidate = {
        "releaseTag": "v0.5.44",
        "releaseState": "candidate",
        "published": False,
        "basedOnReleaseTag": "v0.5.42",
        "releaseEvidenceAuthority": "release-assets-v1",
        "publicContract": {},
        "capabilities": {},
        "supplyChain": {},
    }
    state = {
        "schemaVersion": 1,
        "canonical": True,
        "projections": {"published": "release.json", "candidate": "next-release.json"},
        "state": "candidate_prepared",
        "releaseTag": "v0.5.44",
        "sourceBinding": "deferred_to_release_finalization",
        "sourceCommit": None,
        "previousRelease": "v0.5.42",
        "reservedTags": ["v0.5.43", "v0.5.44"],
        "unavailableTags": [
            {"tag": tag, "kind": "tag_only", "reason": "reserved", "evidence": "https://x"}
            for tag in ("v0.5.43", "v0.5.44")
        ],
        "evidenceStatus": "pending_provider_assets",
        "evidenceBundleDigest": None,
    }
    write_metadata(tmp_path, state=state, candidate=candidate)
    issues = check_release_state_consistency.check_repository(tmp_path)

    assert any("candidate tag must not reuse a reserved tag" in issue for issue in issues)
    assert any("candidate tag must be the next patch" in issue for issue in issues)
