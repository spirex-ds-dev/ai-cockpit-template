import hashlib
import json
from pathlib import Path

import pytest
import sync_published_release_projection as projection

SOURCE_COMMIT = "a" * 40


def write_projection_root(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    (root / ".ai" / "cockpit").mkdir(parents=True)
    (root / "release.json").write_text('{"releaseTag":"v0.5.55"}\n', encoding="utf-8")
    (root / "next-release.json").write_text(
        json.dumps(
            {
                "releaseTag": "v0.5.56",
                "releaseState": "candidate",
                "published": False,
                "basedOnReleaseTag": "v0.5.55",
                "supplyChain": {"requirementsLockDigest": "b" * 64},
            }
        ),
        encoding="utf-8",
    )
    (root / "release-state.json").write_text(
        json.dumps(
            {
                "state": "candidate_prepared",
                "releaseTag": "v0.5.56",
                "previousRelease": "v0.5.55",
                "reservedTags": ["v0.5.55"],
                "unavailableTags": [],
                "metadataDigests": {"published": "0" * 64, "candidate": "1" * 64},
            }
        ),
        encoding="utf-8",
    )
    (root / ".ai" / "cockpit" / "version.json").write_text(
        '{"releaseVersion":"0.5.56"}\n', encoding="utf-8"
    )
    (root / "install.sh").write_text(
        'REF="${AI_COCKPIT_TEMPLATE_REF:-v0.5.56}"\n  AI_COCKPIT_TEMPLATE_REF=v0.5.56\n',
        encoding="utf-8",
    )
    return root


def published_assets() -> tuple[bytes, bytes]:
    release = {
        "releaseTag": "v0.5.56",
        "releaseArchive": {"assetName": "v0.5.56.tar.gz", "sha256": "c" * 64},
    }
    digests = {
        "releaseTag": "v0.5.56",
        "sourceCommit": SOURCE_COMMIT,
        "tagTarget": SOURCE_COMMIT,
        "metadataCommit": SOURCE_COMMIT,
    }
    return (
        (json.dumps(release, sort_keys=True) + "\n").encode(),
        (json.dumps(digests, sort_keys=True) + "\n").encode(),
    )


def test_sync_promotes_verified_public_projection_and_advances_candidate(tmp_path):
    root = write_projection_root(tmp_path)
    release_bytes, digest_bytes = published_assets()

    projection.synchronize_projection(
        root,
        release_tag="v0.5.56",
        source_commit=SOURCE_COMMIT,
        release_json_bytes=release_bytes,
        release_digests_bytes=digest_bytes,
    )

    assert (root / "release.json").read_bytes() == release_bytes
    assert (root / ".ai" / "cockpit" / "release-digests.json").read_bytes() == digest_bytes
    assert json.loads((root / "next-release.json").read_text()) == {
        "releaseTag": "v0.5.57",
        "releaseState": "candidate",
        "published": False,
        "basedOnReleaseTag": "v0.5.56",
        "supplyChain": {"requirementsLockDigest": "b" * 64},
    }
    assert (
        json.loads((root / ".ai" / "cockpit" / "version.json").read_text())["releaseVersion"]
        == "0.5.57"
    )


def test_sync_advances_installer_default_with_the_candidate_projection(tmp_path):
    root = write_projection_root(tmp_path)
    release_bytes, digest_bytes = published_assets()

    projection.synchronize_projection(
        root,
        release_tag="v0.5.56",
        source_commit=SOURCE_COMMIT,
        release_json_bytes=release_bytes,
        release_digests_bytes=digest_bytes,
    )

    installer = (root / "install.sh").read_text(encoding="utf-8")
    assert 'REF="${AI_COCKPIT_TEMPLATE_REF:-v0.5.57}"' in installer
    assert "AI_COCKPIT_TEMPLATE_REF=v0.5.57" in installer


def test_sync_records_the_verified_historical_release_status(tmp_path):
    root = write_projection_root(tmp_path)
    release_bytes, digest_bytes = published_assets()

    projection.synchronize_projection(
        root,
        release_tag="v0.5.56",
        source_commit=SOURCE_COMMIT,
        release_json_bytes=release_bytes,
        release_digests_bytes=digest_bytes,
        unavailable_entry={
            "kind": "stable_release_invalid_public_distribution",
            "reason": "full HTTPS installer hydration failed before target writes",
            "evidence": "https://example.test/releases/tag/v0.5.56",
        },
    )

    state = json.loads((root / "release-state.json").read_text())
    assert state["unavailableTags"][-1] == {
        "tag": "v0.5.56",
        "kind": "stable_release_invalid_public_distribution",
        "reason": "full HTTPS installer hydration failed before target writes",
        "evidence": "https://example.test/releases/tag/v0.5.56",
    }


def test_sync_rejects_mismatched_asset_identity_without_writing(tmp_path):
    root = write_projection_root(tmp_path)
    release_bytes, digest_bytes = published_assets()
    before = (root / "release.json").read_bytes()
    bad_digests = digest_bytes.replace(SOURCE_COMMIT.encode(), ("d" * 40).encode())

    with pytest.raises(projection.ProjectionSyncError, match="sourceCommit"):
        projection.synchronize_projection(
            root,
            release_tag="v0.5.56",
            source_commit=SOURCE_COMMIT,
            release_json_bytes=release_bytes,
            release_digests_bytes=bad_digests,
        )

    assert (root / "release.json").read_bytes() == before


def test_cli_rejects_provider_asset_digest_mismatch_without_writing(tmp_path, capsys):
    root = write_projection_root(tmp_path)
    release_bytes, digest_bytes = published_assets()
    release_path = tmp_path / "release.json"
    digests_path = tmp_path / "release-digests.json"
    release_path.write_bytes(release_bytes)
    digests_path.write_bytes(digest_bytes)
    before = (root / "release.json").read_bytes()

    result = projection.main(
        [
            "--root",
            str(root),
            "--release-tag",
            "v0.5.56",
            "--source-commit",
            SOURCE_COMMIT,
            "--release-json",
            str(release_path),
            "--release-digests",
            str(digests_path),
            "--release-json-sha256",
            "0" * 64,
            "--release-digests-sha256",
            hashlib.sha256(digest_bytes).hexdigest(),
        ]
    )

    assert result == 2
    assert "release.json asset digest mismatch" in capsys.readouterr().err
    assert (root / "release.json").read_bytes() == before
