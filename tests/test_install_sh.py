from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_remote_archive_url_supports_branch_tag_and_sha_refs():
    script = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert 'archive/$REF.tar.gz' in script
    assert 'archive/refs/heads/$REF.tar.gz' not in script
