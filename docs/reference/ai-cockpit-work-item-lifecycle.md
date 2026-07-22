---
author: Ray
title: AI Cockpit Work Item Lifecycle
description: Deterministic serial execution, budget, and release-evidence rules for governed Work Items.
---

# AI Cockpit Work Item Lifecycle

The default execution unit is one Work Item, one dedicated branch, and one PR. Work Items in a plan are executed serially:

```text
remote base → Contract/Preflight → dedicated branch → implement → ai-finish/archive
  → push → PR/review → merge → ai-close-work-item → synchronize and clean base
  → next Work Item
```

The next Work Item must not start until the predecessor has evidence for all of the following: PR merged, archive succeeded, local branch deleted, remote branch deleted, and local base synchronized with the remote base. A successor Contract may record this evidence in `predecessorWorkItem`; `make check-ai-serial-order` fails closed when any field is absent or false.

## Contract readiness

Active v2 code Contracts must contain concrete problem, constraints, rationale, sources, acceptance, and verification content. Generic starter phrases are rejected by the Contract check before implementation. If Preflight reports `needs_human_confirmation` or `not_ready`, stop and report the reason; do not continue by treating advisory output as authorization.

## Complexity budget

Before implementation, estimate expected changes in the Contract's `budgetImpact`. At finish, `make check-ai-budget-impact` compares the generated complexity report with `.ai/guards/governance_complexity_policy.yaml`. An overrun is permitted only when the Contract explicitly records approval, a repayment Work Item, and repayment records. A separate budget-repair Work Item/PR is the appropriate repayment path when the current Work Item cannot repay its own increase.

## Release evidence states

Release evidence uses three distinct states:

- Historical: an existing archived Work Item or prior release record; preserve it as evidence and do not rewrite it.
- Candidate: a release commit/tag and its generated artifacts are prepared, but publication and source binding are not yet proven.
- Published: the public tag, source commit, release assets, checksums, SBOM, provenance, and release-state checks all point to the same source-bound release.

Do not report a candidate as published. `check-release-distribution` remains the source-bound verification for public release evidence.

## Closure rule

Only after the PR is merged and the Work Item is archived may `make ai-close-work-item TASK=<task>` run. The command owns branch deletion and must fail closed on any lifecycle mismatch. After closure, verify the local base equals the remote base and only then begin the next serial Work Item.
