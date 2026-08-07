---
author: Ray
title: "Synchronization Conflict Outcome Design"
description: "Design record for #709 synchronization-conflict recovery evidence."
workItem: "conflict-successor-outcome-709-current-main"
issue: "https://github.com/spirex-ds-dev/ai-cockpit-template/issues/709"
status: approved
---

# Synchronization Conflict Outcome Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Problem

`ai-synchronize-work-item` already makes a dirty active Work Item recoverable:
it creates a Contract-authorized checkpoint and automatically aborts a failed
rebase.  Its conflict-successor route, however, requires the source Work Item
to retain a red blocked Outcome whose `failedGate` is
`synchronization_conflict`.  The production synchronization path currently
returns the conflict error without generating that evidence.  Existing tests
hide the gap by writing Outcome JSON directly.

## Selected design

Reuse the canonical blocked-Outcome and Human Benefit Report pipeline from
`scripts/ai_finish.py`, and make its file resolution explicit for a target
repository root.  `scripts/ai_resume_work_item.py` will invoke that pipeline
only after its rebase helper has automatically aborted a proven conflict.

The synchronization command will retain its failure exit code. Before it
returns that error, it will persist a validated red Outcome with
`failedGate: synchronization_conflict`, derive the Markdown report, and
commit those generated recovery artifacts using the same already-authorized
checkpoint boundary. This keeps the source worktree clean for the strict
conflict-successor validator. The source Contract and Start Receipt remain
unchanged; the Summary is intentionally updated with the blocked Outcome
state. Normal successful synchronization logic remains unchanged.

## Data flow

1. The synchronization command validates the active Contract and, where
   authorized, commits Contract-owned dirty paths as a checkpoint.
2. Rebase against the fetched remote default branch conflicts; the command
   automatically runs `rebase --abort`.
3. The command invokes the shared Outcome writer with the explicit source
   worktree root, active Contract/Summary paths, and
   `synchronization_conflict` gate identity.
4. The writer validates and persists JSON and Markdown Outcome evidence,
   derives the Human Benefit Report, and refreshes target-root projections.
5. The command commits the generated recovery evidence, then returns the
   original conflict failure. The existing
   `ai-transition-conflict-successor` command can then validate and bind the
   generated source Outcome to one current-main successor.

## Error handling and boundaries

- If Outcome/report persistence fails, synchronization remains failed and
  reports that the conflict evidence could not be persisted.  It must never
  claim a usable successor route.
- No Outcome is produced for successful synchronization, validation failures
  before an attempted rebase, or arbitrary rebase errors that were not safely
  aborted as a conflict.
- The writer must resolve all evidence paths against the synchronization
  target root, never the caller worktree.
- The change does not permit manual conflict resolution, rewriting the
  checkpoint, weakening successor validation, provider mutation, or release.

## Test strategy

1. A real local Git fixture invokes the production synchronization function
   with an authorized dirty checkpoint and a conflicting remote change.  It
   asserts the rebase is aborted, the source stays clean at its checkpoint
   head, and canonical red JSON/Markdown Outcome evidence exists.
2. The same fixture invokes the real conflict-successor transition and proves
   its receipt binds the generated source Outcome rather than a handwritten
   test artifact.
3. The existing clean synchronization fixture proves the success path still
   advances baseline evidence without creating a blocked Outcome.

## Documentation impact

The lifecycle reference and generated capability projections will state that
a safely aborted synchronization conflict produces a red Outcome and is the
only evidence that can enter the current-main conflict-successor route.
