---
author: Ray
title: "Work Item State Machine and Recovery"
description: "Deterministic local lifecycle transition and recovery boundary."
keywords:
  - work-item
  - lifecycle
  - recovery
---

# Work Item State Machine and Recovery

The governed lifecycle is modeled by `scripts/ai_work_item_state.py`. The canonical path is:

`created → preflight_ready → implementation_active → verification_pending → finish_ready → archived → pushed → pr_open → merged → close_authorized → closed`

`paused`, `blocked`, `cancelled`, `rollback`, and `stale` are recovery states. They never imply completion. A transition is accepted only when its predecessor is correct and the required evidence has a non-empty digest. Stale, contradictory, partial, or locally/ remotely inconsistent evidence fails closed with a resume condition.

Repeated identical events are idempotent: they return the same deterministic event ID and do not authorize duplicate archive or cleanup. Interrupted work recovers to `paused`; inconsistent provider or base evidence recovers to `stale`. Provider identity, enterprise approval, and production readiness remain outside this local evaluator.

Run the focused tests with `pytest -q tests/test_work_item_state_machine.py`.
