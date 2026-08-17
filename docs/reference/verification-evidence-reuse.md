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

The pure evidence-binding classifiers decide whether a receipt is fresh, stale,
or unknown. The runtime planner now consumes that decision. It may skip only an
allowlisted non-protected node when the receipt is a passed, non-expired,
content/diff/environment-bound result whose command, scope, governance,
environment, toolchain, policy, stage, runner, and output identities match.

The planner is not a cache telemetry layer: `ai_verify` passes the plan to the
bounded execution adapter. A fresh reusable node is not called; an unknown or
stale node is called again. Security, scope, governance, coverage, and
source-bound gates are always called. The adapter reports planned, executed,
skipped, stale-rerun, unknown-rerun, and protected-node metrics so a reduced
execution count is observable rather than inferred.

## Evidence considered

The archived `work-item-lifecycle-timing` Summary records local lifecycle
measurements but deliberately leaves provider and human wait unknown. Its PR
`#596` hosted `template-smoke` quality step ran from `2026-08-03T06:52:21Z`
to `2026-08-03T07:01:13Z` and reported `1979 passed` in `514.92s`. That is a
single complete-quality observation, not two comparable executions of the
same verification node with the same receipt bindings.

`scripts/ai_verification_context.py` reads a current working-tree diff and
policy inputs into an immutable in-memory context. `scripts/ai_verify.py`
creates `VerificationNode` candidates, validates an explicit receipt map, and
executes the resulting plan through the checker registry. Missing or malformed
receipt files are treated as unknown evidence and do not authorize a skip.

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

No provider timing or human-wait reduction is asserted here. The material
benefit criterion for this runtime boundary is actual adapter call-count
reduction for an unrelated documentation change while protected execution is
unchanged. The installed `Makefile.ai`, catalog, runtime modules, and parity
tests carry the same boundary into future adopter projects.
