---
author: Ray
title: "CI and Release Evidence"
description: Independently verifiable CI and release evidence contract.
keywords:
  - ai-cockpit
  - ci
  - release
  - evidence
---

# CI and Release Evidence

CI/Release Evidence is a provider-derived JSON record. Its authority is GitHub Actions or the GitHub API, never a pull-request description, agent message, or other self-declared “passed” claim. The validator is `scripts/check_ci_release_evidence.sh`; `make check-ci-release-evidence CI_RELEASE_EVIDENCE=<path>` is the local entry point.

Every record binds a Workflow Run ID, Head SHA, Required Job Names, per-job Conclusions, overall Conclusion, failure reasons, artifact digests, SBOM, Provenance, and a Head-to-Merge relationship. A verified or published record must also bind a merge commit, successful required jobs, empty failure reasons, and non-null SBOM/Provenance digests whose source commit equals the Head SHA. Missing or cross-source identity fails closed.

The smoke workflow has a terminal `ci-evidence` Job with `needs: [template-smoke, installation-smoke, release-evidence]` and `if: always()`. Its evidence always declares and records all three required Jobs from `needs.<job>.result`, including `skipped` results. Explicit release-preparation intent controls whether `release-evidence` runs either release Contract check; it does not remove that Job from the aggregate evidence contract. An ordinary pull request records release validation as not applicable and runs neither `check-release-state-consistency` nor `check-release-distribution`. A successful record must have an empty `failureReasons` array. A skipped or failed Job must never be silently omitted, and a successful Job must never be reported as a failure reason.

The validator reports these boundaries separately: expected Head SHA versus workflow-run Head SHA; a declared required Job absent from `jobs`; a workflow-run required-job set different from the top-level set; and Job statuses inconsistent with the top-level conclusion. The smoke workflow validates the aggregate record before returning its failure, so an upstream failure and dependent skipped Jobs remain reviewable evidence.

The state boundary is explicit:

- `candidate` records describe CI evidence for a change or release candidate and may omit release-only SBOM/Provenance assets.
- `verified` records are provider evidence for an exact source commit after required jobs and release assets have passed.
- `published` records are verified evidence attached to the immutable public release.
- `failed` records must include failure reasons; they cannot authorize a verified or published state.

The smoke workflow emits a structured candidate/failed record to its workflow log and validates it independently. The release workflow obtains exact-SHA smoke and compatibility run records through the provider API, produces `ci-release-evidence.json`, validates it, and publishes it as a release asset. The canonical `release-state.json` rejects `candidate_verified` and `release_published` states without provider-bound `ciEvidence`. Local fixtures are regression inputs only and cannot prove a public release.

For pull requests, the evidence records the PR Head SHA and explains how the provider-side merge commit relates to that head. For release dispatch, the source is resolved from the remote default branch and the merge commit is the exact release source. No PR Body text is parsed or accepted as evidence.
