---
title: "Recovery"
description: "A fail-closed route for a stopped or failed Work Item."
author: Ray
audience:
  - contributor
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Recovery

## Purpose
Turn a stop into a bounded retry instead of an improvised workaround.

## Audience
Contributors and maintainers responsible for a stopped Work Item.

## Outcome
You preserve evidence, repair the named gap, and retry only the affected stage.

## Scenario
Use recovery after preflight, verification, hosted verification, or closure stops.

## Decision
1. Read the stop reason and recovery condition.
2. Preserve the Contract, Summary, branch, checkout, and failing output.
3. Make only an in-scope repair; update evidence.
4. Rerun the failed gate, then the declared aggregate checks.
5. Ask for human review again if the decision state changes.

## Stop conditions
Do not bypass a gate, guess from another Work Item's status, substitute local evidence for hosted evidence, or delete the checkout after a remote failure. If the condition is unclear, stop and ask for clarification.

## Next steps
1. Re-read [Decision States](../concepts/decision-states.md).
2. Follow [Work Item Lifecycle](work-item-lifecycle.md).
3. For installation symptoms, use [Installation Troubleshooting](../troubleshooting/installation.md).
