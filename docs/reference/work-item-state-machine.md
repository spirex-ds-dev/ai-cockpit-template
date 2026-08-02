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

The canonical lifecycle vocabulary and transition decision are owned by
`scripts/ai_domain_model.py`. It defines the typed core objects used at this
boundary: Work Item, Contract, Evidence, Receipt, Decision, Transition,
Finding, Risk, Human Decision, Capability Claim, and Closure.
`scripts/ai_work_item_state.py` is a deliberately thin compatibility adapter:
it preserves the established JSON-compatible CLI while delegating transition
and recovery decisions to the domain service. It must not define another state
graph or evidence rule.

The canonical path is:

`created → preflight_ready → implementation_active → verification_pending → finish_ready → archived → pushed → pr_open → merged → close_authorized → closed`

`paused`, `blocked`, `cancelled`, `rollback`, and `stale` are recovery states. They never imply completion. A transition is accepted only when its predecessor is correct and the required evidence has a non-empty digest. Stale, contradictory, partial, or locally/ remotely inconsistent evidence fails closed with a resume condition.

Repeated identical events are idempotent: they return the same deterministic event ID and do not authorize duplicate archive or cleanup. Interrupted work recovers to `paused`; inconsistent provider or base evidence recovers to `stale`. Provider identity, enterprise approval, and production readiness remain outside this local evaluator.

This is a bounded migration, not a claim that every historical governance
script has been rewritten. New lifecycle consumers must use the domain service
rather than copying its state or evidence vocabulary.

Run the focused tests with:

```sh
pytest -q tests/test_domain_model.py tests/test_work_item_state_machine.py
```
