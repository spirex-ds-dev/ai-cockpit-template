---
author: Ray
title: "Release Evidence Model Corrective Implementation Plan"
description: Replace recurring committed release-freeze invalidation with repository readiness and exact-source rehearsal controls.
keywords:
  - release
  - rehearsal
  - source-bound-evidence
  - governance
---

# Release Evidence Model Corrective Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the recurring premerge-freeze invalidation loop while preserving fail-closed, exact-source release controls.

**Architecture:** Split the current overloaded release preflight into a repository-readiness mode and an exact-source mode. Repository readiness checks stable candidate/policy facts without treating a historical committed freeze as authoritative; the release workflow alone materializes and validates exact-source freeze evidence. Add a mandatory non-publishing rehearsal artifact that an actual release must bind to the same SHA and tag.

**Tech Stack:** Python 3.11+, GNU Make, GitHub Actions YAML, pytest, jq, GitHub CLI.

## Global Constraints

- Keep v0.5.45 unpublished throughout this Work Item; no tag, GitHub Release, or public asset may be created.
- Retain the exact-source runtime finalizer and strict archive, digest, SHA, Japanese assessment, SBOM, provenance, and hosted-CI boundaries before publication.
- A rehearsal must execute the release preparation/evidence path and must be mechanically incapable of running tag, Draft Release, asset, or publish steps.
- An actual release must reject a missing, failed, mismatched-SHA, or mismatched-tag rehearsal receipt before any immutable mutation.
- Do not merge stale PRs #528/#529. Compare their intent, record replacement coverage, then close them only after the successor PR passes Hosted CI.
- If any test demonstrates that a later source commit still requires a new freeze Work Item merely to run readiness/rehearsal, stop implementation and return to root-cause analysis.

---

### Task 1: Separate repository readiness from strict exact-source preflight

**Files:**

- Modify: `scripts/check_release_preflight.py`
- Modify: `Makefile`
- Test: `tests/test_release_preflight.py`
- Test: `tests/test_makefile.py`

**Interfaces:**

- Consumes: `check_release_preflight.py --mode {exact-source,repository-readiness}`.
- Produces: `make check-release-readiness`, which runs current Japanese evidence first and then repository readiness.
- Preserves: `make check-release-preflight RELEASE_PREFLIGHT_SOURCE_COMMIT=<sha>` as the strict runtime-only exact-source validation.

- [ ] **Step 1: Write failing repository-readiness regressions.**

```python
def test_repository_readiness_accepts_later_source_after_historical_freeze(repo):
    _commit(repo, "included source correction", {"scripts/example.py": "new\n"})
    result = _run_release_preflight(repo, "HEAD", mode="repository-readiness")
    assert result.returncode == 0

def test_exact_source_preflight_still_rejects_historical_freeze_after_later_source(repo):
    _commit(repo, "included source correction", {"scripts/example.py": "new\n"})
    result = _run_release_preflight(repo, "HEAD", mode="exact-source")
    assert result.returncode == 1
    assert "sourceTree" in result.stderr
```

- [ ] **Step 2: Run the two tests and record the red failure.**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_release_preflight.py -k 'repository_readiness or historical_freeze'`

Expected: the new `--mode` is unrecognized or repository readiness rejects the stale historical freeze.

- [ ] **Step 3: Implement the mode split.**

```python
parser.add_argument(
    "--mode",
    choices=("exact-source", "repository-readiness"),
    default="exact-source",
)

if args.mode == "repository-readiness":
    issues = validate_release_projection(state=release_state, release=release, candidate=candidate)
    issues.extend(validate_repository_policy(active_work_items=active, archive_count=archive_count, ...))
    return _report_readiness(issues)
```

The readiness path must not load, resolve, or compare `.ai/cockpit/release-freeze.json` or `release-digests.json`. The exact-source path retains the current runtime freeze, concrete SHA, archive, installer, and identity-tuple checks unchanged.

- [ ] **Step 4: Add the Make entry point and its dry-run regression.**

```make
check-release-readiness:
	$(AI_PYTHON) scripts/ai_japanese_capability.py --check --require-final-reassessment
	$(AI_PYTHON) scripts/check_release_preflight.py --root . --mode repository-readiness
```

The existing `check-release-preflight` target remains strict and is not redirected to readiness.

- [ ] **Step 5: Run focused verification.**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_release_preflight.py tests/test_makefile.py`

Expected: PASS; both stale-snapshot behavior and exact runtime rejection are covered.

### Task 2: Add a SHA-bound non-publishing rehearsal to the existing release workflow

**Files:**

- Modify: `.github/workflows/release.yml`
- Test: `tests/test_release_workflow.py`
- Test: `tests/test_workflows.py`

**Interfaces:**

- New workflow-dispatch inputs: `rehearsal` (boolean, default `false`) and `rehearsal_run_id` (string, required by an actual publication run).
- Rehearsal output: run-scoped private artifact `release-rehearsal` containing JSON fields `format`, `version`, `mode`, `sourceCommit`, `releaseTag`, and `runId`.
- Actual release input: a successful same-repository rehearsal run id whose artifact SHA/tag fields exactly equal the newly resolved default-branch `SOURCE_COMMIT` and requested release tag.

- [ ] **Step 1: Write failing workflow-structure tests.**

```python
assert 'rehearsal:' in workflow
assert 'rehearsal_run_id:' in workflow
assert 'name: Validate successful exact-source rehearsal' in workflow
assert 'name: Upload exact-source rehearsal receipt' in workflow
assert 'if: ${{ !inputs.rehearsal }}' in tag_step
assert 'if: ${{ !inputs.rehearsal }}' in publish_step
```

Include a negative assertion that the actual-release validation runs before `Create exact-SHA tag and Draft GitHub Release`.

- [ ] **Step 2: Run workflow tests and record red failure.**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_release_workflow.py tests/test_workflows.py`

Expected: FAIL because the rehearsal inputs, receipt validation, and publication guards are absent.

- [ ] **Step 3: Implement one shared preparation path.**

```yaml
workflow_dispatch:
  inputs:
    rehearsal:
      type: boolean
      default: false
    rehearsal_run_id:
      type: string
      required: false
```

Run exact checkout, runtime finalization, strict preflight, dependency lock verification, required CI collection, source-bound evidence, digest binding, and strict smoke for both modes. In rehearsal mode, write/upload the receipt after these checks. In publication mode, download and verify the successful rehearsal artifact before the first tag/Release operation.

- [ ] **Step 4: Guard every publication side effect.**

```yaml
- name: Create exact-SHA tag and Draft GitHub Release
  if: ${{ !inputs.rehearsal }}

- name: Publish verified Draft Release
  if: ${{ !inputs.rehearsal }}
```

Apply the same guard to Draft asset verification and tagged Quick Install, because a rehearsal has no tag or public asset. The receipt upload is permitted only in rehearsal mode and is a private Actions artifact, not a public release asset.

- [ ] **Step 5: Run focused verification.**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_release_workflow.py tests/test_workflows.py`

Expected: PASS; ordering, receipt binding, and no-publication guards are all proven.

### Task 3: Align operator documentation and legacy freeze wording

**Files:**

- Modify: `docs/reference/ai-cockpit-work-item-lifecycle.md`
- Modify: `docs/reference/distribution.md`
- Modify: `docs/reference/distribution.ja.md`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`

**Interfaces:**

- Operators first run `make check-release-readiness`, then dispatch rehearsal, then dispatch the actual release with the rehearsal run id.
- The hosted runtime exact-source preflight remains the sole authority for source/archive/freeze binding.

- [ ] **Step 1: Add documentation assertions before rewriting.**

```python
assert "repository readiness" in lifecycle.lower()
assert "rehearsal" in lifecycle.lower()
assert "exact-source runtime evidence" in lifecycle.lower()
assert "not a published release" in distribution.lower()
```

- [ ] **Step 2: Update lifecycle sequence.**

Replace the rule requiring every new release attempt to create a premerge freeze Work Item with this sequence: latest main → no active Work Items → repository readiness → successful same-SHA rehearsal → actual hosted runtime finalization/exact preflight → tag/Release/assets. State explicitly that a later source change invalidates the rehearsal SHA and requires a new rehearsal, not another committed freeze.

- [ ] **Step 3: Record stale PR disposition.**

Document that #528 and #529 are stale, unmerged predecessors whose derived-report/self-reference observations were reviewed. They must not be merged; closure happens only after successor Hosted evidence proves replacement coverage.

- [ ] **Step 4: Run focused documentation verification.**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_release_workflow.py tests/test_docs_metadata.py`

Expected: PASS; English/Japanese distribution semantics remain aligned and no publication claim is introduced.

### Task 4: Prove convergence before workflow lifecycle completion

**Files:**

- Modify: `.ai/work-items/active/release-evidence-model-corrective-20260731.summary.json`
- Test: `tests/test_release_preflight.py`
- Test: `tests/test_release_workflow.py`

**Interfaces:**

- Convergence proof: later included-source commit → readiness PASS → rehearsal eligible; exact preflight FAIL before runtime materialization and PASS only after runtime materialization.

- [ ] **Step 1: Run the convergence test set.**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_release_preflight.py tests/test_release_workflow.py tests/test_workflows.py tests/test_makefile.py`

Expected: PASS.

- [ ] **Step 2: Evaluate the stop rule.**

If the test fixture needs a committed premerge freeze after the later source commit merely to reach readiness/rehearsal, stop this Work Item and report non-convergence. Otherwise record the exact test evidence in the Summary.

- [ ] **Step 3: Run required governance checks and create direct active Outcome.**

Run: `make ai-finish CONTRACT=.ai/work-items/active/release-evidence-model-corrective-20260731.contract.json SUMMARY=.ai/work-items/active/release-evidence-model-corrective-20260731.summary.json SKIP_QUALITY=true`

Expected: required governance gates pass under the temporary user-authorized focused-verification exception. Report the active-state Outcome directly in conversation before archive, PR, or any stale-PR closure.

## Self-Review

- Spec coverage: Tasks 1–2 implement the split and same-path rehearsal; Task 3 aligns the human-facing lifecycle; Task 4 tests the exact recurrence the user reported and blocks non-convergent execution.
- Placeholder scan: no TBD/TODO markers; each task names code/tests and executable commands.
- Interface consistency: repository readiness is intentionally non-SHA-bound; runtime preflight remains exact-source; rehearsal receipt is SHA/tag-bound and required only for publication.
