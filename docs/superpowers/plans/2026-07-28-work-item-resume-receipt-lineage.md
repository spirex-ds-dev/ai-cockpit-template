---
author: Ray
title: "Work Item Resume Receipt Lineage Implementation Plan"
description: TDD plan for RFE-ISSUE-117 and its full governed delivery lifecycle.
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# Work Item Resume Receipt Lineage Implementation Plan

## Traceability

| Directive | Plan | Implementation | Acceptance and verification |
|---|---|---|---|
| Preserve immutable start evidence | Test unchanged receipt bytes and binding before implementation | Canonical receipt validator plus atomic resume writer | A2; focused one- and two-resume tests |
| Make resume a governed workflow | Add command contract and source checks | `ai_resume_work_item.py` and `make ai-resume-work-item` | A1, A4; real Git fixture |
| Reject bypasses | Write negative tests first for every transition invariant | Shared fail-closed `resumeHistory` validation | A3; parameterized negative regressions |
| Keep PR semantics aligned | Add archive compatibility regressions | PR checker consumes canonical lineage result | A5; PR aggregate tests |
| Prevent future operator drift | Document exact lifecycle in both maintained runtime languages | English/Japanese cockpit and lifecycle references | A6; documentation/link gates |
| Record and close the process defect | Map RFE-ISSUE-117 into the comprehensive plan and traceability registry | Contract/Summary/plan evidence | A7; traceability checks |
| Complete the full Work Item lifecycle | Run every local and hosted gate, then close and clean branches | Archive, PR, CI, merge, `ai-close-work-item` | A8; lifecycle facts |

## Execution

1. Complete Contract, design, traceability, and `before_edit` checkpoint. Run
   enforced Preflight until `ready`.
2. Add failing unit tests for a valid first resume and repeated append-only
   resume.
3. Add failing negative tests for direct baseline edits, malformed/discontinuous
   history, non-ancestor commits, branch/remote mismatch, predecessor closure,
   merge identity, and manifest identity.
4. Implement the canonical lineage parser/validator and atomic resume writer.
5. Add the Make entry point and route PR compatibility through the canonical
   validator.
6. Update English/Japanese lifecycle guidance and the comprehensive
   instruction-to-acceptance mapping.
7. Run focused tests, all AI checks, and full `make quality`; record actual
   evidence in Summary and mark every scenario only from executed tests.
8. Run `before_finish`, independent review, `ai-finish`, archive, commit,
   `check-ai-pr`, push, PR, hosted CI, merge, `ai-close-work-item`, branch
   deletion, and base synchronization.
9. Rebase the paused performance Work Item, invoke the new resume command, and
   prove its Preflight succeeds without modifying its Start Receipt.

## Stop conditions

Any new workflow defect is recorded in the active Summary and comprehensive
plan. If it can invalidate this Work Item's process, fix it in a separate
corrective lifecycle before proceeding.
