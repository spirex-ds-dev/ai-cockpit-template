---
author: Ray
title: "Japanese Calibration Session Evidence Documentation Corrective Plan"
description: Correct the trilingual Calibration Session evidence-storage boundary before resuming the mandatory Japanese final assessment.
---

# Japanese Calibration Session Evidence Documentation Corrective Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Objective

Resolve `JA-DOC-FACT-002` before the paused Japanese final reassessment
continues. The three installation guides must describe the implemented
Calibration Session schema consistently: `answer` persists the answer fields,
`record-evidence` persists the structured review evidence, and the combined
stage record supports the complete seven-column human review row.

This Work Item changes documentation and its executable checks only.
`scripts/ai_calibrate.py` is the read-only runtime fact source.

## Finding and root cause

Independent Accuracy and Clarity reviews found the same release-blocking
contradiction in English, Chinese, and Japanese:

- the early completion-checklist paragraph said that Session stored only the
  answer or execution state and assigned the other columns to the Work Item;
- the later activation paragraph and `scripts/ai_calibrate.py` showed that
  `record-evidence` already persists `observedEvidence`, `candidateChange`,
  `owner`, `reviewer`, `decision`, `decisionReason`, and `retryStep`;
- the existing metadata gate checked only a broad persistence marker and
  therefore allowed both contradictory statements to coexist.

The Work Item still has a separate role: it records governance rationale,
acceptance, owner decisions, and links to external review evidence. Persisted
`reviewer` and `owner` labels are strings and do not prove who performed a
review or that duties were independently separated.

## Issues found during execution

- `JA-DOC-FACT-002-IMPL-001` — the first implementation added four semantic
  branches directly to the already-large beginner installation validator.
  `quality-fast` correctly rejected function complexity 54 against the limit
  50, and Ruff reported one formatting change. The fix keeps the policy limit,
  extracts a focused `_calibration_session_evidence_errors` validator, formats
  the file, and requires a fresh quality run.
- `JA-DOC-FACT-002-REVIEW-001` — independent pre-finish review found that the
  first correction called the `checklistEvidence` child object the whole
  seven-column row, allowed required prose to hide in comments, did not test
  contradictory prose while retaining the positive statement, used unnatural
  Japanese, and made pre-finish evidence appear to prove post-merge closure.
  The correction now describes the combined stage record, validates visible
  prose only within the completion section, adds contradiction-preserving and
  comment-hiding mutations, uses beginner-facing Japanese, and separates
  pre-finish acceptance from the post-merge resume condition.
- `JA-DOC-FACT-002-RESUME-001` — the first Finish exposed stale Capability
  Truth bytes because the original Contract omitted the matrix. The independent
  capability-evidence corrective closed through PR #453 before this Work Item
  resumed. Resume now records that closed predecessor, owns and regenerates the
  matrix, and preserves regeneration as evidence maintenance rather than
  Japanese capability proof.

## Instruction → plan → implementation → acceptance

| Instruction | Plan | Implementation evidence | Acceptance evidence |
| --- | --- | --- | --- |
| Japanese capability is mandatory and every discovered issue must be corrected before release. | Stop the final reassessment and complete this independent corrective lifecycle first. | Contract; this plan; comprehensive plan | archived Summary; PR; Hosted; merge; closure |
| Keep English, Chinese, and Japanese aligned. | Replace the contradictory storage paragraph in all three guides with the same storage and trust boundary. | three `installation*.md` guides | metadata checker and multilingual mutation tests |
| Do not let the same omission recur. | Require one shared marker plus language-specific complete-record, Work Item, and label-limitation statements. | `scripts/check_docs_metadata.py` | `tests/test_docs_metadata.py` |
| Do not change runtime to fit documentation. | Treat `scripts/ai_calibrate.py` as read-only and verify the diff contains no runtime change. | Contract scope and git diff | scope/diff-ownership gates and focused tests |
| Every Work Item uses bidirectional traceability and a complete lifecycle. | Register `PLAN-DIRECTIVE-043`, align Summary evidence, then archive, PR, Hosted, merge, close, and clean branches. | traceability and context registries | traceability gate and lifecycle evidence |
| Fix discovered process defects before resuming. | Bind the closed capability-evidence corrective as predecessor and regenerate the matrix under explicit Contract ownership. | resumeHistory; capability matrix | Preflight Evidence Dependency signal; matrix validation |

## Test-driven implementation

1. Add red-first mutations for:
   - a missing shared evidence-boundary marker in any language;
   - a narrow “Session stores only answers/state” claim;
   - equivalent narrow claims with alternate English, Chinese, and Japanese word order;
   - equivalent postpositive `only` / `仅` / `のみ` claims;
   - a missing Work Item governance/external-evidence boundary;
   - a missing reviewer/owner label limitation;
   - required statements hidden only in HTML comments;
   - a prompt that loses the `answer` versus `record-evidence` storage split.
2. Confirm all eight mutation regressions fail before their corresponding implementation.
3. Correct all three documents and make the metadata checker fail closed.
4. Regenerate the Capability Truth matrix, then run the complete documentation
   metadata suite and full repository quality.
5. Confirm `scripts/ai_calibrate.py` is byte-for-byte unchanged by this Work
   Item.

## Completion and resume boundary

This corrective is complete only after `ai-finish` archive evidence, one
dedicated PR, exact-Head Hosted success, merge, `ai-close-work-item`, local and
remote branch deletion, and synchronized `main`.

The Work Item resumed from `4a78169e` to `e0f80ea3` only after
`capability-evidence-scope-dependency-corrective-20260729` closed through
PR #453; that transition is source-bound in `resumeHistory`.

Only then may
`japanese-final-reassessment-after-documentation-truth-20260729` rebase and
resume. Documentation alignment, deprecated-assets cleanup, release, and plan
cleanup remain blocked until that final reassessment has zero blockers and
completes its own lifecycle.
