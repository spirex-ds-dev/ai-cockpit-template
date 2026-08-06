---
author: Codex
title: "Trusted Self-hosted Recovery Validation Implementation Plan"
description: Test-first implementation plan for temporary self-hosted recovery diagnostics.
keywords:
  - ai-cockpit
  - self-hosted-runner
  - ci
  - verification
---

# Trusted Self-hosted Recovery Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore maintainer-only diagnostic feedback during a hosted Actions outage without changing the authoritative hosted compatibility, merge, or release gate.

**Architecture:** A new dispatch-only workflow validates an exact source SHA, runs on the isolated macOS runner label set, executes `make quality`, and writes an explicit diagnostic red/green summary. Topology tests make the trigger, runner, source identity, and evidence boundary executable; operations documentation states how to use and retire the temporary path.

**Tech Stack:** GitHub Actions YAML, Python/pytest workflow-topology tests, Markdown operations documentation, Make quality gate.

## Global Constraints

- Only `workflow_dispatch` may trigger the recovery workflow; no `push` or `pull_request` event is permitted.
- Require `[self-hosted, macOS, X64, ai-cockpit-recovery]`; do not imitate hosted runner labels.
- Validate a 40-hex `source_commit`, check out that exact SHA, and fail if `HEAD` differs.
- Set `contents: read`; do not grant write permissions or mutate GitHub/provider state.
- Every result is diagnostic/non-release and cannot satisfy compatibility, merge, archive, or release gates.
- When hosted Actions recovers, run the normal hosted matrix before any merge or release decision.

---

### Task 1: Lock the recovery workflow security contract with tests

**Files:**
- Modify: `tests/test_workflows.py`
- Test: `tests/test_workflows.py`

**Interfaces:**
- Consumes: `.github/workflows/self-hosted-recovery.yml`, introduced in Task 2.
- Produces: `test_self_hosted_recovery_is_maintainer_dispatched_and_diagnostic`, a static topology regression test.

- [ ] **Step 1: Write the failing test**

```python
def test_self_hosted_recovery_is_maintainer_dispatched_and_diagnostic():
    workflow = (ROOT / ".github" / "workflows" / "self-hosted-recovery.yml").read_text(
        encoding="utf-8"
    )
    assert "  workflow_dispatch:" in workflow
    assert "  pull_request:" not in workflow
    assert "  push:" not in workflow
    assert "runs-on: [self-hosted, macOS, X64, ai-cockpit-recovery]" in workflow
    assert "^[0-9a-f]{40}$" in workflow
    assert "RECOVERY_RESULT=green" in workflow
    assert "RECOVERY_RESULT=red" in workflow
    assert "diagnostic only" in workflow
    assert "cannot satisfy compatibility, merge, or release gates" in workflow
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_workflows.py::test_self_hosted_recovery_is_maintainer_dispatched_and_diagnostic -q`

Expected: FAIL because `.github/workflows/self-hosted-recovery.yml` does not exist.

- [ ] **Step 3: Commit after the red test and later implementation in Task 2**

```bash
git add tests/test_workflows.py .github/workflows/self-hosted-recovery.yml
git commit -m "ci: add trusted self-hosted recovery workflow"
```

### Task 2: Implement the dispatch-only recovery workflow

**Files:**
- Create: `.github/workflows/self-hosted-recovery.yml`
- Test: `tests/test_workflows.py::test_self_hosted_recovery_is_maintainer_dispatched_and_diagnostic`

**Interfaces:**
- Consumes: `workflow_dispatch.inputs.source_commit` as a 40-hex immutable Git commit SHA.
- Produces: a GitHub Actions run with an exact-SHA checkout, `make quality` result, and red/green diagnostic summary.

- [ ] **Step 1: Create the minimal workflow that satisfies Task 1**

```yaml
name: self-hosted recovery validation

on:
  workflow_dispatch:
    inputs:
      source_commit:
        description: Immutable 40-character Git commit SHA to diagnose.
        required: true
        type: string

permissions:
  contents: read

jobs:
  recovery-quality:
    runs-on: [self-hosted, macOS, X64, ai-cockpit-recovery]
    timeout-minutes: 45
```

Add steps that reject a non-40-hex input, fetch/check out `source_commit`, compare `git rev-parse HEAD` to it, run `make quality`, and use an `if: always()` summary step that sets `RECOVERY_RESULT=green` only when the quality step succeeded and otherwise sets `RECOVERY_RESULT=red`.

- [ ] **Step 2: Run the focused test to verify it passes**

Run: `pytest tests/test_workflows.py::test_self_hosted_recovery_is_maintainer_dispatched_and_diagnostic -q`

Expected: PASS.

- [ ] **Step 3: Run related workflow tests**

Run: `pytest tests/test_workflows.py -q`

Expected: PASS.

### Task 3: Document operation and hosted-return boundary

**Files:**
- Modify: `docs/operations/quality-gates.md`
- Test: `tests/test_workflows.py`

**Interfaces:**
- Consumes: recovery workflow dispatch contract from Task 2.
- Produces: documented provisioning, dispatch, evidence, and hosted-return procedure.

- [ ] **Step 1: Add the operations section**

Document the required custom label, maintainer-only dispatch, immutable SHA input, diagnostic-only interpretation, red/green result meaning, failure handling, and mandatory return to hosted smoke/compatibility after the GitHub outage.

- [ ] **Step 2: Run documentation and workflow checks**

Run: `pytest tests/test_workflows.py -q && make check-ai-contract && make check-ai-scope`

Expected: PASS.

- [ ] **Step 3: Commit the documentation**

```bash
git add docs/operations/quality-gates.md
git commit -m "docs: define self-hosted recovery evidence boundary"
```

### Task 4: Produce governed evidence and exercise the route

**Files:**
- Modify: `.ai/work-items/active/trusted-self-hosted-recovery-validation-724.summary.json`
- Generated: `.ai/cockpit/current_status.md`, Outcome and archive evidence.

**Interfaces:**
- Consumes: exact branch SHA, focused test results, local quality result, and a maintainer-dispatched recovery run URL when Actions accepts dispatches.
- Produces: truthful Summary/Outcome and an archive-ready Work Item; a recovery run remains diagnostic, not hosted merge evidence.

- [ ] **Step 1: Record the before-edit checkpoint**

Run: `make ai-prepare-implementation CONTRACT=.ai/work-items/active/trusted-self-hosted-recovery-validation-724.contract.json SUMMARY=.ai/work-items/active/trusted-self-hosted-recovery-validation-724.summary.json`

Expected: PASS before changing workflow, test, or operations files.

- [ ] **Step 2: Run focused and full local verification**

Run: `make ai-verify-focused CONTRACT=.ai/work-items/active/trusted-self-hosted-recovery-validation-724.contract.json SUMMARY=.ai/work-items/active/trusted-self-hosted-recovery-validation-724.summary.json` and then `make ai-verify-full CONTRACT=.ai/work-items/active/trusted-self-hosted-recovery-validation-724.contract.json SUMMARY=.ai/work-items/active/trusted-self-hosted-recovery-validation-724.summary.json STAGE=pr`.

Expected: Results recorded without claiming a self-hosted run is hosted evidence.

- [ ] **Step 3: Dispatch only if GitHub accepts it and record the result**

Run: `gh workflow run self-hosted-recovery.yml --ref codex/trusted-self-hosted-recovery-validation-724 -f source_commit=<exact-branch-SHA>`.

Expected: The labeled runner executes the workflow; record its URL and result as diagnostic evidence. If the provider outage prevents dispatch, record that blocked external fact without bypassing gates.

- [ ] **Step 4: Finish, archive, PR, and retain hosted verification requirements**

Run the Work Item’s required `ai-finish`, archive commit, `make check-ai-pr AI_BASE_COMMIT=a49343f90fe4a4bed19438024965e5a3d26501fa`, PR, and lifecycle sequence. Do not merge until required hosted checks are healthy and green.

## Self-review

- Spec coverage: Tasks 1–2 cover trigger, label, SHA, and red/green behavior; Task 3 covers operations/evidence boundaries; Task 4 covers governance, dispatch, and hosted return.
- Placeholder scan: no TBD/TODO entries or unspecified validation behavior remain.
- Interface consistency: `source_commit`, the exact label set, and diagnostic classification are used consistently by every task.
