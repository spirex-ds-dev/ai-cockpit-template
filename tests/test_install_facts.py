import json
from pathlib import Path

import pytest
from ai_install_facts import (
    InstallFactsError,
    canonical_json,
    validate_fact_bundle,
    write_fact_bundle,
)


def make_install_tree(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / ".ai" / "cockpit").mkdir(parents=True)
    (target / ".ai" / "guards").mkdir(parents=True)
    (target / ".ai" / "cockpit").mkdir(parents=True)
    (target / ".ai" / "work-items" / "archive").mkdir(parents=True)
    (target / ".ai" / "guards" / "policy.yaml").write_text("mode: blocking\n", encoding="utf-8")
    (target / ".ai" / "cockpit" / "version.json").write_text("{}\n", encoding="utf-8")
    (target / ".ai" / "work-items" / "archive" / "history.json").write_text(
        "{}\n", encoding="utf-8"
    )
    return source, target


def test_write_fact_bundle_contains_bound_manifest_and_all_ownerships(tmp_path):
    source, target = make_install_tree(tmp_path)
    facts = write_fact_bundle(
        source=source,
        target=target,
        distribution_version={
            "distributionVersion": 2,
            "releaseVersion": "0.5.32",
            "contractSchema": 2,
        },
    )

    assert set(facts) == {
        "manifest",
        "version",
        "managedRegions",
        "rollbackBaseline",
        "releaseIdentity",
    }
    assert facts["releaseIdentity"]["sourceCommit"] is None
    manifest = facts["manifest"]
    assert manifest["installationId"]
    assert facts["version"]["manifestHash"]
    assert {item["ownership"] for item in manifest["files"]} >= {
        "shared",
        "generated",
        "historical",
    }
    assert all(item["currentDigest"] == item["installedDigest"] for item in manifest["files"])
    assert all(item["projectModified"] is False for item in manifest["files"])
    assert all(item["ownershipClass"] for item in manifest["files"])
    assert validate_fact_bundle(target)["version"] == facts["version"]


def test_tagged_release_identity_binds_tag_commit_version_and_assets(tmp_path):
    source, target = make_install_tree(tmp_path)
    identity = {
        "releaseTag": "v1.2.3",
        "releaseVersion": "1.2.3",
        "sourceCommit": "a" * 40,
        "tagTarget": "a" * 40,
        "metadataCommit": "a" * 40,
        "artifactDigests": {"install.sh": "b" * 64},
    }

    facts = write_fact_bundle(
        source=source,
        target=target,
        distribution_version={
            "distributionVersion": 2,
            "releaseVersion": "1.2.3",
            "contractSchema": 2,
        },
        release_identity=identity,
    )

    assert facts["releaseIdentity"]["releaseTag"] == "v1.2.3"
    assert facts["releaseIdentity"]["sourceCommit"] == "a" * 40
    assert facts["version"]["releaseIdentityHash"]
    assert validate_fact_bundle(target)["releaseIdentity"] == facts["releaseIdentity"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("releaseTag", "not-a-release", "semantic"),
        ("tagTarget", "c" * 40, "one matching SHA-1"),
        ("artifactDigests", {"install.sh": "not-a-digest"}, "SHA-256"),
    ],
)
def test_tagged_release_identity_rejects_inconsistent_metadata_before_fact_writes(
    tmp_path, field, value, message
):
    source, target = make_install_tree(tmp_path)
    identity = {
        "releaseTag": "v1.2.3",
        "releaseVersion": "1.2.3",
        "sourceCommit": "a" * 40,
        "tagTarget": "a" * 40,
        "metadataCommit": "a" * 40,
        "artifactDigests": {"install.sh": "b" * 64},
    }
    identity[field] = value

    with pytest.raises(InstallFactsError, match=message):
        write_fact_bundle(
            source=source,
            target=target,
            distribution_version={
                "distributionVersion": 2,
                "releaseVersion": "1.2.3",
                "contractSchema": 2,
            },
            release_identity=identity,
        )

    assert not (target / ".ai/install/manifest.json").exists()


def test_validation_reports_current_digest_and_project_modification(tmp_path):
    source, target = make_install_tree(tmp_path)
    write_fact_bundle(source=source, target=target, distribution_version={"distributionVersion": 2})
    changed = target / ".ai" / "guards" / "policy.yaml"
    changed.write_text("mode: project-change\n", encoding="utf-8")
    facts = validate_fact_bundle(target)
    item = next(
        item for item in facts["manifest"]["files"] if item["path"] == ".ai/guards/policy.yaml"
    )
    assert item["projectModified"] is True
    assert item["currentDigest"] != item["installedDigest"]


def test_fact_reads_are_deterministic_and_canonical(tmp_path):
    source, target = make_install_tree(tmp_path)
    write_fact_bundle(
        source=source,
        target=target,
        distribution_version={"distributionVersion": 2, "contractSchema": 2},
    )
    first = validate_fact_bundle(target)
    second = validate_fact_bundle(target)
    assert canonical_json(first) == canonical_json(second)


def test_manifest_preserves_readmes_and_excludes_transient_install_lock(tmp_path):
    source, target = make_install_tree(tmp_path)
    (source / "README.md").write_text("template\n", encoding="utf-8")
    (target / "README.md").write_text("adopter\n", encoding="utf-8")
    lock = target / ".ai" / "cockpit" / ".install.lock"
    lock.write_text("transient\n", encoding="utf-8")

    facts = write_fact_bundle(
        source=source,
        target=target,
        distribution_version={"distributionVersion": 2, "contractSchema": 2},
    )

    entries = {item["path"]: item for item in facts["manifest"]["files"]}
    assert entries["README.md"]["ownership"] == "project"
    assert ".ai/cockpit/.install.lock" not in entries


@pytest.mark.parametrize("mutation", ["missing", "malformed", "tampered"])
def test_invalid_fact_bundle_fails_closed(tmp_path, mutation):
    source, target = make_install_tree(tmp_path)
    write_fact_bundle(
        source=source,
        target=target,
        distribution_version={"distributionVersion": 2, "contractSchema": 2},
    )
    manifest_path = target / ".ai" / "install" / "manifest.json"
    if mutation == "missing":
        manifest_path.unlink()
    elif mutation == "malformed":
        manifest_path.write_text("not json\n", encoding="utf-8")
    else:
        entry = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry["files"][0]["installedDigest"] = "0" * 64
        manifest_path.write_bytes(canonical_json(entry))
    with pytest.raises(InstallFactsError):
        validate_fact_bundle(target)
