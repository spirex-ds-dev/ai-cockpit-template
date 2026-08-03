---
author: Ray
title: "Verification Evidence Reuse Decision"
description: "Source-backed decision boundary for future verification-evidence reuse."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
capabilityClaims:
  - work_item_intelligence_interface
---

# Verification Evidence Reuse Decision

## Decision

No content-addressed verification receipt or reuse path is added by this Work
Item. Every required verification check continues to execute normally.

This is a no-change decision, not a claim that reuse is impossible forever.
It prevents a cost observation from being mistaken for evidence that a check
may safely be skipped.

## Evidence considered

The archived `work-item-lifecycle-timing` Summary records local lifecycle
measurements but deliberately leaves provider and human wait unknown. Its PR
`#596` hosted `template-smoke` quality step ran from `2026-08-03T06:52:21Z`
to `2026-08-03T07:01:13Z` and reported `1979 passed` in `514.92s`. That is a
single complete-quality observation, not two comparable executions of the
same verification node with the same receipt bindings.

`scripts/ai_verification_context.py` reads a current working-tree diff and
policy inputs into an immutable in-memory context. It does not persist a
receipt identity. `scripts/ai_verify.py` selects and executes declared stages;
it contains no reuse cache or receipt-validation path. The present behavior is
therefore normal execution, and this Work Item preserves it.

## Binding requirements for a future reuse proposal

A later Work Item may propose reuse only after it defines a content-addressed
receipt whose validity requires exact equality for every one of these inputs:

| Binding | Required value |
| --- | --- |
| Source revision | `baseCommit` and `headCommit` |
| Change set | normalized changed-path set and its digest |
| Verification invocation | exact command and command digest |
| Execution environment | environment descriptor digest |
| Toolchain | version-manifest or toolchain digest |
| Governing policy | verification-policy digest |

Changing any binding must invalidate the candidate receipt and cause the
required check to execute normally. A later implementation must add a failing
test for a valid reusable receipt and an invalidation test for each binding;
it must not infer safety from elapsed time, cache labels, or a provider result.

## Limits and next evidence threshold

No cache hit, provider timing, human wait, reuse policy, or verification-cost
budget is asserted here. Before this boundary can change, an independent Work
Item needs comparable source-bound receipts with identical bindings, an
explicit material-benefit criterion, and the invalidation coverage above.
