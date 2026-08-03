---
author: Ray
title: "Work Item Intelligence Interface"
description: "Local, fact-derived Work Item snapshots for external-agent queries."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
lastVerifiedBy: work-item-intelligence-tests
capabilityClaims:
  - work_item_intelligence_interface
---

# Work Item Intelligence Interface

WIII is the authoritative machine-readable projection for a governed Work
Item. It derives a snapshot from Contract, execution facts, evidence,
verification, recorded human decisions, risks, and closure facts. It does not
trust an Agent's declaration of completion.

```text
authoritative facts -> evaluator -> integrity-checked snapshot -> read-only query
```

The interface is repository-local: it neither calls a provider nor starts an
HTTP, WebSocket, webhook, or MCP service. It is not a scheduler, DAG/workflow
engine, retry controller, or agent manager. An external Agent chooses its own
next action from `actionEligibility`; WIII never schedules or retries it.

## Status dimensions

`lifecyclePhase`, `governanceState`, and `activityHealth` are independent.
Activity health is observational only; an idle or stale heartbeat never fails,
cancels, or retries a Work Item. Snapshots include fact counters instead of a
subjective completion percentage, and expose blockers, missing evidence,
dependencies, decisions, risks, verification, eligibility, and a digest.

Local lifecycle observability may emit paired phase measurements for planning,
preflight, implementation, verification, finish, and closure. Each measurement
contains only local elapsed compute, execution count, and cache outcome. Provider
and human wait are `unknown` unless an authoritative source records them; an
unpaired or negative local duration produces no timing claim.

Lifecycle timing is not verification-reuse authorization. The current
source-backed decision keeps every required verification check on its normal
execution path; a future reuse proposal must bind identical source, change-set,
command, environment, toolchain, and policy inputs. See
[`verification-evidence-reuse.md`](verification-evidence-reuse.md).

Verification routing is also observational. `make ai-verify-impact-graph` and
the `impactGraph` field from `ai-verify` describe Fast, Finish, and Hosted
proof layers, dependencies, parallelizable roots, and receipt invalidation;
they never execute a check, schedule a Work Item, or authorize a cache hit.

`completed`, `release_ready`, and `distribution_verified` remain unavailable
until the matching authoritative evidence is present. A Strict Work Item alone
does not imply release verification.

## Commands

```sh
make ai-work-item-status ARGS="--work-item example-task --format json"
make ai-work-item-status ARGS="--work-item example-task --schema-version 2"
make ai-work-item-status ARGS="--list-active --state active"
make ai-work-item-status ARGS="--list-active --pending-human-decisions"
make ai-work-item-status ARGS="--list-active --eligible-action continue"
make ai-work-item-status ARGS="--list-active --after-index-version 42"
make ai-work-item-status ARGS="--list-active --measure"
make ai-work-item-intelligence-rebuild ARGS="--work-item example-task"
```

Queries return `{ok,data,error}`. Exit codes are 0 success, 10 not found, 11
unavailable, 12 inconsistent/tampered, 20 invalid query, 30 invalid data, and
40 internal failure. Code 13 is reserved for a future stale-query policy;
today stale activity is returned as an observational health value and does not
cause a query to fail. Query commands never write facts, refresh a
snapshot, or execute a quality gate. Rebuild is an explicit maintenance
operation, not a query. `--measure` executes repeated local active-list reads
and returns transient min/median/p95/max milliseconds; it persists neither a
benchmark nor a snapshot.

## Storage and compatibility

Runtime data lives under `.ai/work-items/runtime/<id>/`: facts appended through
the CLI writer, a digest-checked derived status projection, optional activity
observation, and an item-local `index-entry.json` publication. A publication
contains a stable `publicationId`, a persisted monotonic cursor, and the
derived snapshot digest. Writers lock only their owning Work Item; publishing
one item never needs a repository-wide index lock.

Before an audit rebuild trusts a fact log, it requires an exact item identity,
unique `factId`, contiguous sequence beginning at one, and a digest matching
the complete fact content. `reducer-state.json` is a digest-bound incremental
reduction checkpoint: ordinary append uses it with the new fact instead of
reparsing the log, while explicit rebuild discards it and audits every fact.
An expired JSON owner lease may be recovered only after its owner PID is no
longer alive; a live owner is never removed even after its lease expires.
These lock records support local crash recovery only and do not imply
distributed locking or scheduler ownership.

`runtime/index-cache.json` (and the compatibility mirror `runtime/index.json`)
are rebuildable aggregates, never the source of truth. Readers enumerate and
verify item-local publications, so they can return an old complete result, a
new complete result, or `inconsistent` if a complete active snapshot lacks its
publication. A malformed or stale cache is recoverable through an explicit
rebuild and cannot silently omit a valid publication. Raw local runtime files
are not immutable or a per-fact tamper-evident ledger, and they are not an
archival rewrite. Existing Markdown Cockpit Status remains the canonical
human-facing generated projection; WIII is authoritative for machine queries.

The snapshot shape is described by
`.ai/schemas/work-item-intelligence-snapshot.schema.json`. Schema version 1
remains the default compatibility view. Schema version 2 is opt-in through
`--schema-version 2` and adds `versions`, `sourceValidation`, `subjects`, and
`openEntities`.
Its `versions.governance` and `versions.sourceSequence` advance only for
source-bound governance facts; `versions.runtimeObservation` tracks runtime
observations separately. Rebuilding unchanged facts preserves these counters.
It also preserves that publication's cursor and identifier; a new fact creates
a new publication that advances the active-list cursor.

A source-bound V2 fact carries a payload `subject` (`kind`, `id`) and
`sourceRef` (`kind`, local `path`, `sha256:` digest). WIII reads the local
source and checks its digest before using that source-bound fact as valid V2
governance evidence. Missing, unreadable, malformed, or digest-mismatched
sources yield an explicit V2 `inconsistent` governance state rather than a
trusted result. Legacy V1 facts remain available through schema version 1;
they are not retroactively presented as source-bound evidence.

## Keyed open entities

V2 reduces verification failures, human decision requests, and missing
dependencies as open entities keyed by `subject.kind` and `subject.id`. A
matching `verification_passed`, `human_decision_recorded`, or
`dependency_satisfied` fact must name the exact `resolves` value (`kind:id`)
and carry the same subject. It closes only that entity. Missing, unknown,
malformed, or cross-subject resolution references yield `inconsistent` rather
than clearing a blocker. `openEntities` reports remaining keyed blockers. A
`closed` fact projects `closed` only when no keyed open entity remains. The V1
compatibility view omits these V2-only fields.

## Governance, runtime, and completion domains

V2 keeps authoritative governance separate from runtime observation. The
`governance` object contains lifecycle phase, governance state, and governance
version; `runtimeObservation` contains activity health and its independent
version. A heartbeat or activity-health change cannot change governance state
or governance version.

`completion` exposes five independent booleans: `implementation`,
`verification`, `review`, `integration`, and `closure`. They report observed
evidence and are not a claim that an external scheduler or release workflow
ran. `governancePermissions` is a bounded list of currently eligible phase
actions: `start`, `continue`, `run_verification`, `request_human_decision`,
`finish`, and `close`. It never contains `retry` or `cancel`. Schema version 1
continues to omit all four V2-only objects.

Do not record tokens, passwords, secrets, full environment values, private
human notes, or external response bodies in facts.

## Reproducible performance characterization

`scripts/ai_work_item_intelligence_benchmark.py` measures the V2 active-list
query against fixtures created only below its required `--root` directory. It
does not alter this repository's runtime data and it does not establish an
enforcement threshold. Each published case records W (Work Items), F (fixture
facts), concurrency, cold/warm mode, Python and filesystem identifiers, 30 or
more samples, p50/p95/p99 latency, timeout count, lock wait, and bytes written.

Run the full declared matrix with a disposable root and save the JSON outside
the repository runtime tree:

```sh
python scripts/ai_work_item_intelligence_benchmark.py \
  --root /tmp/wiii-benchmark --output /tmp/wiii-benchmark-report.json
```

The companion performance baseline records the exact profile and observed
local values. Those values are evidence for this environment only, not a
cross-machine product guarantee.
