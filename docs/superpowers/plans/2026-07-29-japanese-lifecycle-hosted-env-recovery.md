---
author: Ray
title: "Japanese Lifecycle Hosted Environment Recovery"
description: Governed replacement delivery after outer Work Item context contaminated adopter installation in Hosted CI.
keywords:
  - ai-cockpit
  - japanese
  - installer
  - hosted-ci
  - recovery
---

# Japanese Lifecycle Hosted Environment Recovery
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Purpose

Recover `japanese-lifecycle-fixture-corrective-20260729` without rewriting its
archive. PR #439 passed local verification but Hosted run `30387736987`
injected the template Work Item's `AI_BASE_COMMIT`. The installer passed that
ambient value to adopter status generation, which tried to resolve template
commit `f8da33712fe1c19bf1f017ca7b6b9824b00479de` inside the isolated adopter
repository and correctly rolled the installation transaction back.

This is a production environment-boundary defect, not a Japanese translation
failure and not a Head SHA or terminal evidence aggregation defect.

## Governed recovery

- Keep predecessor archive sequence 649 immutable.
- Keep closed PR #439 and Hosted run `30387736987` as failed delivery evidence.
- Deliver the fix through
  `japanese-lifecycle-hosted-env-recovery-20260729`.
- Open one replacement PR containing the predecessor and adjacent recovery
  archive bundles.
- Require aggregate recovery-chain validation, all Hosted jobs, merge,
  lifecycle closure, both branch deletions, and synchronized `main`.

## Instruction → plan → implementation → acceptance

1. Reproduce the Hosted failure with an outer `AI_BASE_COMMIT` that is not an
   adopter commit.
2. Add a shared installer subprocess environment that removes Git, coverage,
   Work Item identity, and recursive Make override context.
3. Preserve ordinary environment values and explicit template release/source
   selection.
4. Route every adopter status-generation subprocess through that boundary.
5. Run the helper regression, installer rollback regressions, and the complete
   Japanese adopter lifecycle under Hosted-equivalent contamination.
6. Update the comprehensive issue record and machine traceability registry.
7. Run focused checks, `quality-fast`, complete quality, archive, aggregate PR
   ownership, and replacement Hosted CI.
8. Merge, run `ai-close-work-item`, remove predecessor and recovery branches,
   restore the normal GitHub identity, synchronize `main`, and only then start
   JA-DOC-001.

## Process issue

`WI-16-ISSUE-012` — The earlier nested Work Item environment correction
protected core recursive Make and quality subprocesses, but
`install_ai_cockpit.py` directly launched adopter status generation with
`{**os.environ, ...}`. Hosted `AI_BASE_COMMIT` therefore crossed repository
authority boundaries. A fixture-only workaround would hide a real installer
failure, so the recovery centralizes the production subprocess boundary and
tests both direct variables and encoded recursive Make overrides.
