---
author: Ray
title: "RFE-153 Post-Archive Status Diagnosis Implementation Plan"
description: TDD plan for manifest- and Summary-bound no-active ownership and truthful repair guidance.
---

# RFE-153 Post-Archive Status Diagnosis Implementation Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Goal

Accept the canonical governed archive-before-first-commit transition without
hiding arbitrary no-active edits, and ensure every diagnostic recommends an
operation that can actually resolve the detected state.

## Tasks

1. Add red-first regressions for a complete changed archive bundle whose
   Summary owns all implementation paths.
2. Add negative regressions for an omitted path, unrelated dirt, malformed
   `changedFiles`, incomplete/current-versus-historical bundle, and manifest
   mismatch.
3. Generalize current Start Receipt classification into complete transaction
   ownership derived from the exact manifest-bound archived Summary.
4. Split stale serialized Status diagnostics from unowned live-change
   diagnostics.
5. Refuse unowned no-active repair before rewriting Status; preserve bytes.
6. Align English/Japanese Cockpit and Status guidance, parent issue history,
   and bidirectional traceability.
7. Run focused checks, stable checkpoints, full `ai-finish`, archive, commit,
   aggregate PR validation, Hosted CI, merge, transactional closure, branch
   deletion, and clean synchronized `main`.

## Non-claims

- No arbitrary dirty no-active tree becomes valid.
- Contract scope does not substitute for Summary changed-file evidence.
- Repair does not create ownership or mutate archive evidence.
- RFE-152 and release work do not begin before this lifecycle closes.
