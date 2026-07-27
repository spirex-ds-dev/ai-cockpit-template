---
author: Codex
title: "Documentation Alignment Summary Schema Implementation Plan"
description: "TDD and lifecycle plan for RFE-ISSUE-118."
keywords:
  - ai-cockpit
  - documentation-alignment
  - work-item
  - tdd
---

# Documentation Alignment Summary Schema Implementation Plan

**Work Item:** `documentation-alignment-summary-schema-20260728`

**Goal:** Close RFE-ISSUE-118 with a required, source-bound, five-domain
documentation-alignment record for current v2 Summaries while preserving
immutable archive compatibility.

## Execution

1. Start from latest `origin/main` on a dedicated branch, bind the immutable
   Start Receipt, record PR #414 closure as predecessor, and reach a fresh
   `ready` Preflight.
2. Record `before_edit` against the final Contract.
3. Add failing tests for complete alignment, incomplete domains, untrusted
   paths, reverse documentation coverage, legacy archives, ai-start, installer
   adoption/upgrade, and the checked example.
4. Implement one canonical skeleton and validator; require it for current v2
   Summaries, let bounded installer finalization align its final declared write
   set, and retain explicit legacy-archive compatibility.
5. Rewrite current Work Item alignment references to durable archive paths
   while preserving execution-time verification evidence.
6. Update authoritative field and lifecycle documentation, the comprehensive
   plan, and PLAN-DIRECTIVE-013.
7. Run focused Summary tests, expanded Summary/archive/installer tests, document
   and traceability checks, then full `make quality`.
8. Complete `documentationAlignment` with evidence for every changed
   documentation/command surface, update acceptance/scenario evidence, refresh
   both declared checkpoints after any final Contract change, and run
   `make ai-finish`.
9. Commit the archive bundle, rewrite PLAN-DIRECTIVE-013 from active to archive
   Contract path, run committed-state `check-ai-pr`, push, and open exactly one
   PR.
10. Wait for all Hosted CI jobs, merge without automatic branch deletion, run
   `make ai-close-work-item`, verify local/remote branch removal and
   `main == origin/main`, then proceed to the paused performance Work Item.

## Acceptance mapping

- A1–A4: `tests/test_ai_check_summary.py`
- A5: legacy archive tests in `tests/test_ai_check_summary.py`
- A6: `tests/test_start_and_archive.py`, `tests/test_installer.py`,
  `tests/test_finish_e2e.py`, `tests/test_project_governance_journey.py`,
  `tests/test_contract_examples.py`
- A7: field/lifecycle docs, comprehensive plan, PLAN-DIRECTIVE-013
- A8: archive manifest, PR checks, Hosted CI, merge and closure output

No test, document, or plan result alone authorizes release or proves a runtime
capability.
