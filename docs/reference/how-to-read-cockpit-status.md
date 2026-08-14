---
title: "How to Read Cockpit Status"
description: "Translate generated status into a human decision."
author: Ray
audience:
  - adopter
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# How to Read Cockpit Status

## Purpose
Turn the generated status into an understandable, bounded decision.

## Audience
Anyone reviewing a Work Item, including non-technical approvers.

## Outcome
You can read the conclusion, evidence, risk, and next action without guessing.

## Scenario
Read the active status after preflight, verification, finish, or a failed gate.

## Decision
Read in this order: `Key Conclusion`, `Recommendation`, `Decision Drivers`, `Evidence`, then `Scenario Coverage`. Color is a semantic signal, not a score.

| Color | Human decision | Safe next action |
| --- | --- | --- |
| Green | Evidence is sufficient for review; decide whether to proceed. | Review the named evidence. Do not treat it as merge or release authorization. |
| Yellow | Residual risk or incomplete evidence needs a conscious decision. | Read the risk and drivers; investigate or record the decision. |
| Red | A hard blocker or ambiguity requires stopping. | Stop and follow the stated recovery condition. |
| Unknown | The signal is not reliable enough to interpret. | Ask for clarification or the missing evidence. |

## Stop conditions
If status is stale, malformed, cross-task, or missing its evidence, do not edit it by hand and do not guess. Generated status is a projection of Contract, Summary, and checks.

## Next steps
1. Apply [Decision States](../concepts/decision-states.md).
2. Follow [Work Item Lifecycle](../operations/work-item-lifecycle.md).
3. Use [Recovery](../operations/recovery.md) for a stop.
