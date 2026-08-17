---
author: Ray
title: "Verification Evidence Reuse Runtime"
description: "Execution contract connecting evidence reuse decisions to verification nodes."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: reference
capabilityClaims:
  - verification_evidence_reuse_runtime
---

# Verification Evidence Reuse Runtime

## Runtime boundary

`scripts/ai_verify.py` is the supported entry point. It builds a bounded list
of `VerificationNode` values for the requested stage, calls
`plan_verification`, and passes that plan to `execute_verification_plan`.
Planning never executes a command. The adapter invokes exactly the checker
nodes whose plan action is `execute`; it does not call a reused checker.

The receipt file is explicit (`REUSE_RECEIPTS=...` in the Make targets). A
missing or malformed file is an empty receipt map, so every reusable node is
unknown and executes again. A receipt is reusable only when its identity and
all current bindings validate. A local receipt does not satisfy a Hosted
stage/runner.

## Protected gates

The gate classes `security`, `scope`, `governance`, `coverage`, and
`source_bound` are protected. Even a fresh receipt produces an `execute`
decision for these nodes. `protectedNodesSkipped` is therefore a fail-closed
metric and must remain zero in a passing scenario. A generic
`stage_not_applicable` result is not a successful required execution.

## Evidence and metrics

The runtime result records `nodesPlanned`, `nodesExecuted`,
`nodesSkippedReused`, `rerunStale`, `rerunUnknown`,
`protectedNodesExecuted`, `protectedNodesSkipped`, planning time, execution
time, each node action, reason code, and receipt identity. The required cost
observation is an end-to-end adapter test showing fewer actual checker calls
for an unrelated documentation change while protected checker calls remain.

## Adopter parity

The installer catalog copies the runtime module, checker registry, immutable
verification context, evidence binding dependencies, and `ai_verify` entry
point. `templates/make/Makefile.ai` exposes `ai-verify`, `ai-verify-focused`,
and `ai-verify-full` with the same `REUSE_RECEIPTS` override. Parity tests must
assert both the copied scripts and the target surface.
