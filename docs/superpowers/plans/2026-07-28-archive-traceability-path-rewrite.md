---
author: Ray
title: "Archive Traceability Path Rewrite"
description: Implement an atomic active-to-archive Contract reference migration for registered instruction traceability evidence.
keywords:
  - ai-cockpit
  - archive
  - traceability
  - rollback
  - work-item
---

# Archive Traceability Path Rewrite
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Purpose

Close `RFE-ISSUE-080`. A Work Item may correctly reference its active Contract
from `docs/reference/remediation-instruction-traceability.json` while work is in
progress. Archival moves the Contract but currently leaves the external
reference stale, so every lifecycle depends on a manual post-archive edit.

## Boundary

The archive transaction may rewrite only exact string occurrences of its own
repository-relative active Contract path in the registered mutable traceability
manifest. It must not rewrite similar names, unrelated active paths, historical
archive paths, verification commands, Summary execution evidence, or immutable
archive bundles.

An absent registered manifest or a valid manifest without the current path is a
no-op. A malformed registered manifest fails before active files move. If a
later transaction step fails, the original manifest bytes are restored together
with the existing Contract, Summary, index, status, and partial-artifact
rollback.

## Instruction → plan → implementation → acceptance

1. Add red-first archive tests for exact duplicate references, lookalikes,
   no-reference input, malformed JSON, and a failure after external rewrite.
2. Capture the traceability manifest's original bytes before archive mutation.
3. Recursively replace only the exact current Contract path and atomically
   persist only when at least one replacement occurs.
4. Add the generated manifest change to archived Summary ownership and preserve
   execution evidence unchanged.
5. Restore the original bytes on every exception after mutation.
6. Run focused tests, real post-archive traceability/status checks, full quality,
   archive, committed PR validation, Hosted CI, merge, closure, and cleanup.

## Serial order

This corrective is the first item in “other process issues and RFE-ISSUE-082”.
`RFE-ISSUE-147` and then `RFE-ISSUE-082` remain blocked until this Work Item is
fully merged, closed, and cleaned.
