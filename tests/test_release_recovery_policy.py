import json

from check_release_recovery_policy import ROOT, documentation_policy_issues, recovery_policy_issues


def test_recovery_policy_requires_next_patch_after_highest_reserved_tag(tmp_path):
    (tmp_path / "release.json").write_text('{"releaseTag": "v0.5.42"}', encoding="utf-8")
    (tmp_path / "next-release.json").write_text(
        json.dumps(
            {
                "releaseTag": "v0.5.45",
                "releaseState": "candidate",
                "published": False,
                "basedOnReleaseTag": "v0.5.42",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "release-state.json").write_text(
        json.dumps({"reservedTags": ["v0.5.44"]}), encoding="utf-8"
    )

    assert recovery_policy_issues(tmp_path) == []


def test_recovery_policy_rejects_reuse_of_reserved_draft_tag(tmp_path):
    (tmp_path / "release.json").write_text('{"releaseTag": "v0.5.42"}', encoding="utf-8")
    (tmp_path / "next-release.json").write_text(
        json.dumps(
            {
                "releaseTag": "v0.5.44",
                "releaseState": "candidate",
                "published": False,
                "basedOnReleaseTag": "v0.5.42",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "release-state.json").write_text(
        json.dumps({"reservedTags": ["v0.5.44"]}), encoding="utf-8"
    )

    assert recovery_policy_issues(tmp_path) == [
        "next-release.json releaseTag 'v0.5.44' must be the next patch after highest "
        "immutable reserved tag 'v0.5.44'"
    ]


def test_recovery_policy_keeps_the_reserved_tag_boundary_documented():
    assert documentation_policy_issues(ROOT) == []
