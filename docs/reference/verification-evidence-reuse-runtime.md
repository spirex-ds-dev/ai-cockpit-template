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

## Concrete checker mapping

Reuse classes are dimensions of an existing runtime node; they are not
additional checker ids. `runtime_nodes()` in `scripts/ai_verify.py` keeps the
stage checker ids unchanged: task uses `scope, tests`, PR uses
`scope, tests, trust`, and release uses `scope, tests, trust, identity,
supply_chain`.

| Existing checker id | Runtime mapping | Reuse policy |
| --- | --- | --- |
| `tests` | One concrete `CheckerRegistry` node with `content-bound`, `diff-bound`, and `environment-bound` binding dimensions | A receipt is reusable only when all three digests, plus the normal receipt identity, match; a diff or environment change executes the existing `tests` checker again. |
| `scope` | Existing scope gate node | Protected; always executes. |
| `trust`, `identity`, `supply_chain` | Existing security gate nodes | Protected; always execute in their existing PR/release stages. |

The `binding_classes` field on `VerificationNode` carries the additional
dimensions for the one `tests` node. `create_receipt()` writes all required
binding digests, and `_receipt_state()` requires all of them to match before
`consume_runtime_plan()` can skip the node. The adapter calls
`registry.run([decision.node_id], ...)`, so both changed-binding executions
resolve to the concrete existing `tests` id. No `diff` or `environment`
checker id is registered or generated.

The command-line entry point intentionally constructs an empty registry in
this template, so an unconfigured CLI run reports `stage_not_applicable` for
the stage ids; that is not execution evidence. The registry evidence is the
injected `CheckerRegistry` path covered by `tests/test_ai_verify.py`, which
registers the existing `tests`/`scope`/`trust`/`identity`/`supply_chain` ids,
observes the callback id on changed diff/environment inputs, and verifies the
unchanged receipt skip. The CLI evidence is limited to confirming that its
runtime plan contains only the existing stage ids.

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
