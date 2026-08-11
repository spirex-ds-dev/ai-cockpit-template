---
author: Ray
title: "Superseded Pre-Archive Coverage Binding Implementation Plan"
description: TDD plan for immutable historical Outcomes and current archive-candidate coverage.
status: historical
authority: implementation_record
---

# Superseded Pre-Archive Coverage Binding Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

**Goal:** Archive an exact superseded historical red Outcome without weakening
current candidate coverage or rewriting historical evidence.

**Architecture:** Add one canonical superseded transition predicate to lifecycle
truth, reuse it from Summary validation and the archive coverage-binding edge,
and preserve the normal exact-binding path.

### Task 1: Red-first transition predicate

- [ ] Add tests for a valid blocked Outcome/receipt pair and every invalid
  transition class.
- [ ] Extract the reusable predicate in `scripts/ai_lifecycle_truth.py`.
- [ ] Keep `superseded_summary_validation_exception` as the Summary-issue
  allowlist plus the canonical transition predicate.

### Task 2: Red-first coverage binding edge

- [ ] Add a failing test proving a valid superseded historical Outcome may omit
  only `preArchiveCandidateCoverage`.
- [ ] Add failing tests proving a mismatched existing binding and invalid
  receipt remain blocked.
- [ ] Update `load_pre_archive_candidate_coverage` to return the current binding
  only for the exact absent-field superseded case.

### Task 3: Documentation and evidence

- [ ] Document current-report and archive-manifest requirements plus the narrow
  historical exception.
- [ ] Regenerate capability and documentation-alignment evidence.
- [ ] Update the Summary with scenarios, sources, and guideline compliance.

### Task 4: Verification and delivery

- [ ] Run focused archive/lifecycle tests and `quality-fast`.
- [ ] Run `ai-finish` once for strict full quality, archive, commit, and PR gates.
- [ ] Push, obtain green hosted checks, merge, and run lifecycle closure.
- [ ] Return to the preserved predecessor worktree, generate its exact current
  candidate report, archive its unchanged red evidence, and close it.
