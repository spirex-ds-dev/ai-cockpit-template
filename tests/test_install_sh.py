import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_install_help_identifies_canonical_repository():
    script = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert "AI_COCKPIT_TEMPLATE_REPO=spirex-ds-dev/ai-cockpit-template" in script


def test_remote_archive_url_supports_branch_tag_and_sha_refs():
    script = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert 'git clone --depth 1 --branch "$REF" --single-branch "$URL" "$SOURCE"' in script
    assert 'python3 "$SOURCE/scripts/verify_quick_install_release.py"' in script
    assert 'EXPECTED_SHA256="${AI_COCKPIT_TEMPLATE_SHA256:-}"' in script
    assert "http://*|https://*|git@*)" in script
    assert 'URL="$REPO"' in script
    assert "verify_quick_install_release.py" in script
    assert "release.json remains authoritative" in script
    assert "release-digests.json" in script
    assert "AI_COCKPIT_TEMPLATE_RELEASE_DIGESTS_URL" in script
    assert "public release-digests.json does not match requested release tag" in script
    assert 'public_release_asset_url(repository, ref, "release-digests.json")' in script


def test_quick_install_uses_candidate_tag_without_reading_candidate_metadata_at_runtime():
    script = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert "next-release.json" not in script
    candidate_tag = json.loads((ROOT / "next-release.json").read_text(encoding="utf-8"))[
        "releaseTag"
    ]
    assert f'REF="${{AI_COCKPIT_TEMPLATE_REF:-{candidate_tag}}}"' in script
