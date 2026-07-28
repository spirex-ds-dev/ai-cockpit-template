---
author: Ray
title: "Traceability Archive Evidence Rewrite Corrective Plan"
description: Close the archive-path rewrite and stale-active fallback gap before resuming WI-10.
keywords:
  - ai-cockpit
  - traceability
  - archive
  - corrective
  - fail-closed
---

# Traceability Archive Evidence Rewrite Corrective Plan

## Status and order

`traceability-archive-evidence-rewrite` is a release-blocking process
corrective inserted while the archived, uncommitted
`wi10-installation-version-neutral` branch is frozen.

The order is:

1. complete this corrective through PR, Hosted checks, merge,
   `ai-close-work-item`, and branch cleanup;
2. rebase the frozen WI-10 branch onto the corrected `origin/main`;
3. verify that its archived Contract and Summary paths are both durable;
4. complete the WI-10 PR and lifecycle;
5. resume final Japanese assessment.

## User instruction and observed failure

The user requires “instruction → plan → implementation → acceptance”
bidirectional traceability and explicitly required archive processing to
rewrite or resolve traceability paths so obsolete active paths are not left
behind.

After WI-10 `ai-finish`, `PLAN-DIRECTIVE-037.contractPaths` was rewritten to
the archived Contract, but `acceptanceEvidence` still named the removed active
Summary. `make check-instruction-traceability` passed because `_resolved_path`
silently found the archived file.

The same strengthened check exposed four earlier stale Summary references:

- `rfe082-release-truth-reconciliation-20260729`;
- `japanese-assessment-depth-corrective-20260729`;
- `japanese-lifecycle-hosted-env-recovery-20260729`;
- `installed-detached-uninstaller-runtime-corrective-20260729`.

## Root cause

The archive transaction already creates a replacement map for Contract,
Summary, review, success, and outcome paths. It applied only the Contract
replacement to the registered traceability manifest. The validator had a
stale-active special case only for `contractPaths`; implementation and
acceptance evidence continued through archive fallback.

This combination made the stored path false while the Gate reported success.

## Bidirectional mapping

| Instruction / finding | Plan | Implementation | Acceptance |
|---|---|---|---|
| Rewrite every archived Work Item evidence path | Complete replacement-map transaction in this plan | `scripts/ai_archive_work_item.py` | all-path rewrite and rollback tests |
| Reject stale active evidence in every traceability field | Fail-closed validator rule in this plan | `scripts/check_instruction_traceability.py` | Contract, Summary, review, and live-active tests |
| Remove existing hidden debt | Four-item inventory above | `docs/reference/remediation-instruction-traceability.json` | repository manifest Gate |
| Resume WI-10 only after process closure | Status and order above | corrective PR/merge/closure, then WI-10 rebase | exact-Head Hosted and branch cleanup evidence |

## Implementation tasks

- [x] Create a dedicated Contract from latest `origin/main`, reach Preflight
  `ready`, and record `before_edit`.
- [x] Add red-first regressions reproducing the missing complete rewrite and
  stale active Summary false negative.
- [x] Apply the complete replacement map inside the existing atomic archive
  transaction.
- [x] Reject archive-resolvable stale active Work Item paths in
  `contractPaths`, `implementationEvidence`, and `acceptanceEvidence`.
- [x] Preserve valid references to active files that still exist.
- [x] Prove post-rewrite failure restores traceability bytes and active files.
- [x] Migrate all four pre-existing stale Summary references to verified
  archive paths.
- [ ] Run focused suites, manifest Gate, `quality-fast`, and full Finish.
- [ ] Complete PR, Hosted checks, merge, closure, remote/local branch deletion,
  and clean synchronized main.
- [ ] Resume and rebase WI-10; do not manually bypass its archive evidence.

## Problem log

- `TRACE-ARCHIVE-ISSUE-001` (high): archive transaction used only the Contract
  replacement even though the complete replacement map already existed.
- `TRACE-ARCHIVE-ISSUE-002` (high): validator rejected stale active Contracts
  but silently accepted stale active Summary/review/outcome evidence.
- `TRACE-ARCHIVE-ISSUE-003` (medium): the strengthened Gate exposed four
  historical stale Summary paths. All four archive targets exist and are
  migrated together; no fallback-hidden debt is retained.
- `TRACE-ARCHIVE-ISSUE-004` (low): the first `quality-fast` passed static
  checks and then stopped in Documentation Metadata/System Invariants because
  this new plan was not yet registered. Add the registry to Contract scope,
  register this plan as `current_instruction`, refresh Preflight/checkpoint,
  and restart the complete fast gate rather than reusing partial results.
- `TRACE-ARCHIVE-ISSUE-005` (low): the first full Finish passed 1456 tests and
  85.61% coverage, then Summary validation rejected an invalid
  `intentAlignment` shape, a date-only alignment timestamp, and command/anchor
  strings where file paths were required. Correct the Summary to the enforced
  schema and rerun Finish from the beginning; the prior quality result is
  evidence of the failure run, not a substitute for the rerun.

## Completion boundary

This corrective does not complete WI-10, Japanese assessment, documentation
alignment, deprecated-asset cleanup, or release. Those claims remain blocked
until their own Work Item lifecycles close.
