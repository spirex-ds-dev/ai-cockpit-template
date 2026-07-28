---
author: Ray
title: "RFE-153 Post-Archive Status Diagnosis Design"
description: Truthful no-active ownership and repair diagnostics for the governed archive-before-commit transition.
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# RFE-153 Post-Archive Status Diagnosis Design

## Problem

After `ai-finish` archives a Work Item, the canonical branch is intentionally
dirty until the first archive-bundle commit. The no-active generator persists a
deterministic zero-change marker, but the consistency checker compares that
marker with the live implementation diff and reports that `repair-ai-status`
can resolve the mismatch. Repair writes the same marker and fails again.

RFE-116 classified only a matching Start Receipt as archive-transaction-owned.
It does not classify implementation and documentation paths already declared in
the immutable archived Summary.

## Authority boundary

A live path is temporarily owned after archive only when all of these facts are
true:

1. the current diff includes the archive index, same-task Start Receipt,
   archived Contract, archived Summary, and archive manifest;
2. the manifest has the supported format/version and binds those exact paths;
3. the archived Summary is valid JSON for the same Work Item;
4. `changedFiles` is a list of repository-relative path records; and
5. every current live path except the generated Status is named by that
   Summary.

Scope, path prefix, historical existence, and prose never grant ownership.
Any omitted, unrelated, malformed, incomplete, or mismatched path remains fail
closed.

## State and diagnostics

- Clean no-active: pass.
- Complete current archive transaction: pass without serializing transient
  paths.
- Stale serialized Status: recommend `repair-ai-status`.
- Unowned live changes: explain that repair cannot establish ownership; require
  restoring the changes or creating/resuming a Work Item.

Repair checks unowned no-active changes before invoking the generator and
preserves Status bytes on refusal. A complete archive transaction and clean
tree remain idempotently repairable.

## Verification

Red-first tests cover a complete transaction, Summary-omitted and unrelated
paths, malformed Summary evidence, incomplete/mismatched/historical bundles,
stale serialized Status, clean post-commit state, and failed-repair byte
preservation. The real RFE-151 incident remains immutable source evidence.
