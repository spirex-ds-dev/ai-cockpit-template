from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_compatibility_runs_on_main_pushes_and_pull_requests():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    assert "  push:\n    branches:\n      - main" in workflow
    assert "  pull_request:" in workflow
    assert "  workflow_dispatch:" in workflow


def test_smoke_hosted_measurement_dispatch_returns_a_non_authorizing_exact_commit_receipt():
    workflow = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    assert "- hosted_measurement" in workflow
    assert "Write hosted measurement receipt" in workflow
    assert "ai-cockpit-hosted-measurement-receipt" in workflow
    assert 'authorizationClaim: "not_provided_by_receipt"' in workflow
    assert "forbiddenActions" in workflow
    assert "commitSha: $commit_sha" in workflow
    assert "runUrl: $run_url" in workflow
    assert "requiredJobConclusions" in workflow
    assert "Upload hosted measurement receipt" in workflow
    assert "hosted-measurement-receipt-${{ github.run_id }}-${{ github.run_attempt }}" in workflow


def test_csharp_compatibility_uses_dependabot_setup_dotnet_600_pin():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    csharp_setup = workflow.split("uses: actions/setup-dotnet@", 1)[1].split("\n      - ", 1)[0]

    assert csharp_setup.startswith("a98b56852c35b8e3190ac28c8c2271da59106c68")
    assert "if: matrix.stack == 'csharp'" in workflow
    assert 'dotnet-version: "9.0.305"' in csharp_setup


def test_ruby_compatibility_uses_dependabot_setup_ruby_13210_pin_at_both_locations():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    old_sha = "a30dfa457ad68707b8b910ac3a244714b61c0626"
    new_sha = "95ef2b042f9d7a56d8268cba8559e2842e2ad01b"

    assert old_sha not in workflow
    assert workflow.count(f"uses: ruby/setup-ruby@{new_sha}") == 2
    assert workflow.count("if: matrix.stack == 'ruby'") >= 2
    assert 'ruby-version: "3.4.2"' in workflow
    assert "ruby-version: ruby-head" in workflow
    assert "  compatibility-gate:" in workflow
    assert "needs:\n      - shellcheck" in workflow
    assert 'test "$result" = success' in workflow
    assert workflow.count("fetch-depth: 0") == 7
    assert 'toolchain: "1.86.0"' in workflow


def test_compatibility_runs_lockfile_reproducibility_on_clean_runner():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    lockfile = workflow.split("  lockfile-reproducibility:", 1)[1].split(
        "  real-stack-quality:", 1
    )[0]
    assert 'python-version: "3.11"' in lockfile
    assert (
        "python -m pip install --disable-pip-version-check pip==25.2 pip-tools==7.6.0 typing-extensions==4.16.0"
        in lockfile
    )
    assert "make check-lockfile-reproducibility" in lockfile


def test_lockfile_input_pin_matches_python_311_compatible_lock_output():
    requirements = (ROOT / "requirements-dev.in").read_text(encoding="utf-8")
    lockfile = (ROOT / "requirements-dev.lock").read_text(encoding="utf-8")
    assert "ruff==0.16.0" in requirements
    assert "ruff==0.16.0" in lockfile
    assert "stevedore==5.9.0" in requirements
    assert "stevedore==5.9.0" in lockfile
    assert "ruff==0.15.21" not in requirements
    assert "stevedore==5.8.0" not in requirements
    assert "canonical Python 3.11" in lockfile


def test_compatibility_separates_blocking_baseline_from_latest_probes():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    gate = workflow.split("  compatibility-gate:", 1)[1].split("  compatibility-latest:", 1)[0]
    assert "needs:" in gate
    assert "real-stack-quality" in gate
    assert "extended-real-stack-quality" in gate
    assert "mobile-stack-quality" in gate
    assert "compatibility-latest:" in workflow
    assert "continue-on-error: true" not in gate
    assert "fixed compatibility baseline is the blocking release gate" in workflow
    assert 'go-version: "1.24.4"' in workflow
    assert 'toolchain: "1.86.0"' in workflow
    assert 'node-version: "24.11.1"' in workflow


def test_extended_gradle_fixtures_ignore_generated_state_before_baseline_commit():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    extended = workflow.split("  extended-real-stack-quality:", 1)[1].split(
        "  mobile-stack-quality:", 1
    )[0]
    ignore_block = (
        'if [[ "$STACK" == java || "$STACK" == kotlin ]]; then\n'
        "            printf '/.gradle/\\n/build/\\n' > .gitignore\n"
        "          fi"
    )

    assert ignore_block in extended
    assert extended.index(ignore_block) < extended.index("git add .")
    assert "src/main" not in ignore_block
    assert "src/test" not in ignore_block


def test_extended_java_fixture_declares_the_runtime_lane_required_by_the_java_preset():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    extended = workflow.split("  extended-real-stack-quality:", 1)[1].split(
        "  mobile-stack-quality:", 1
    )[0]

    assert "AI_COCKPIT_JAVA_LANE=ci-java21" in extended
    assert "AI_COCKPIT_JAVA_REQUIRED_MAJOR=21" in extended


def test_latest_compatibility_probe_uses_distinct_current_tool_commands():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    latest = workflow.split("  latest-ecosystem-probe:", 1)[1].split("  compatibility-gate:", 1)[0]
    report = workflow.split("  compatibility-latest:", 1)[1]
    assert "continue-on-error: true" in latest
    assert 'python-version: "3.x"' in latest
    assert "check-latest: true" in latest
    assert "go-version: stable" in latest
    assert "node-version: node" in latest
    assert "ruby-version: ruby-head" in latest
    assert "php-version: latest" in latest
    assert "brew install swift-format" in latest
    assert "needs:\n      - latest-ecosystem-probe" in report
    assert "fixed compatibility baseline is the blocking release gate" in report


def test_go_fixture_setup_disables_cache_until_temporary_modules_exist():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    setup_blocks = workflow.split("uses: actions/setup-go@")[1:]
    assert len(setup_blocks) == 2
    for block in setup_blocks:
        action_step = block.split("\n      - ", 1)[0]
        assert "with:" in action_step
        assert "cache: false" in action_step
        assert "cache-dependency-path:" not in action_step


def test_swift_homebrew_steps_remove_only_unrelated_aws_tap_before_install():
    workflow = (ROOT / ".github" / "workflows" / "compatibility.yml").read_text(encoding="utf-8")
    narrow_guard = (
        "if brew tap | grep -Fxq 'aws/tap'; then\n"
        "                brew untap aws/tap\n"
        "              fi\n"
        "              brew install swift-format"
    )
    probe_guard = (
        "if brew tap | grep -Fxq 'aws/tap'; then\n"
        "            brew untap aws/tap\n"
        "          fi\n"
        "          brew install swift-format"
    )
    assert narrow_guard in workflow
    assert probe_guard in workflow
    assert workflow.count("brew untap aws/tap") == 2
    assert "brew trust aws/tap" not in workflow
    assert "HOMEBREW_NO_REQUIRE_TAP_TRUST" not in workflow
    assert "|| true" not in "\n".join(line for line in workflow.splitlines() if "aws/tap" in line)


def test_release_documentation_requires_one_verified_commit():
    documentation = (ROOT / "docs" / "reference" / "distribution.md").read_text(encoding="utf-8")
    assert "Both `smoke` and `compatibility`" in documentation
    assert "historical release tag is immutable" in documentation
    assert "Maintainers dispatch `.github/workflows/release.yml`" in documentation
    assert "release.json.releaseTag" in documentation
    assert "pending publication" in documentation
    assert "strict smoke verification" in documentation


def test_release_workflow_is_exact_sha_and_action_dependency_free():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "source_commit:" in workflow
    assert "  actions: write" in workflow
    assert 'requested_source_commit="$SOURCE_COMMIT"' in workflow
    assert (
        "required: false"
        in workflow.split("      source_commit:", 1)[1].split("        type: string", 1)[0]
    )
    assert 'requested_source_commit="$SOURCE_COMMIT"' in workflow
    assert 'SOURCE_COMMIT="$DEFAULT_BRANCH_COMMIT"' in workflow
    assert "source_commit must equal the freshly resolved default branch commit" in workflow
    assert 'echo "SOURCE_COMMIT=$SOURCE_COMMIT"' in workflow
    assert "gh auth setup-git" in workflow
    assert 'git fetch --no-tags --quiet origin "${SOURCE_COMMIT}"' in workflow
    assert (
        'git fetch --no-tags --quiet origin "refs/tags/${RELEASE_TAG}:refs/tags/${RELEASE_TAG}"'
        in workflow
    )
    assert 'git rev-parse "$RELEASE_TAG^{commit}"' in workflow
    assert workflow.index(
        'git fetch --no-tags --quiet origin "refs/tags/${RELEASE_TAG}:refs/tags/${RELEASE_TAG}"'
    ) < workflow.index('git rev-parse "$RELEASE_TAG^{commit}"')
    assert "smoke.yml" in workflow and "compatibility.yml" in workflow
    assert "timeout-minutes: 70" in workflow
    assert "RELEASE_DEPENDENCY_TIMEOUT_SECONDS: 1800" in workflow
    assert 'dependency_timeout="${RELEASE_DEPENDENCY_TIMEOUT_SECONDS:-}"' in workflow
    assert '[[ "$dependency_timeout" =~ ^[0-9]+$ && "$dependency_timeout" -ge 1800 ]]' in workflow
    assert "deadline=$((SECONDS + dependency_timeout))" in workflow
    assert "timeout window=$dependency_timeout" in workflow
    assert "deadline=$((SECONDS + 900))" not in workflow
    assert 'any(.[]; .conclusion == "success")' in workflow
    assert 'any(.[]; .status != "completed")' in workflow
    assert "timed out waiting for ${workflow}" in workflow
    assert "sleep 15" in workflow
    assert "gh release create" in workflow
    assert 'git push origin "$SOURCE_COMMIT:refs/tags/$RELEASE_TAG"' in workflow
    assert workflow.index(
        'git push origin "$SOURCE_COMMIT:refs/tags/$RELEASE_TAG"'
    ) < workflow.index("gh release create")
    assert "--draft" in workflow
    assert (
        'gh workflow run smoke.yml --repo "$GITHUB_REPOSITORY" --ref "$GITHUB_REF_NAME"' in workflow
    )
    assert 'gh release edit "$RELEASE_TAG" --repo "$GITHUB_REPOSITORY" --draft=false' in workflow
    assert "actions/checkout" not in workflow
    assert "release-assets" in workflow
    assert "'.commitSha'" in workflow
    assert "release-digests.json" in workflow
    assert "evidenceBundleDigest" in workflow
    assert "EVIDENCE_BUNDLE_DIGEST" in workflow
    assert "#sbom.json" in workflow
    assert "#provenance.json" in workflow
    assert "git ls-remote --symref origin HEAD" in workflow
    assert "refs/remotes/origin/${RELEASE_DEFAULT_BRANCH}" in workflow
    assert 'requested_source_commit="$SOURCE_COMMIT"' in workflow
    assert "release-source.json" in workflow
    assert "RELEASE_REMOTE" in workflow
    assert "RELEASE_DEFAULT_BRANCH" in workflow
    assert "GITHUB_RUN_ID" in workflow


def test_release_workflow_embedded_python_precondition_has_stable_indentation():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    block = workflow.split("          python3 -", 1)[1].split("          PY", 1)[0]
    python_body = block.split("<<'PY'\n", 1)[1]
    lines = [line for line in python_body.splitlines() if line.strip()]
    assert 'assert candidate["releaseState"] == "candidate"' in block
    assert 'assert candidate["published"] is False' in block
    assert 'assert candidate["basedOnReleaseTag"] == published["releaseTag"]' in block
    assert all(line.startswith("          ") for line in lines)
    assert not any(line.startswith("            assert candidate") for line in lines)


def test_release_workflow_binds_one_source_identity_before_provider_checks():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert '--arg tagTarget "$SOURCE_COMMIT"' in workflow
    assert '--arg metadataCommit "$SOURCE_COMMIT"' in workflow
    assert "Fail closed on release freeze, installer, and source-bound archive" in workflow
    assert workflow.index("make check-release-preflight") < workflow.index(
        "Install locked release evidence dependencies"
    )
    assert workflow.index("make check-release-preflight") < workflow.index(
        'git push origin "$SOURCE_COMMIT:refs/tags/$RELEASE_TAG"'
    )


def test_release_workflow_verifies_tagged_quick_install_before_publish():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    verifier = "python3 scripts/verify_quick_install_release.py"
    draft = workflow.index("Verify Draft tag target and release asset subjects")
    publish = workflow.index('gh release edit "$RELEASE_TAG"')
    assert "gh release download" not in workflow
    assert 'gh release view "$RELEASE_TAG" --repo "$GITHUB_REPOSITORY" --json assets' in workflow
    assert '.apiUrl | split("/") | last' in workflow
    assert '[[ "$asset_id" =~ ^[0-9]+$ ]]' in workflow
    assert 'test "$asset_id" =~' not in workflow
    assert '"repos/${GITHUB_REPOSITORY}/releases/assets/${asset_id}"' in workflow
    assert "download_draft_asset release.json" in workflow
    assert '--asset-url "$verified_archive_url"' in workflow
    assert draft < workflow.index(verifier) < publish


def test_release_workflow_publishes_provider_bundle_digest_in_source_evidence():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    bind = workflow.index("Bind the generated evidence bundle digest")
    draft = workflow.index("Create exact-SHA tag and Draft GitHub Release")
    assert workflow.index("release-source.with-digest.json", bind) < draft
    assert workflow.index(".evidenceBundleDigest", bind) < draft


def test_release_workflow_rejects_stale_source_before_mutations():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    mismatch = workflow.index("source_commit must equal the freshly resolved default branch commit")
    checkout = workflow.index('git checkout --detach --quiet "${SOURCE_COMMIT}"')
    evidence = workflow.index("Generate source-bound release evidence")
    tag = workflow.index('git push origin "$SOURCE_COMMIT:refs/tags/$RELEASE_TAG"')
    draft = workflow.index("gh release create")
    publish = workflow.index('gh release edit "$RELEASE_TAG"')
    assert mismatch < checkout < evidence < tag < draft < publish
    assert "rm " not in workflow
    assert "unlink" not in workflow


def test_release_workflow_runs_strict_smoke_before_tag_and_release_mutations():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    smoke = workflow.index("Dispatch strict smoke verification")
    tag = workflow.index("Create exact-SHA tag and Draft GitHub Release")
    publish = workflow.index("Publish verified Draft Release")
    assert smoke < tag < publish
    dispatch = workflow[smoke:tag]
    assert '--ref "$GITHUB_REF_NAME"' in dispatch
    assert '--commit "$SOURCE_COMMIT"' in dispatch


def test_release_strict_smoke_uses_a_distinct_release_run_concurrency_identity():
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    smoke = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")

    strict_smoke = release[
        release.index("Dispatch strict smoke verification") : release.index(
            "Create exact-SHA tag and Draft GitHub Release"
        )
    ]

    assert "-f purpose=release_verification" in strict_smoke
    assert '-f release_run_id="$GITHUB_RUN_ID"' in strict_smoke
    assert 'displayTitle == "smoke release_verification for release ' in strict_smoke
    assert "GITHUB_RUN_ID" in strict_smoke
    assert "release_verification" in smoke
    assert "release_run_id:" in smoke
    assert (
        "smoke-${{ github.ref }}-${{ inputs.purpose || github.event_name }}-${{ inputs.release_run_id || 'shared' }}"
        in smoke
    )
    assert "run-name: smoke ${{ inputs.purpose || github.event_name }}" in smoke
    assert "format(' for release {0}', inputs.release_run_id)" in smoke


def test_release_workflow_bootstraps_pinned_tool_before_lockfile_reproducibility():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    install = "python3 -m pip install --disable-pip-version-check pip==25.2 pip-tools==7.6.0 typing-extensions==4.16.0"
    check = workflow.index("make check-lockfile-reproducibility")
    tag = workflow.index('git push origin "$SOURCE_COMMIT:refs/tags/$RELEASE_TAG"')
    assert workflow.index(install) < check < tag


def test_release_workflow_generates_and_verifies_correlation_record():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert '--workflow-run-id "$GITHUB_RUN_ID"' in workflow
    assert '--workflow-run-sha "$GITHUB_SHA"' in workflow
    assert "correlation.workflowRunId" in workflow
    assert "correlation.workflowRunSha" in workflow
    assert "correlation.sourceCommit" in workflow
    assert "correlation.releaseTag" in workflow
    assert workflow.index("Generate source-bound release evidence") < workflow.index(
        "Create exact-SHA tag and Draft GitHub Release"
    )


def test_release_workflow_wait_has_source_bound_diagnostics_and_timeout_context():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "SOURCE_COMMIT" in workflow
    assert "WAIT_DIAGNOSTIC" in workflow
    assert "dependent run IDs" in workflow
    assert "timeout window" in workflow


def test_smoke_dispatch_declares_explicit_measurement_or_release_purpose():
    workflow = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    assert "github.event_name == 'pull_request'" in workflow
    assert "github.event_name == 'workflow_dispatch'" in workflow
    assert "purpose:" in workflow
    assert "hosted_measurement" in workflow
    assert "release_preparation" in workflow
    assert "inputs.purpose == 'release_preparation'" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "startsWith(github.head_ref" not in workflow


def test_smoke_workflow_has_release_blocking_delegated_secret_scan():
    workflow = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    secret_scan = workflow.split("  secret-scan:\n", 1)[1].split("\n  project-test-manifest:", 1)[0]
    assert "Delegated secret scanning (release-blocking)" in workflow
    assert "github.com/zricethezav/gitleaks/v8@9c72c5f9f05200fdc06e3f1b16e9aaa89fbe9f75" in workflow
    assert "fetch-depth: 0" in secret_scan
    assert 'gitleaks" detect --source="$GITHUB_WORKSPACE"' in secret_scan


def test_smoke_workflow_quality_gate_has_fail_closed_timeout():
    workflow = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    assert "timeout-minutes: 30" in workflow
    assert "Run repository quality gates" in workflow
    assert workflow.index("timeout-minutes: 30") < workflow.index("Run repository quality gates")
    assert "timeout-minutes: 25" in workflow
    assert "quality heartbeat" in workflow


def test_smoke_workflow_reports_hci_quality_progress_every_thirty_seconds():
    workflow = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    quality_step = workflow.split("      - name: Run repository quality gates", 1)[1].split(
        "      - name: Publish failed quality gate logs", 1
    )[0]

    assert "🟡 quality-full running" in quality_step
    assert "Current gate:" in quality_step
    assert "Evidence: target/quality/sessions/" in quality_step
    assert "sleep 30" in quality_step
    assert "🟢 quality-full completed" in quality_step
    assert "Coverage:" in quality_step
    assert "Outcome:" in quality_step


def test_smoke_template_smoke_owns_fail_closed_project_test_aggregate_and_remaining_quality():
    """Regression: the critical-path job must aggregate evidence before remaining gates."""
    workflow = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")

    for shard in ("core", "governance", "installer", "lifecycle", "release"):
        job = workflow.split(f"  project-test-{shard}:\n", 1)[1].split("\n  project-test-", 1)[0]
        assert "needs: project-test-manifest" in job
        assert f"make project-test-shard SHARD={shard}" in job
        assert "actions/download-artifact@" in job
        download = job.split("      - name: Download project-test plan", 1)[1].split(
            f"      - name: Run {shard} project-test shard", 1
        )[0]
        assert "path: target/quality" in download
        assert "actions/upload-artifact@" in job
        assert "include-hidden-files: true" in job
    template = workflow.split("  template-smoke:\n", 1)[1].split("\n  installation-smoke:", 1)[0]
    assert "if: always()" in template
    assert "project-test-core" in template
    assert "project-test-release" in template
    assert "secret-scan" in template
    assert "make project-test-aggregate" in template
    assert "include-hidden-files: true" in template
    assert "Run repository quality gates" in template
    assert "PROJECT_TEST_GATE=project-test-receipt" in template
    assert "Download aggregate project-test evidence" not in template
    assert "Delegated secret scanning (release-blocking)" not in template
    assert template.count("Install development quality tools") == 1
    assert template.count("make check-ai-status-consistency") == 1


def test_smoke_pr_audit_does_not_receive_a_github_api_token_for_offline_recovery_validation():
    workflow = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    audit = workflow.split("      - name: Run template AI checks", 1)[1].split(
        "\n  installation-smoke:", 1
    )[0]

    assert "GH_TOKEN:" not in audit
    assert "Provider-bound recovery receipts are validated offline" in audit


def test_smoke_quality_failure_publishes_detailed_gate_logs():
    workflow = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")

    assert "Publish failed quality gate logs" in workflow
    assert "target/quality/current-session.txt" in workflow
    assert "target/quality/sessions/$(cat target/quality/current-session.txt)" in workflow
    assert "$session_root/logs" in workflow
    assert "Upload quality diagnostics" in workflow
    assert "target/quality/sessions/**" in workflow
    assert "failure log:" in workflow
    assert "if: failure()" in workflow
    assert workflow.index("Run repository quality gates") < workflow.index(
        "Publish failed quality gate logs"
    )
    assert workflow.index("Publish failed quality gate logs") < workflow.index(
        "Publish quality timing summary"
    )


def test_release_workflow_uploads_final_runtime_metadata_not_stale_projection():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    draft = workflow.index("Create exact-SHA tag and Draft GitHub Release")
    publish = workflow.index("Publish verified Draft Release")
    draft_block = workflow[draft:publish]

    assert 'cp release.json "$RUNNER_TEMP/release.json"' in draft_block
    assert (
        'cp "$RUNNER_TEMP/release-projection.json" "$RUNNER_TEMP/release.json"' not in draft_block
    )
