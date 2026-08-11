---
author: Ray
title: "Superseded Outcome Byte Preservation Design"
description: Preserve the receipt-bound red Outcome while archiving a valid superseded predecessor.
status: historical
authority: implementation_record
---

# Superseded Outcome Byte Preservation Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Problem

The archive transaction rewrote active paths inside every Outcome JSON after it
moved the file. A valid successor receipt binds the blocked predecessor Outcome
by SHA-256, so that rewrite invalidated the archived proof and made closure
impossible.

## Decision

Evaluate the canonical `transition=superseded` predicate before mutation. When
it succeeds, move the Outcome JSON unchanged, preserve its bytes in the archive
manifest, and use a rewritten in-memory copy only to regenerate the derived
Human Benefit Report. Normal Outcomes continue to be rewritten in place.

## Fail-closed boundaries

- A malformed, stale, mismatched, foreign, or non-blocked successor receipt
  cannot enable preservation.
- The Contract, Summary, Outcome Markdown, successor receipt, manifest,
  candidate coverage, rollback, and closure gates remain mandatory.
- Any archive failure restores the original active artifacts and projections.
