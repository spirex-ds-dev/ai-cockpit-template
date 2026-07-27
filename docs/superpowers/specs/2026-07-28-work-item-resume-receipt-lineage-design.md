---
author: Ray
title: "Governed Work Item Resume Receipt Lineage Design"
description: Append-only, source-bound baseline transitions for paused Work Items.
---

# Governed Work Item Resume Receipt Lineage

## Problem

A Work Item can be paused because a process defect must be corrected first. After
the corrective PR is merged and closed, the paused branch must rebase onto the
latest remote default branch. Its immutable Start Receipt still proves the
original delegation boundary, while its Contract baseline must advance so scope,
ownership, and complexity checks do not treat the corrective commits as work
owned by the resumed task.

Today those facts cannot coexist: receipt validation requires the original and
current baselines to be identical. Manual receipt rewriting destroys evidence;
manual Contract rewriting has no proof for the transition.

## Decision

Add `make ai-resume-work-item` backed by a repository script. The command updates
only an active Contract and appends a `resumeHistory` entry:

```json
{
  "resumeVersion": 1,
  "fromBaseCommit": "<previous Contract base>",
  "toBaseCommit": "<latest remote default branch>",
  "baseRemote": "<discovered remote>",
  "baseBranch": "<discovered default branch>",
  "workBranch": "<dedicated Work Item branch>",
  "recordedAt": "<UTC ISO-8601>",
  "priorContractDigest": "<SHA-256 before transition>",
  "predecessorWorkItemId": "<closed corrective Work Item>",
  "predecessorMergeCommit": "<exact merge commit>",
  "predecessorManifestPath": "<archive manifest>",
  "predecessorClosure": {
    "statusClosed": true,
    "prMerged": true,
    "closureSucceeded": true,
    "localBranchDeleted": true,
    "remoteBranchDeleted": true,
    "baseSynchronized": true
  }
}
```

The Start Receipt and its Contract binding never change. The first transition
must start at the receipt baseline; each later transition must start at the
previous transition's target; the final target must equal the current Contract
`baseCommit`.

## Generation boundary

The writer must verify before changing the Contract:

- the current branch is dedicated and matches `workBranch`;
- the requested remote/default branch ref exists and is the exact target;
- the prior baseline is an ancestor of the target;
- the Contract's `predecessorWorkItem` is fully closed;
- predecessor PR merge commit equals the transition target;
- the referenced archive manifest exists, uses the supported format, names the
  predecessor Work Item, and binds its Contract and Summary;
- existing history already validates;
- the original Start Receipt bytes and Contract binding are not rewritten.

The write is atomic. A failed check leaves the Contract unchanged.

## Validation boundary

`validate_receipt` remains the canonical validator. Exact receipt/Contract
baseline equality remains valid for never-resumed Work Items. If the values
differ, a complete valid history is mandatory. Each structural, chain, Git, and
lifecycle invariant receives a distinct diagnostic.

PR/archive validation calls the same lineage helper. It may not infer a resume
from ancestry alone or create a second exception.

## Repeated resume

History is append-only. The writer computes `priorContractDigest` before each
transition and never edits older entries. A subsequent correction therefore
produces a second edge rather than replacing the first.

## Out of scope

- rewriting legacy Start Receipts;
- allowing arbitrary historic branch rebases;
- retaining a branch without predecessor closure;
- changing release recovery exceptions;
- introducing cryptographic identity or signing claims.

## Verification

Focused tests use temporary Git repositories and real commits. They cover one
resume, repeated resume, immutable receipt preservation, atomic failure,
malformed chains, ancestry failures, branch/remote mismatch, predecessor and
manifest mismatch, and shared PR validation.
