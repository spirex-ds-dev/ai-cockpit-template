---
author: Ray
title: "RFE-082 Release Truth Reconciliation Plan"
description: TDD and lifecycle plan for v0.5.45 candidate truth and obsolete-path retirement.
---

# RFE-082 Release Truth Reconciliation Plan

## Goal

Prepare a truthful v0.5.45 candidate without conflating reserved tags with
stable provider Releases, without carrying a stale source SHA, and without
leaving the obsolete #401 execution path available.

## Instruction → plan → implementation → acceptance

| Instruction | Plan | Implementation | Acceptance |
| --- | --- | --- | --- |
| Fix the process permanently | Model tag reservation and provider publication separately | Distribution provider-fact parsing and diagnostics | Tag-only v0.5.44 is reserved but never called published |
| The next candidate may be v0.5.45 | Advance after every unavailable immutable version | Candidate/state sequence validation | v0.5.44 reuse fails; v0.5.45 passes |
| Do not bind stale evidence | Defer source identity until finalization | Canonical source-binding state | Prepared candidate has no false exact-source claim |
| Remove old callable paths | Retire #401 while preserving audit history | Close PR; delete exact local/remote branch | #401 closed and both branches absent |
| Prevent instruction omissions | Bind directive, files, negative tests, and lifecycle | Traceability registry, Contract, Summary | Machine traceability and full Work Item lifecycle pass |

## Tasks

1. Add red tests for stable provider Releases, draft/prerelease exclusion,
   malformed payloads, tag-only reservation, stale projection diagnostics, and
   exact v0.5.45 progression.
2. Add red state tests for duplicate/reused/unexplained quarantine tags and
   deferred versus exact source binding.
3. Implement provider-fact classification and update distribution paths to use
   stable Releases for publication and all tags for reservation.
4. Advance `next-release.json` and canonical state to v0.5.45, refresh current
   candidate supply-chain metadata, and recompute projection digests.
5. Update distribution documentation, parent issue history, machine
   traceability, Contract, and Summary.
6. Close obsolete PR #401 with a replacement record and delete its exact local
   and remote branch; do not alter any version tag or Release.
7. Run focused tests, state/preparation checks, full quality, `ai-finish`,
   archive, aggregate PR validation, Hosted CI, merge,
   `ai-close-work-item`, and branch cleanup.

## Verification boundary

The normal and post-publication distribution checks may continue to reject
historical public evidence until a new valid release exists. This Work Item
must make those failures accurate and make preparation deterministic; it must
not hide the release blocker by claiming old provider state is valid.

## Next stage

Japanese assessment remains blocked until this Work Item, its PR, and all
branch cleanup are complete.
