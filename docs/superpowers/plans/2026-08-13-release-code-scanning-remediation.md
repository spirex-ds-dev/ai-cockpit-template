---
author: Ray
title: "Release Code Scanning remediation implementation plan"
description: "TDD plan for removing untrusted cross-run release artifact consumption."
status: historical
authority: implementation_record
---

# Release Code Scanning Remediation Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate release publication's untrusted cross-run artifact flow without weakening its exact-source rehearsal requirement.

**Architecture:** Publication validates the supplied rehearsal run as metadata only, then creates and verifies its own strict-smoke run. This removes the prior run's receipt, artifact names, artifact contents, and derived run ID from publication's data flow. Rehearsal evidence creation remains isolated to rehearsal runs.

**Tech Stack:** GitHub Actions YAML, GitHub CLI, jq, pytest.

## Global Constraints

- Preserve successful exact-source rehearsal validation before publication.
- Fail closed on malformed identifiers and mismatched workflow metadata.
- Do not publish releases or mutate tags in this Work Item.
- Do not suppress CodeQL alerts.

---

### Task 1: Lock the safe data-flow contract in a regression test

**Files:**

- Modify: `tests/test_release_workflow.py`
- Modify: `.github/workflows/release.yml:121-181,411-442`

**Interfaces:**

- Consumes: release workflow text.
- Produces: a regression assertion that the publication path validates a rehearsal run but never downloads its artifacts or exports its derived ID.

- [ ] **Step 1: Write the failing test**

```python
def test_publication_validates_rehearsal_metadata_without_consuming_prior_run_artifacts():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    validation = workflow[workflow.index("Validate successful exact-source rehearsal") : workflow.index("Materialize exact-source runtime release freeze")]

    assert 'gh run download "$REHEARSAL_RUN_ID"' not in validation
    assert 'gh run download "$strict_run_id"' not in validation
    assert 'echo "STRICT_SMOKE_REUSED_RUN_ID=$strict_run_id" >> "$GITHUB_ENV"' not in validation
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/test_release_workflow.py -k publication_validates_rehearsal_metadata`

Expected: FAIL because publication currently downloads the rehearsal receipt and its strict-smoke artifacts.

- [ ] **Step 3: Write minimal implementation**

```yaml
- name: Dispatch strict smoke verification for verified source commit
  working-directory: ${{ github.workspace }}
  run: |
    set -euo pipefail
    gh workflow run smoke.yml --repo "$GITHUB_REPOSITORY" --ref "$GITHUB_REF_NAME" \
      -f purpose=release_verification \
      -f release_run_id="$GITHUB_RUN_ID"
    # Locate and wait for the current run's matching strict smoke run.
```

Delete only the publication-path receipt and artifact reuse block. Keep the
metadata validation for `REHEARSAL_RUN_ID`, and remove the rehearsal-only
condition from strict-smoke dispatch.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q tests/test_release_workflow.py -k publication_validates_rehearsal_metadata`

Expected: PASS.

### Task 2: Verify preserved release guards

**Files:**

- Modify: `tests/test_release_workflow.py`
- Modify: `.github/workflows/release.yml:121-181,411-442`

**Interfaces:**

- Consumes: the revised release workflow.
- Produces: regression coverage that strict smoke dispatch happens for publication and rehearsal while public side effects remain conditional on non-rehearsal mode.

- [ ] **Step 1: Extend the focused test**

```python
strict_smoke = workflow[workflow.index("Dispatch strict smoke verification for verified source commit") : workflow.index("Record exact-source rehearsal receipt")]
assert 'if: ${{ inputs.rehearsal }}' not in strict_smoke
assert 'echo "STRICT_SMOKE_RUN_ID=$run_id" >> "$GITHUB_ENV"' in strict_smoke
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/test_release_workflow.py -k publication_validates_rehearsal_metadata`

Expected: FAIL before the workflow condition is removed.

- [ ] **Step 3: Complete minimal workflow change**

Retain the existing successful conclusion, exact SHA, workflow name, event,
and job-result checks around rehearsal and strict-smoke run metadata. Keep
`if: ${{ inputs.rehearsal }}` only on rehearsal receipt creation and upload.

- [ ] **Step 4: Run focused workflow tests**

Run: `.venv/bin/python -m pytest -q tests/test_release_workflow.py`

Expected: PASS.

### Task 3: Record the security boundary

**Files:**

- Create: `docs/superpowers/specs/2026-08-13-release-code-scanning-remediation-design.md`
- Create: `docs/superpowers/plans/2026-08-13-release-code-scanning-remediation.md`

**Interfaces:**

- Consumes: the approved Work Item Contract and workflow behavior.
- Produces: an auditable explanation of the trust boundary and verification scope.

- [ ] **Step 1: Document the selected design**

State that publication uses rehearsal metadata only, dispatches its own strict
smoke run, and never trusts prior-run artifacts.

- [ ] **Step 2: Verify documentation scope**

Run: `make check-ai-scope CONTRACT=.ai/work-items/active/fix-release-code-scanning.contract.json`

Expected: the design and plan records are owned by the Work Item.

### Task 4: Run governed verification

**Files:**

- Modify: `.ai/work-items/active/fix-release-code-scanning.summary.json`
- Generate: `.ai/cockpit/current_status.md`

**Interfaces:**

- Consumes: focused test results and AI Cockpit checks.
- Produces: a truthful Change Summary and archived Work Item only after all required checks pass.

- [ ] **Step 1: Run focused tests**

Run: `.venv/bin/python -m pytest -q tests/test_release_workflow.py`

Expected: PASS.

- [ ] **Step 2: Run required quality and Work Item checks**

Run: `make quality` and `make ai-finish TASK=fix-release-code-scanning`

Expected: all checks pass and the Work Item is archived.

- [ ] **Step 3: Inspect hosted Code Scanning after merge**

Run: GitHub Code Scanning alert query for this repository after the PR merges.

Expected: alerts #2, #3, and #4 are fixed or any remaining finding has a documented root cause and follow-up Work Item.
