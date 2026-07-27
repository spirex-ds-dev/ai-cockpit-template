from scripts.determine_quality_scope import determine


def test_docs_only_change_is_fast():
    assert determine(["docs/operations/quality-gates.md"])["scope"] == "fast"


def test_code_and_governance_changes_are_full():
    assert determine(["scripts/example.py"])["scope"] == "full"
    assert determine([".ai/quality/gates.yaml"])["scope"] == "full"


def test_release_paths_require_release_scope():
    result = determine(["release.json"])
    assert result["scope"] == "release"
    assert result["releasePreparation"] is True


def test_unknown_or_mixed_scope_defaults_full():
    assert determine(["unknown.txt", "docs/guide.md"])["scope"] == "full"
