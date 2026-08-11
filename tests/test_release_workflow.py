from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def test_release_workflow_allows_an_allow_list_compatible_runner_override():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: ${{ vars.AI_COCKPIT_RELEASE_RUNNER || 'ubuntu-latest' }}" in workflow


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


def test_release_workflow_requires_same_source_nonpublishing_rehearsal():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "rehearsal:" in workflow
    assert "rehearsal_run_id:" in workflow
    assert "Validate successful exact-source rehearsal" in workflow
    assert "Upload exact-source rehearsal receipt" in workflow
    assert "name: release-rehearsal" in workflow
    assert '--name "release-rehearsal"' in workflow

    rehearsal_validation = workflow.index("Validate successful exact-source rehearsal")
    tag = workflow.index("Create exact-SHA tag and Draft GitHub Release")
    publish = workflow.index("Publish verified Draft Release")
    assert rehearsal_validation < tag < publish

    tag_step = workflow[tag : workflow.index("Verify Draft tag target and release asset subjects")]
    publish_step = workflow[publish:]
    assert "if: ${{ !inputs.rehearsal }}" in tag_step
    assert "if: ${{ !inputs.rehearsal }}" in publish_step


def test_actual_release_reuses_only_a_complete_exact_source_rehearsal_receipt():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    receipt_validation = workflow.index("Validate successful exact-source rehearsal")
    reuse = workflow.index("Reuse strict smoke verification from exact-source rehearsal receipt")
    strict_smoke = workflow.index("Dispatch strict smoke verification for verified source commit")
    tag = workflow.index("Create exact-SHA tag and Draft GitHub Release")

    assert receipt_validation < reuse < strict_smoke < tag
    assert "if: ${{ !inputs.rehearsal }}" in workflow[reuse:strict_smoke]
    assert (
        "if: ${{ inputs.rehearsal }}"
        in workflow[strict_smoke : workflow.index("Record exact-source rehearsal receipt")]
    )
    for field in (
        "treeDigest",
        "strictSmokeRunId",
        "strictSmokeEvidenceDigest",
        "requiredJobNames",
        "testCollection",
        "coverage",
        "artifactDigests",
        "validUntil",
    ):
        assert field in workflow[receipt_validation:tag]


def test_rehearsal_receipt_reuse_rejects_incomplete_or_mismatched_evidence_before_tagging():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    reuse = workflow.index("Reuse strict smoke verification from exact-source rehearsal receipt")
    tag = workflow.index("Create exact-SHA tag and Draft GitHub Release")
    receipt = workflow.index("Record exact-source rehearsal receipt")
    validation = workflow[reuse:tag]
    receipt_creation = workflow[receipt : workflow.index("Upload exact-source rehearsal receipt")]

    assert "gh run view" in validation
    assert 'conclusion == "success"' in validation
    assert 'workflowName == "smoke"' in validation
    assert "release_verification" in validation
    assert "validUntil" in validation
    assert "sha256sum" in validation
    assert 'git rev-parse "${SOURCE_COMMIT}^{tree}"' in receipt_creation
    assert "quality-diagnostics" in receipt_creation


def test_rehearsal_guards_every_public_release_side_effect():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    public_steps = (
        "Create exact-SHA tag and Draft GitHub Release",
        "Verify Draft tag target and release asset subjects",
        "Verify tagged Quick Install contract before publication",
        "Publish verified Draft Release",
    )

    for name in public_steps:
        start = workflow.index(f"- name: {name}")
        end = workflow.find("\n      - name:", start + 1)
        step = workflow[start:] if end == -1 else workflow[start:end]
        assert "if: ${{ !inputs.rehearsal }}" in step


def test_draft_quick_install_verification_uses_authenticated_asset_api_after_upload():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    create = workflow.index("Create exact-SHA tag and Draft GitHub Release")
    verify = workflow.index("Verify tagged Quick Install contract before publication")
    publish = workflow.index("Publish verified Draft Release")
    draft_upload = workflow[create:verify]
    quick_install = workflow[verify:publish]

    assert 'cp release.json "$RUNNER_TEMP/release.json"' in draft_upload
    assert (
        'cp "$RUNNER_TEMP/release-projection.json" "$RUNNER_TEMP/release.json"' not in draft_upload
    )
    assert '"$RUNNER_TEMP/release.json#release.json"' in draft_upload
    assert "gh release download" not in quick_install
    assert (
        'gh release view "$RELEASE_TAG" --repo "$GITHUB_REPOSITORY" --json assets' in quick_install
    )
    assert '.apiUrl | split("/") | last' in quick_install
    assert '[[ "$asset_id" =~ ^[0-9]+$ ]]' in quick_install
    assert 'test "$asset_id" =~' not in quick_install
    assert '"repos/${GITHUB_REPOSITORY}/releases/assets/${asset_id}"' in quick_install
    assert "download_draft_asset release.json" in quick_install


def test_release_archive_projects_and_compares_the_runtime_digest_manifest():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    evidence = workflow.index("Generate source-bound release evidence")
    verification = workflow.index("Verify source-bound release evidence subjects")
    segment = workflow[evidence:verification]

    assert 'cp "$RUNNER_TEMP/release-evidence/release-digests.json"' in segment
    assert '"$GITHUB_WORKSPACE/.ai/cockpit/release-digests.json"' in segment
    assert "--use-worktree" in segment
    assert '"ai-cockpit/.ai/cockpit/release-digests.json"' in segment
    assert 'cmp -s "$RUNNER_TEMP/archive-release-digests.json"' in segment


def test_published_projection_is_not_promoted_in_repository():
    import json

    published = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
    candidate = json.loads((ROOT / "next-release.json").read_text(encoding="utf-8"))

    assert published["releaseTag"] == "v0.5.56"
    assert (
        published["releaseArchive"]["sha256"]
        == "aff7fd8790d4b2dd632dbb72d56a4a5a6ff9c98a97e0d609470f4c803489f2bb"
    )
    assert candidate["releaseTag"] == "v0.5.57"
    assert candidate["releaseTag"] != published["releaseTag"]
    assert candidate["releaseTag"].startswith("v")
    assert candidate["basedOnReleaseTag"] == published["releaseTag"]
    assert candidate["published"] is False


def test_release_preflight_runs_before_runtime_projection():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    runtime_freeze = workflow.index("name: Materialize exact-source runtime release freeze")
    preflight = workflow.index("name: Validate exact-source release preflight after runtime freeze")
    projection = workflow.index("name: Create source-bound runtime release projection")
    assert runtime_freeze < preflight < projection
    assert 'make finalize-release-freeze-runtime RUNTIME_SOURCE_COMMIT="$SOURCE_COMMIT"' in workflow
    assert (
        'make check-release-preflight RELEASE_PREFLIGHT_SOURCE_COMMIT="$SOURCE_COMMIT"'
        in workflow[preflight:projection]
    )


def test_lifecycle_guide_keeps_premerge_metadata_and_runtime_preflight_separate():
    lifecycle = (ROOT / "docs" / "reference" / "ai-cockpit-work-item-lifecycle.md").read_text(
        encoding="utf-8"
    )

    assert "Do not run `make check-release-preflight` on the premerge metadata commit." in lifecycle
    assert "The gate runs only after runtime" in lifecycle
    assert "exact merged `SOURCE_COMMIT`" in lifecycle
    assert "make check-release-readiness" in lifecycle
    assert "successful same-SHA rehearsal" in lifecycle
    assert "not another committed freeze" in lifecycle


def test_distribution_guides_distinguish_rehearsal_from_publication():
    english = (ROOT / "docs" / "reference" / "distribution.md").read_text(encoding="utf-8")
    japanese = (ROOT / "docs" / "reference" / "distribution.ja.md").read_text(encoding="utf-8")

    assert "rehearsal" in english.lower()
    assert "not a published release" in english.lower()
    assert "リハーサル" in japanese
    assert "公開済みリリースではありません" in japanese
