---
author: Ray
title: "WI-01 through WI-20 Hosted Coverage Recovery"
description: Governed replacement delivery for the WI-01 through WI-20 audit after portable coverage margin failure.
keywords:
  - ai-cockpit
  - traceability
  - coverage
  - hosted-ci
  - recovery
---

# WI-01 through WI-20 Hosted Coverage Recovery
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Purpose

Recover the completed bidirectional traceability audit without rewriting its
archived evidence. PR #425 ran all 1,333 tests successfully on Hosted Linux, but
reported 85.05% coverage against the unchanged 85.10% executable threshold.
The predecessor local result was 85.102326%, only 0.002326 percentage points
above the threshold, so it did not provide a portable verification margin.

## Governed recovery

This replacement Work Item is an adjacent recovery relationship:

- predecessor: `wi01-wi20-bidirectional-traceability-audit-20260728`,
  archive sequence 635, immutable;
- superseded delivery: closed PR #425 and Hosted run `30345295068`;
- recovery: `wi01-wi20-hosted-coverage-recovery-20260728`, explicitly
  authorized and source-linked to the predecessor;
- replacement delivery: one new PR containing both archive bundles, accepted
  only by aggregate recovery-chain validation.

The recovery does not lower the coverage threshold, exclude production files,
change the completed twenty-row audit, implement later process issues, or
prepare a release.

## Instruction → plan → implementation → acceptance

1. Preserve the predecessor Contract, Summary, Manifest, sequence, and failed
   provider evidence without amendment.
2. Identify uncovered fail-closed branches in
   `scripts/check_instruction_traceability.py`.
3. Add red-first negative tests that prove malformed, missing, stale, or
   mismatched corrective evidence is rejected with a useful diagnostic.
4. Run the focused suite and authoritative traceability check; confirm the
   twenty-row result remains complete with zero open findings.
5. Run full local quality at the unchanged 85.10% threshold and require a
   margin larger than the observed local-to-Hosted variance.
6. Archive the recovery, commit both immutable bundles, and run aggregate PR
   validation against the predecessor's recorded base.
7. Open a replacement PR and require every Hosted check, including
   `template-smoke` and terminal `ci-evidence`, to pass.
8. Merge, run `ai-close-work-item`, remove both recovery and superseded
   branches, synchronize `main`, and only then enter the process-issues stage.

## Process issue

`RFE-ISSUE-148` — A local full-suite result only 0.002326 percentage points
above the executable coverage threshold was accepted as finish evidence, but
the same 1,333 tests produced 85.05% on Hosted Linux. The gate correctly failed;
the process gap is that local finish had no portable margin requirement despite
known cross-platform coverage variance. This recovery keeps the threshold at
85.10%, adds meaningful branch regressions, records the exact Hosted failure,
and requires replacement Hosted success before lifecycle closure.
