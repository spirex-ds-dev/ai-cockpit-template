---
author: Ray
title: "No-Active Archive Status Diagnostic Design"
description: Narrow ownership design for a start receipt in a pre-commit archive bundle.
---

# No-Active Archive Status Diagnostic Design

## Problem

`ai-finish` generates a no-active status while it moves the completed Work Item into the
archive. Before the first commit of that archive bundle, Git reports the start receipt as a
live change. Archive paths are already excluded from the no-active snapshot, but the matching
start receipt is not. `check-ai-status-consistency` therefore rejects the generated status and
recommends `repair-ai-status`; repair regenerates the same status and fails again.

## Boundary

A start receipt is transient archive-transaction evidence only when the current Git change set
also contains, under one archive directory:

- the same task's Contract;
- the same task's Summary;
- the same task's archive manifest; and
- the archive index update.

The manifest must use `ai-cockpit-archive-manifest`, name the same Work Item, and bind the exact
Contract and Summary paths. Existing historical archive files do not qualify unless they are in
the current change set.

Every orphan receipt, incomplete pair, malformed or mismatched manifest, and unrelated changed
path remains visible to no-active consistency and fails closed.

## Implementation

`live_no_active_changed_files` will gather the complete Git change set first. A small
deterministic classifier will identify start receipts owned by a valid changed archive bundle.
Only those receipt paths and existing archive paths are excluded from the live no-active list.
The status generator remains unchanged and continues to serialize zero transient changes.

## Verification

Regression tests cover a complete pre-commit bundle, missing members, historical-only files,
manifest identity/path mismatch, an orphan receipt, unrelated dirt, and a clean post-commit
state. Documentation states that this exception is transaction-bound and does not make a dirty
worktree generally acceptable.
