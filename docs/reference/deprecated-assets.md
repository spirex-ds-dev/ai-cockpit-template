---
author: Ray
title: "Deprecated Assets and Archive Hygiene"
description: "Registry and fail-closed boundaries for deprecation candidates and immutable archive evidence."
keywords:
  - ai-cockpit
  - deprecated-assets
  - archive
  - governance
---

# Deprecated Assets and Archive Hygiene

[`deprecated-assets-registry.json`](deprecated-assets-registry.json) is the
machine-readable inventory for deprecation candidates. Each entry records its
replacement, dates, references, runtime use, migration need, and reason.

Run `make check-deprecated-assets` before proposing cleanup. The check validates
references and stale dates, and it fails closed when protected archive evidence
could be treated as deletable. Passing this check does not delete anything and
does not complete the execution-plan cleanup reserved for WI-18.

## Current-facing command-chain guard

The registry also declares the maintained Agent-facing scan surface and the obsolete `make quality → make staging → make ai-finish` shell chain. That chain is unreachable in current guidance and must not be restored: `ai-finish` owns the required local quality and governance verification, and staging is not a lifecycle prerequisite. Use the canonical order in [`docs/operations/work-item-lifecycle.md`](../operations/work-item-lifecycle.md) instead.

`make check-deprecated-assets` scans only declared current-facing text assets. It excludes immutable archives, decisions, events, release evidence, historical release notes, and plan history; it never changes any of them. A prohibited chain in a declared current-facing path fails the quality gate with the path and registry candidate ID. The registry records the candidate's source, reachability, replacement, active references, and regression impact so an absence is not mistaken for an unreviewed deletion.

Contracts, Summaries, Events, Manifests, release evidence, decision evidence,
and other historical records remain preserved. Any future deletion requires a
separate Work Item with explicit scope, recovery path, replacement evidence,
PR review, merge, and lifecycle closure.

## Current pre-release audit boundary

The earlier historicalization commit is retained as a historical repository
fact. It did not establish a standalone pull-request, hosted-verification, and
lifecycle-closure record, so it must not be described as a completed governed
delivery. The replacement audit
`pre-release-deprecated-assets-lifecycle-audit-replacement-20260731` records
the current classification and creates that new reviewable lifecycle without
rewriting the older archive evidence.
