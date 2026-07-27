---
author: Ray
title: "No-Active Archive Status Diagnostic Implementation Plan"
description: TDD implementation plan for transaction-bound start-receipt classification.
---

# No-Active Archive Status Diagnostic Implementation Plan

> **For agentic workers:** Use the repository Work Item lifecycle and execute each task with
> test-driven development. Do not mark Contract scenarios verified until their commands pass.

**Goal:** Make archive-before-commit no-active status consistent without hiding unrelated
changes.

**Architecture:** Classify a changed start receipt as transient only when a valid, same-task,
currently changed archive Contract/Summary/manifest bundle and index update bind it.

**Tech Stack:** Python 3, pytest, Git porcelain output, JSON archive manifests.

### Task 1: Characterize the failure

**Files:**

- Modify: `tests/test_core_gates.py`

- [ ] Add a failing regression for the complete pre-commit archive bundle.
- [ ] Add negative cases for orphan, incomplete, historical-only, and malformed bundles.
- [ ] Confirm the positive case fails under the current implementation.

### Task 2: Implement narrow transaction ownership

**Files:**

- Modify: `scripts/ai_check_status_consistency.py`

- [ ] Gather the complete changed-path set before filtering archive paths.
- [ ] Validate same-task archive manifest identity and bound paths.
- [ ] Exclude only the matching start receipt; retain every unrelated path.
- [ ] Run focused tests and formatter/lint checks.

### Task 3: Align process documentation and traceability

**Files:**

- Modify: `.ai/cockpit/README.md`
- Modify: `.ai/cockpit/README.ja.md`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`
- Modify: `docs/reference/remediation-instruction-traceability.json`

- [ ] Record RFE-ISSUE-116 and the corrective boundary.
- [ ] Document pre-commit versus post-commit behavior in English and Japanese.
- [ ] Map instruction, implementation, acceptance, and lifecycle verification.

### Task 4: Finish the complete lifecycle

- [ ] Convert all three Contract scenarios to verified with test evidence.
- [ ] Complete Summary and before-finish checkpoint.
- [ ] Run full `ai-finish` with the public `PYTHON` Make override.
- [ ] Commit archive evidence and verify no-active consistency both before and after commit.
- [ ] Push, open PR, wait for hosted CI, merge, run `ai-close-work-item`, and clean branches.
