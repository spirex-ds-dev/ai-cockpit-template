from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def test_release_workflow_projects_candidate_metadata_at_runtime():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Create source-bound runtime release projection" in workflow
    assert 'git show "${SOURCE_COMMIT}:next-release.json"' in workflow
    assert '"$RUNNER_TEMP/release-projection.json"' in workflow
    assert 'cp "$RUNNER_TEMP/release-projection.json" "$GITHUB_WORKSPACE/release.json"' in workflow
    assert 'assert candidate["releaseState"] == "candidate"' in workflow
    assert 'assert candidate["published"] is False' in workflow
    assert 'assert candidate["releaseTag"] == requested_tag' in workflow
    assert 'assert candidate["basedOnReleaseTag"] == published["releaseTag"]' in workflow


def test_published_projection_is_not_promoted_in_repository():
    import json

    published = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
    candidate = json.loads((ROOT / "next-release.json").read_text(encoding="utf-8"))

    assert published["releaseTag"] == "v0.5.42"
    assert candidate["releaseTag"] != published["releaseTag"]
    assert candidate["releaseTag"].startswith("v")
    assert candidate["basedOnReleaseTag"] == published["releaseTag"]
    assert candidate["published"] is False


def test_release_preflight_runs_before_runtime_projection():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    runtime_freeze = workflow.index("name: Materialize exact-source runtime release freeze")
    preflight = workflow.index(
        "name: Validate committed source release preflight before projection"
    )
    projection = workflow.index("name: Create source-bound runtime release projection")
    assert runtime_freeze < preflight < projection
    assert 'make finalize-release-freeze-runtime RUNTIME_SOURCE_COMMIT="$SOURCE_COMMIT"' in workflow
    assert (
        'make check-release-preflight RELEASE_PREFLIGHT_SOURCE_COMMIT="$SOURCE_COMMIT"'
        in workflow[preflight:projection]
    )
