---
author: Ray
title: "Superseded Work Item Lifecycle Closure Design"
description: A fail-closed design for applying one successor-receipt rule to archive and closure.
status: historical
authority: implementation_record
---

# Superseded Work Item Lifecycle Closure Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Problem

`ai_archive_work_item.py` accepts a blocked predecessor only when its Summary
issues are limited to missing or failed required verification and an exact
`transition=superseded` receipt binds the red Outcome. After archival,
`ai_close_work_item.py` repeats strict Summary validation without that narrow
exception. The Work Item can therefore be archived but cannot be lifecycle
closed or cleaned up.

## Considered approaches

1. Put one reusable predicate in `ai_lifecycle_truth.py` and call it from both
   archive and closure. This is selected because the receipt validator already
   lives there and a single rule prevents semantic drift.
2. Copy the archive exception into `ai_close_work_item.py`. This is smaller in
   the immediate diff but creates two independently changeable allowlists and
   receipt checks.
3. Let closure trust the archive manifest. This is rejected because the
   manifest proves artifact movement and digests, not why failed Summary
   verification was eligible for the exceptional lifecycle path.

## Design

Add a lifecycle-truth predicate that receives the predecessor Contract path,
Work Item ID, and Summary validation issues. It returns true only when:

- at least one Summary issue exists;
- every issue starts with the exact missing-required-verification or
  required-verification-not-passed prefix;
- the sibling Outcome is readable, belongs to the Work Item, and remains
  `blocked`;
- the sibling receipt is readable and declares `transition=superseded`;
- the canonical successor receipt validator confirms predecessor identity,
  successor identity/base/branch, Outcome digest, repository issue, authority,
  and reason.

The archive module keeps its existing public helper as a thin compatibility
wrapper around this predicate. Closure first validates the Contract normally,
then validates the Summary normally. It ignores Summary issues only when the
shared predicate accepts them. Contract issues and any unrelated Summary issue
remain fatal.

## Cleanup boundary

The design changes only archived-evidence eligibility. It does not change PR
lookup, branch-to-task mapping, exact PR Head SHA, merged state, fast-forward
base synchronization, clean-worktree checks, closure receipt generation,
remote-ref absence proof, or local branch deletion ordering.

## Tests

Tests must prove a valid superseded predecessor is accepted and must reject a
missing, malformed, quarantined, mismatched, non-blocked, wrong-digest,
foreign-issue, missing-authority, or missing-reason receipt. An unrelated
Summary error must also remain fatal. Existing normal closure and cleanup
ordering tests run unchanged.

## Distribution

Both `ai_lifecycle_truth.py` and `ai_close_work_item.py` are already installed
runtime files, so the behavior reaches future adopter projects through the
normal published template distribution. No template-only alternate path is
introduced.

## Approval

The user explicitly authorized all required confirmations, full Work Item
lifecycles, and local/remote cleanup, and required that authorization be
recorded in the Contract. That standing authorization approves this bounded
design; it does not authorize gate bypass, evidence rewriting, or unrelated
release changes.
