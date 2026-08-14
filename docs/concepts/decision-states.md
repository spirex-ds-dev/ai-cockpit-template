---
title: "Decision States"
description: "A plain-language route from evidence to a human decision."
author: Ray
audience:
  - adopter
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Decision States

## Purpose
Help a non-technical reader decide whether to review, investigate, or stop.

## Audience
Adopters, contributors, maintainers, and reviewers.

## Outcome
You can name the state, the human decision it requires, and the safe next action.

## Scenario
Open `.ai/cockpit/current_status.md` after a check, preflight, or finish step.

## Decision

| State | What it means | Human decision | Safe next action |
| --- | --- | --- | --- |
| Green | Required evidence is current and the bounded action is supported. | Review the evidence and decide whether to proceed. | Follow the declared next step; green never authorizes merge or release by itself. |
| Yellow | Evidence is incomplete, stale, contradictory, or has residual risk. | Decide whether to investigate, record the risk, or stop. | Read the named drivers and repair or document the gap. |
| Red | A required control failed, scope was exceeded, or authority is missing. | Stop. Decide only how to satisfy the recovery condition. | Preserve the Work Item and resolve the stated blocker. |
| Unknown | The evidence cannot be interpreted reliably. | Do not make a progress decision. | Ask for the missing source or human clarification. |

## Stop conditions
Never guess from a color, copy another task's status, or treat agent prose as proof. A stop is successful when its missing evidence and recovery condition are explicit.

## Next steps
1. Read [How to Read Cockpit Status](../reference/how-to-read-cockpit-status.md).
2. Follow the [Work Item Lifecycle](../operations/work-item-lifecycle.md).
3. If stopped, use [Recovery](../operations/recovery.md).
