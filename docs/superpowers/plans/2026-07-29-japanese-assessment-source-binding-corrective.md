---
author: Ray
title: "Japanese Assessment Source Binding Corrective Implementation Plan"
description: Bind Japanese assessment evidence bytes and release-time execution to the asserted source before final reassessment resumes.
---

# Japanese Assessment Source Binding Corrective Implementation Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make stale or source-mismatched Japanese capability evidence fail closed before the final reassessment and release.

**Architecture:** The canonical assessment will hash a sorted inventory of every stable source, test, corpus, and documentation file used by its cases, and include that identity in the top-level report digest. Release-time execution will separately resolve the asserted source commit and require it to equal checked-out `HEAD`; this avoids an impossible self-referential report-to-own-commit digest while still proving that the content-bound report was checked in the exact release checkout.

**Tech Stack:** Python 3 standard library, pytest, GNU Make, deterministic JSON/Markdown generation, Git commit resolution, AI Cockpit Contract/Summary lifecycle.

## Global Constraints

- Japanese capability remains a mandatory pre-release gate.
- General provider/model Japanese fluency and native-human translation quality remain explicit non-claims.
- Generated `.ai/cockpit/current_status.md` is not a stable report input; Status behavior is bound through implementation, Make targets, and tests.
- Missing, escaping, non-file, stale, or source-mismatched evidence fails closed.
- This corrective does not complete the final Japanese reassessment and does not start documentation alignment or release.
- The final reassessment resumes only after PR, Hosted CI, merge, archive, `ai-close-work-item`, branch cleanup, and synchronized `main`.

---

### Task 1: Freeze the defect and evidence boundary

**Files:**
- Modify: `.ai/work-items/active/japanese-assessment-source-binding-corrective-20260729.contract.json`
- Modify: `.ai/work-items/active/japanese-assessment-source-binding-corrective-20260729.summary.json`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`
- Modify: `docs/reference/remediation-instruction-traceability.json`
- Modify: `docs/reference/documentation-context-registry.json`

**Interfaces:**
- Consumes: current `evaluate()`, `report_drift()`, Make release prerequisite, user-approved serial workflow.
- Produces: `RFE-ISSUE-154`, a ready Contract, traceability directive, and before-edit checkpoint.

- [x] **Step 1: Record the root cause**

Add `RFE-ISSUE-154` to the comprehensive plan: the report hashes path labels and pass observations but not evidence bytes; Make does not pass `RELEASE_PREFLIGHT_SOURCE_COMMIT` to the Japanese prerequisite.

- [x] **Step 2: Register bidirectional traceability**

Add one machine directive mapping the user instruction and `RFE-ISSUE-154` to this Contract, plan, implementation files, red/green tests, report outputs, full Finish, PR, and closure evidence.

- [x] **Step 3: Register this plan**

Add this plan to `documentation-context-registry.json` as mutable `current_instruction`.

- [x] **Step 4: Run Preflight and checkpoint**

Run:

```bash
make ai-preflight CONTRACT=.ai/work-items/active/japanese-assessment-source-binding-corrective-20260729.contract.json
make check-ai-serial-order TASK=japanese-assessment-source-binding-corrective-20260729
make check-ai-budget-impact TASK=japanese-assessment-source-binding-corrective-20260729
make ai-checkpoint CONTRACT=.ai/work-items/active/japanese-assessment-source-binding-corrective-20260729.contract.json SUMMARY=.ai/work-items/active/japanese-assessment-source-binding-corrective-20260729.summary.json STAGE=before_edit
```

Expected: Preflight `ready`; serial order, budget, and checkpoint pass.

### Task 2: Add red tests for evidence-content identity

**Files:**
- Modify: `tests/test_japanese_capability.py`
- Test: `tests/test_japanese_capability.py`

**Interfaces:**
- Consumes: desired helper `build_evidence_source(paths, root=ROOT) -> dict[str, object]`.
- Produces: failing requirements for sorted per-file SHA-256 inventory, aggregate digest, and fail-closed path validation.

- [x] **Step 1: Write the content-change regression**

Create two evidence files in `tmp_path`, call `build_evidence_source`, change only whitespace in one file, call again, and assert that file and aggregate digests change while the sorted path list stays identical.

- [x] **Step 2: Write fail-closed path regressions**

Parametrize missing file, directory, absolute path, and `../` traversal. Assert `JapaneseCapabilityError` names the rejected path and reason.

- [x] **Step 3: Write inventory-boundary regression**

Call `evaluate()` and assert `evidenceSource.paths` contains `scripts/ai_japanese_capability.py`, every case source/test evidence file, and no `.ai/cockpit/current_status.md`.

- [x] **Step 4: Verify RED**

Run:

```bash
PYTHONPATH=scripts:. .venv/bin/pytest -q \
  tests/test_japanese_capability.py -k 'evidence_source or evidence_path or transient_status'
```

Expected: FAIL because `build_evidence_source`, `JapaneseCapabilityError`, and `evidenceSource` do not exist.

### Task 3: Implement deterministic evidence-content identity

**Files:**
- Modify: `scripts/ai_japanese_capability.py`
- Modify: `docs/reference/japanese-capability-assessment.json`
- Modify: `docs/reference/japanese-capability-assessment.md`
- Test: `tests/test_japanese_capability.py`

**Interfaces:**
- Consumes: normalized repository-relative evidence paths from matrix cases.
- Produces: `build_evidence_source(paths, root=ROOT)`, assessment schema version 3, `evidenceSource.algorithm`, sorted `files`, and aggregate `digest`.

- [x] **Step 1: Implement strict path normalization**

Reject absolute paths, `..`, missing paths, and non-files. Resolve each candidate below `root`, read bytes, and store lowercase SHA-256.

- [x] **Step 2: Build the canonical inventory**

Union all stable `sourceEvidence` and `testEvidence` paths with `scripts/ai_japanese_capability.py`; remove the transient Status output from the Status case and keep its generator, checker, Makefile, and tests.

- [x] **Step 3: Bind the report**

Set `assessmentVersion` to `3`, add `evidenceSource` before calculating the top-level digest, render its algorithm/file-count/digest in Markdown, and describe `workItemId` as the assessment-definition Work Item rather than a final-run claim.

- [x] **Step 4: Regenerate canonical views**

Run:

```bash
PYTHONPATH=scripts:. .venv/bin/python scripts/ai_japanese_capability.py --write
```

Expected: JSON and Markdown have one identical evidence-source digest and zero current blocking findings.

- [x] **Step 5: Verify GREEN**

Run:

```bash
PYTHONPATH=scripts:. .venv/bin/pytest -q tests/test_japanese_capability.py
PYTHONPATH=scripts:. .venv/bin/python scripts/ai_japanese_capability.py --check
```

Expected: all tests and report freshness pass.

### Task 4: Add red tests for release source equality

**Files:**
- Modify: `tests/test_japanese_capability.py`
- Modify: `tests/test_makefile.py`
- Test: `tests/test_japanese_capability.py`
- Test: `tests/test_makefile.py`

**Interfaces:**
- Consumes: desired `validate_expected_source(root: Path, expected_ref: str) -> str`.
- Produces: failing requirements for exact commit equality and Make variable propagation.

- [x] **Step 1: Write real-Git mismatch and equality tests**

Initialize a temporary repository with two commits. Assert an expected first commit against second-commit `HEAD` raises `JapaneseCapabilityError`; assert second commit returns its full lowercase SHA.

- [x] **Step 2: Write Make propagation test**

Assert `check-japanese-capability` conditionally adds `--source-commit "$(RELEASE_PREFLIGHT_SOURCE_COMMIT)"` and remains a prerequisite of `check-release-preflight`.

- [x] **Step 3: Verify RED**

Run:

```bash
PYTHONPATH=scripts:. .venv/bin/pytest -q \
  tests/test_japanese_capability.py -k expected_source \
  tests/test_makefile.py -k japanese
```

Expected: FAIL because source validation and Make propagation do not exist.

### Task 5: Implement release-time source binding

**Files:**
- Modify: `scripts/ai_japanese_capability.py`
- Modify: `Makefile`
- Test: `tests/test_japanese_capability.py`
- Test: `tests/test_makefile.py`

**Interfaces:**
- Consumes: `--source-commit <ref>` and `RELEASE_PREFLIGHT_SOURCE_COMMIT`.
- Produces: exact resolved SHA equality before report acceptance.

- [x] **Step 1: Resolve immutable commits**

Use controlled `git -C <root> rev-parse <ref>^{commit}` subprocess calls for expected ref and `HEAD`; reject errors, empty output, malformed SHA, and mismatch with distinct diagnostics.

- [x] **Step 2: Extend the CLI**

Add optional `--source-commit`; validate it before report drift and blocker decisions. Keep direct `--check` behavior unchanged when omitted.

- [x] **Step 3: Propagate the Make variable**

Pass `--source-commit "$(RELEASE_PREFLIGHT_SOURCE_COMMIT)"` only when the variable is non-empty. Preserve Japanese prerequisite ordering.

- [x] **Step 4: Verify GREEN and dry-run wiring**

Run:

```bash
PYTHONPATH=scripts:. .venv/bin/pytest -q tests/test_japanese_capability.py tests/test_makefile.py
make -n check-release-preflight RELEASE_PREFLIGHT_SOURCE_COMMIT="$(git rev-parse HEAD)"
```

Expected: tests pass; the executable Make regression proves the exact value reaches both processes through the environment without appearing in either shell command, and the dry run preserves Japanese-before-release ordering.

- [x] **Step 5: Apply independent-review hardening**

Record and fix the Bandit import regression, shell-interpolated source input, explicit-empty bypass, normalized-path alias duplication, symbolic-link/Git-blob mismatch, and missing bound-versus-unrelated end-to-end drift regressions. Pass the source through the exported Make environment without command interpolation and fail closed on explicit empty input.

### Task 6: Complete governance evidence and local verification

**Files:**
- Modify: `.ai/work-items/active/japanese-assessment-source-binding-corrective-20260729.summary.json`
- Modify: `.ai/cockpit/current_status.md`
- Modify: `docs/reference/remediation-instruction-traceability.json`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`

**Interfaces:**
- Consumes: focused test results and regenerated report digest.
- Produces: verified scenarios, changed-file/source mappings, issue resolution, documentation alignment, and review-ready Summary.

- [x] **Step 1: Update the Summary**

Record every changed file, TDD red/green evidence, `RFE-ISSUE-154`, source-binding limitations, zero capability blockers without a final-assessment claim, scenario results, user-correction solidification, and five-domain documentation alignment.

- [x] **Step 2: Complete reverse traceability**

Map every acceptance item to production and test evidence; map every changed implementation/test/report path back to the instruction and plan.

- [x] **Step 3: Run focused and fast gates**

Run:

```bash
PYTHONPATH=scripts:. .venv/bin/pytest -q tests/test_japanese_capability.py tests/test_makefile.py
make check-japanese-capability
make check-instruction-traceability
make quality-fast
```

Expected: all pass.

- [x] **Step 4: Refresh final checkpoint**

Run the `before_finish` checkpoint only after Contract, Summary, plan, and traceability stop changing.

### Task 7: Finish, review, merge, and close

**Files:**
- Generate: `.ai/work-items/archive/2026/japanese-assessment-source-binding-corrective-20260729.contract.json`
- Generate: `.ai/work-items/archive/2026/japanese-assessment-source-binding-corrective-20260729.summary.json`
- Generate: `.ai/work-items/archive/2026/japanese-assessment-source-binding-corrective-20260729.archive-manifest.json`
- Modify: `.ai/work-items/archive/index.json`

**Interfaces:**
- Consumes: completed active Contract/Summary and passing local gates.
- Produces: immutable archive, merged PR, clean closure, and synchronized `main`.

- [ ] **Step 1: Run full Finish**

The first post-review attempt passed 1472 tests and all quality gates but stopped at `check-ai-agent-risk` because the Contract scope expansion made the original `before_edit` checkpoint hash stale. Refresh `before_edit` and `before_finish`, record `RFE-ISSUE-154-CHECKPOINT-001`, and rerun the complete Finish; do not treat the first quality result as completion evidence.

The second attempt again passed 1472 tests and full quality, and the refreshed agent-risk gate passed, but Summary validation stopped because high-risk acceptance entries lacked per-item `humanReview` and used non-Contract verification labels. Record `RFE-ISSUE-154-SUMMARY-001`, bind all ten entries to the user's standing authorization and exact verification IDs, then rerun the complete Finish.

```bash
make ai-finish TASK=japanese-assessment-source-binding-corrective-20260729
```

Expected: full quality and every required governance check pass; active evidence archives atomically.

- [ ] **Step 2: Commit and validate the aggregate PR**

Commit the exact archive bundle, then run:

```bash
make check-ai-pr AI_BASE_COMMIT=83ba616981a1003342b37220b958823d53b85410
```

Expected: complete diff ownership, traceability, archive, and recovery checks pass.

- [ ] **Step 3: Push and open one PR**

Push only `codex/japanese-assessment-source-binding-corrective-20260729`, open one ready PR, and wait for all required Hosted checks.

- [ ] **Step 4: Merge and close**

Merge without provider-side branch deletion, then run:

```bash
make ai-close-work-item TASK=japanese-assessment-source-binding-corrective-20260729
```

Expected: exact PR Head ownership, merged state, archive evidence, local/remote branch deletion, clean worktree, and synchronized default branch are all proved.

- [ ] **Step 5: Resume the final Japanese reassessment**

Create a fresh dedicated branch from the newly synchronized `origin/main`; do not reuse this corrective branch or its verification as the final reassessment lifecycle.
