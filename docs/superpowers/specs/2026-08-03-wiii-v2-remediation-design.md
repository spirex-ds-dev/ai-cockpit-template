---
author: Ray
title: "Work Item Intelligence V2 remediation design"
description: "Evidence-backed evolution of the local Work Item Intelligence interface."
status: proposed
---

# Work Item Intelligence V2 remediation design

## Decision

Evolve Work Item Intelligence (WIII) in small, evidence-bound Work Items. The
first implementation objective is correctness of the current open state; scale
and verification-cost work follows only after reproducible measurement. WIII
remains a repository-local query/projection interface. It must not become a
scheduler, retry controller, workflow engine, agent manager, remote service, or
source of provider truth.

The V2 response is additive while V1 consumers exist: the CLI will retain a V1
response mode during the migration and expose V2 explicitly. The final audit
will decide, from consumer and installer evidence, whether V2 can become the
default. No Work Item may silently change a documented snapshot contract.

## Assessment disposition

| Finding | Disposition | Implementation evidence | Existing test evidence or gap | Design response |
| --- | --- | --- | --- | --- |
| Query CLI, error envelope, read-only queries, and explicit rebuild exist | Confirmed | `scripts/ai_work_item_status.py`, `docs/reference/work-item-intelligence-interface.md` | `tests/test_work_item_intelligence_integration.py` covers the envelope and read query delegation | Preserve these boundary properties. |
| Lifecycle integration is complete | Partly confirmed | Start, preflight, checkpoint, finish, archive, and close emit only a small set of positive facts | No test proves not-ready, decision, dependency, verification-failure, or closure-start projection; Tasks 1–3 add them | Add typed, source-bound lifecycle projections and invalidation paths. |
| `statusVersion` is not implemented | Confirmed | `snapshot()` writes `statusVersion: 1` | No increment/no-op-rebuild test; Task 1 adds both | Add independent governance, runtime-observation, and source-sequence versions. |
| Existing optimistic concurrency is broken | Partly confirmed | There is no expected-version mutation API or stale-write rejection | No mutation API test exists because no such API exists | Do not claim OCC; reserve an expected-version guard for any future mutation API. |
| Recoverable states are reduced as historical type presence | Confirmed | `_state()` checks `verification_failed`, decision, and dependency fact types globally | `tests/test_work_item_intelligence.py` covers one dependency and one decision only; no failed-to-passed or multi-entity test | Reduce keyed open entities with resolution/supersession, not historical existence. |
| Facts duplicate authority and can drift | Confirmed | Rebuild reads only `facts.jsonl`; raw facts do not validate Contract, Summary, Receipt, or Closure sources | Existing tamper test changes derived status/index only; no source-drift test | Make facts minimal source-bound projections and fail closed on source mismatch. |
| Global index serializes independent writes | Confirmed | Shared `index.lock` covers append, full reduction, and full index rewrite | Existing concurrency test writes one Work Item only; no cross-item contention test | Publish a per-item entry and make aggregate index a rebuildable cache. |
| Lock order is Work Item then index | Unconfirmed | Implementation takes index lock first | No lock-order assertion exists; Task 5 documents/removes the shared write path | Correct documentation; retain a single documented lock order until the shared lock is removed. |
| Facts are re-read and duplicate checks are quadratic | Confirmed | `read_facts()` scans prior rows for every row; append and rebuild both read | Existing measure test only asserts a non-negative result; Task 4/6 add scale evidence | Use sequence metadata, set-based validation, incremental reduction, and audit rebuild. |
| `actionEligibility` already schedules retries/cancels | Partly confirmed | The field names orchestration actions, but retry/cancel are never eligible | Existing state test verifies decision eligibility, not retry/cancel absence | Replace with governance permissions and document that consumers choose their own actions. |
| Activity changes governance | Unconfirmed | Activity shares a status object but reducer excludes it | `test_dependencies_decisions_and_activity_remain_independent` proves stale activity leaves governance unchanged | Separate the data domains and versions to prevent consumer confusion. |
| Completion state lacks independently useful milestones | Confirmed | Current reducer does not expose implementation, verification, review, integration, and closure completion separately | No completion-matrix test exists; Task 3 adds one | Add a completion matrix. |
| Current latency targets are established product budgets | Unconfirmed | Existing measurement is a small read-only baseline, not a scale budget | `measure_query_baseline` test uses three rounds and only checks a non-negative P95 | Characterize first; make targets profile-bound only after sufficient samples. |
| Repeated verification and total Work Item duration are not modeled | Confirmed | Quality receipts exist, but no lifecycle phase/wait/retry model exists | No end-to-end timing test exists; Task 7 adds it | Add lifecycle timing before receipt reuse or impact-DAG policy. |

## V2 model

### Authoritative input and projection

An event recorded by WIII is a projection, not an independent assertion of
repository truth. Each governance-relevant event carries:

```json
{
  "factType": "verification_state",
  "subject": {"kind": "verification", "id": "quality"},
  "state": "open",
  "sourceRef": {
    "kind": "verification_receipt",
    "path": "target/quality-receipt.json",
    "digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
  }
}
```

The reducer validates that the source exists where the source is expected to be
available, matches its recorded digest, and belongs to the Work Item. A missing
or changed source produces `inconsistent`; it never silently keeps a positive
derived state. Runtime observations remain explicitly non-authoritative and are
not source evidence for governance transitions.

### Open entities

Verification issues, decisions, dependencies, blockers, and claims are keyed
entities. An entity is open until a later source-bound fact with the same
`subject.kind` and `subject.id` records `resolved`, `satisfied`, or
`superseded`, together with `resolvesFactId` where applicable. The reducer
derives state only from current entities. This permits a failed verification to
pass later, one of several decisions to remain pending, and a missing
dependency to become satisfied.

### Versions and cursor

V2 has monotonic persisted counters, not wall-clock versions:

```json
{
  "versions": {
    "governance": 12,
    "runtimeObservation": 37,
    "sourceSequence": 142
  }
}
```

Governance increments only when the externally visible governance projection
changes. Runtime observation changes do not increment governance. Source
sequence follows accepted fact order. An unchanged rebuild preserves all three
versions. The active-list cursor is a persisted monotonic publication sequence
and can return only a complete old publication, a complete new publication, or
an explicit `inconsistent` result.

### API boundary

V2 groups authoritative data under `governance` and non-authoritative data
under `runtimeObservation`. `actionEligibility` becomes
`governancePermissions`, limited to whether governance permits implementation,
verification, finish, or closure. It does not tell an agent to retry, cancel,
or schedule work. The V1 adapter remains during migration and cannot fabricate
states that V2 has marked inconsistent.

### Storage and recovery

Each Work Item owns facts, snapshot, metadata, and a compact
`index-entry.json`. A writer updates only that item under its item lock.
`index-cache.json` is optional and rebuildable; it is never authoritative for a
single Work Item. The publication protocol binds snapshot and index entry to a
shared item publication id. Readers validate that binding. Recovery rebuilds
from every valid per-item entry; it must not replace a multi-item cache with a
single entry after corruption. Lock recovery uses an owner/lease or an OS lock
with tests proving it never breaks a live writer.

### Measurement and verification efficiency

The characterization Work Item measures warm/cold reads, writes, lock wait,
timeouts, bytes written, and rebuild cost for declared workloads with at least
30 samples. Candidate budgets become enforceable only when the measurement
documents machine, filesystem, Python version, workload, and profile.

Lifecycle timing is separate from WIII state correctness. It records active
compute, human wait, provider wait, repeated execution, cache outcome, and
phase boundaries. Only then may receipt content addressing and an
impact-scoped verification graph be implemented. Evidence reuse may reuse a
valid receipt; it must never omit a required check when its binding inputs have
changed.

## Delivery order

```text
design → source/version foundation → keyed reducer → API boundary
      → characterization → per-item publication → linear reduction/recovery
      → lifecycle timing → receipt reuse decision → integration truth audit
```

The first four are semantically coupled and merge serially. Characterization
research and later test-design review can use sub-agents in parallel, but no
two Work Items may concurrently archive, merge, or run `ai-close-work-item`:
they share generated archive/status ownership and the remote base advances
after every merge.

## Completion evidence

This design Work Item is complete only when its companion plan names exact
successor scopes, interfaces, tests, verification, lifecycle closure sequence,
and the measurable evidence each final claim requires. It does not claim any
V2 behavior is implemented.
