---
author: Ray
title: "RFE-101 Pre-Archive Human Outcome Gate"
description: "Make human-readable Task Outcome delivery precede explicit archive without inventing chat-delivery evidence."
---

# RFE-101: Pre-Archive Human Outcome Gate

Work Item: `rfe-101-prearchive-outcome-gate-20260729`

## Problem

RFE-100 demonstrated two gaps. `make ai-finish` archived by default, so a
validated Outcome could move from active state before the agent reported it to
the user. Its generated report also omitted structured Summary findings and
residual risks, reducing an evidence file to an unhelpful success-shaped path.

## Decision

`ai-finish` will validate and preserve an active Outcome by default, print a
clearly delimited report for the agent to relay in the conversation, and state
that archive is a separate explicit lifecycle action. Repository code cannot
attest that a particular human saw a chat message; the agent protocol performs
that final delivery. Archive remains immutable once performed.

## Implementation Steps

1. Add red tests for default active preservation, explicit archive, stdout
   report boundary, and evidence-derived finding/risk projection.
2. Change finish defaults and Make help without weakening validation or archive
   transaction checks.
3. Extend the Outcome generator/renderer only from structured Summary data;
   preserve no-score, redaction, and conditional-impact boundaries.
4. Update plan, traceability, context registry, Capability Truth, and the
   source-bound Japanese assessment with official generators.
5. Run focused tests, full quality, `ai-finish --no-archive`, directly relay
   the active Outcome, then use explicit archive and complete the PR lifecycle.

## Non-Goals

- No automatic external-chat transmission or identity attestation.
- No change to immutable RFE-099 or RFE-100 archive bytes.
- No release, merge, or branch cleanup in this corrective implementation.

## Acceptance Mapping

| Requirement | Evidence |
| --- | --- |
| Default finish keeps active review point | `tests/test_finish_e2e.py` |
| Explicit archive remains separate | `tests/test_finish_e2e.py` |
| Human Outcome has recorded findings/risks | `tests/test_task_outcome_generator.py` and `tests/test_task_outcome_ai_finish_integration.py` |
| Conversation boundary is not overclaimed | `scripts/ai_finish.py`, this plan, and rendered output tests |
| Source-bound documentation remains aligned | official truth/Japanese generators and full quality |
