---
title: "WI-22 Outcome Section Projection Audit"
author: "AI Cockpit"
description: "Evidence-bound audit of the WI-22 human Outcome section projection correction."
workItemId: wi-22-outcome-section-projection
status: in_progress
---

# WI-22 Outcome Section Projection Audit

## Finding

The archived WI-21 Outcome contains evidence-bound `humanHandoff` resolution and risk claims, while its generic top-level `Resolutions` and `Residual Risks` sections render `None`. Its Human Decisions section also repeats the same confirmation. The source is [the archived WI-21 Outcome](../../.ai/work-items/archive/2026/wi-21-outcome-resolution-projection.outcome.md).

## Correction boundary

- `resolutions` and `handoffRisks` are normalized into top-level sections.
- Markdown renders problem, action, verification, and risk detail.
- Duplicate decisions are removed in first-seen order.
- Claims without evidence remain `inference`.
- WI-01 through WI-21 archives remain immutable.

## Verification plan

Focused generator and `ai-finish` tests cover resolved, unresolved, malformed, and duplicate inputs. Full governed verification must bind the final implementation, generated evidence, archive digest comparison, and hosted checks.
