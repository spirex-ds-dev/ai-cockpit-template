---
author: Codex
title: "Release Receipt Reuse Implementation Plan"
description: "TDD plan for fail-closed reuse of exact-source release rehearsal evidence."
status: historical
authority: implementation_record
---

# Release Receipt Reuse Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the second identical strict-smoke run from a public release only when a complete, exact-source rehearsal receipt proves it already passed.

**Architecture:** The rehearsal stores a versioned receipt derived from its strict-smoke run and provider artifacts. Publication verifies every receipt binding against GitHub and downloaded artifacts before it proceeds to the existing runtime freeze, evidence, Draft asset, and Quick Install gates.

**Tech Stack:** GitHub Actions YAML, Bash, `gh`, `jq`, Python pytest.

## Global Constraints

- Never use a cache hit as verification evidence.
- Require source SHA, Git tree, tag, complete successful jobs, collection/shards, coverage/source set, artifact digests, receipt integrity and expiry.
- Reject invalid receipt evidence before creating a tag or public Release.
- Keep runtime freeze, preflight, supply-chain evidence, Draft asset checks and Quick Install.

---

### Task 1: Specify receipt reuse with regression tests

**Files:**
- Modify: `tests/test_release_workflow.py`
- Modify: `.github/workflows/release.yml`

**Interfaces:**
- Consumes: `release-rehearsal` Actions artifact.
- Produces: version 2 `ai-cockpit-release-rehearsal` receipt.

- [ ] **Step 1: Write failing workflow-contract tests**

```python
assert "Reuse strict smoke verification from exact-source rehearsal receipt" in workflow
assert "treeDigest" in workflow
assert "strictSmokeRunId" in workflow
```

- [ ] **Step 2: Verify red**

Run: `pytest -q tests/test_release_workflow.py`

Expected: the receipt-reuse tests fail because the workflow has no reuse step.

- [ ] **Step 3: Implement receipt and verifier**

```bash
source_tree="$(git rev-parse "${SOURCE_COMMIT}^{tree}")"
strict_run="$(gh run view "$strict_run_id" --json conclusion,headSha,workflowName,event,displayTitle,jobs)"
jq -e '(.coverage.percent >= 85.10)' "$receipt"
```

- [ ] **Step 4: Verify green**

Run: `pytest -q tests/test_release_workflow.py tests/test_workflows.py`

Expected: all focused tests pass and YAML parses.

### Task 2: Document that receipt reuse is fail-closed evidence consumption

**Files:**
- Modify: `docs/reference/ai-cockpit-work-item-lifecycle.md`
- Modify: `docs/reference/distribution.md`
- Modify: `docs/reference/distribution.ja.md`

- [ ] **Step 1: State the exact retained boundaries**

Document source/tree/tag/job/collection/coverage/artifact/integrity/expiry matching and the preserved runtime, Draft, and Quick Install gates.

- [ ] **Step 2: Run documentation regression checks**

Run: `pytest -q tests/test_release_workflow.py tests/test_workflows.py`

Expected: lifecycle and distribution tests remain green.

### Task 3: Validate, publish and prove future-adopter delivery

**Files:**
- Modify: `.ai/work-items/active/release-receipt-reuse.summary.json`

- [ ] **Step 1: Run Contract-required local quality gates**

Run: `make quality-fast && make quality-full && make quality-release`

- [ ] **Step 2: Publish hosted evidence and review the exact-source rehearsal**

Run: `gh workflow run release.yml -f tag=v0.5.52 -f source_commit=<merged-sha> -f rehearsal=true`

- [ ] **Step 3: Publish using only the successful same-SHA receipt**

Run: `gh workflow run release.yml -f tag=v0.5.52 -f source_commit=<merged-sha> -f rehearsal=false -f rehearsal_run_id=<rehearsal-run-id>`

- [ ] **Step 4: Prove public delivery**

Run: `make check-release-distribution-post-publish`

Expected: a new empty adopter repository validates and installs the public correction release.
