---
author: Ray
title: Work Item Intelligence Interface
description: Local fact-derived Work Item Intelligence Interface specification.
status: current
instructional: false
---

# Work Item Intelligence Interface (WIII)

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Purpose

Expose a trustworthy, local, read-only intelligence view of governed Work Items
to external agents. The interface improves decision quality; it is not an agent
runtime or a workflow controller.

## Decision model

```text
Contract + Execution Facts + Evidence + Verification + Human Decisions + Risks + Closure Facts
  -> Status Evaluator
  -> Work Item Intelligence Snapshot
  -> Agent query
```

Snapshots are derived from facts. Agents cannot write a terminal governance
state, self-assert `completed`, `release_ready`, or `distribution_verified`, or
let an activity heartbeat change governance state.

## Required dimensions

Each snapshot exposes independent lifecycle phase, governance state, and
activity health. It also includes identity, fact progress counters, stable
blocking and missing-evidence reasons, dependencies, human decisions, risks,
verification, action eligibility, current activity, and integrity metadata
(`statusVersion`, `factSequence`, `lastFactId`, `snapshotDigest`).

Lifecycle phases are `intake`, `preflight`, `implementation`, `verification`,
`review`, `finish`, `closure`, and `closed`. Governance state and activity
health remain separate. Stale activity never automatically fails, cancels, or
retries a Work Item.

## Local storage and queries

Runtime data is local and per Work Item under
`.ai/work-items/runtime/<id>/`, with an append-only `facts.jsonl`, derived
`status.json`, optional `activity.json`, and a lock. An incremental
`.ai/work-items/runtime/index.json` supports listings and cursors. Snapshots and
the index must be digest-checked and rebuildable from authoritative facts.

Phase 1 supports a single JSON status query, active list, state filtering,
pending-human-decision filtering, action-eligibility filtering, and
index-version deltas through `make ai-work-item-status` and
`scripts/ai_work_item_status.py`. Responses use `{ok,data,error}` and stable
errors/exit codes. Queries never mutate storage or run quality gates.

## Boundaries

No HTTP/WebSocket/webhook/MCP server, scheduler, DAG engine, workflow engine,
retry controller, agent manager, provider configuration, provider identity, or
historical archive rewrite is part of WIII. Existing Markdown Cockpit Status
remains a compatibility projection; the derived snapshot is authoritative for
the new interface.

## Verification

Tests cover fact-derived state, stale/missing/rejected evidence, dependency and
human-decision behavior, heartbeat separation, read-only queries, multiple
Work Item isolation, tamper detection/rebuild, concurrency, compatibility, and
measured local baseline output. No performance target is claimed without a
recorded local measurement.
