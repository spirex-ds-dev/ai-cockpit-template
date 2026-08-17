---
title: "Work Item Lifecycle"
description: "The safe sequence for one governed change."
author: Ray
audience:
  - contributor
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Work Item Lifecycle

<!-- governance-flow: install,configure-work-item,onboard,doctor,calibrate,confirm,validate,readiness,develop -->

## Purpose
Make the order of human and agent work visible so a reader never skips a control.

## Audience
Contributors, maintainers, and reviewers.

## Outcome
You know when to continue, when to pause, and when a Work Item is truly closed.

## Scenario
Use this route for one change from a trusted base to merged cleanup.

## Decision
`latest remote base → Contract → preflight → implementation → verification → Summary/Outcome → archive → commit/push → PR → merge → closure → cleanup`.

Each Work Item has one Contract, one dedicated branch, and one PR. Independent Work Items may be active concurrently only when their branch and worktree, declared scope, evidence ownership, and shared serialized-projection constraints are compatible. The Agent/Orchestrator owns the scheduling and projection-lease coordination; governance gates remain fail-closed. A blocked Work Item does not block an independent compatible Work Item. Parallel execution does not combine Work Item identities, and shared branch-integrated projections remain serialized against the closed projection inventory. `ai-finish` archives evidence before the PR. Only after the provider reports the PR merged may `ai-close-work-item` verify archive ownership, merged Head SHA, synchronized base, clean worktrees, and remote branch absence.

## Stop conditions
Stop at any failed gate, unresolved Unknown, scope mismatch, incompatible parallel boundary, or missing human decision. Do not guess that a green step means closure. Do not delete a Work Item checkout after a remote failure. If a candidate omits or overlaps the closed serialized-projection inventory, reject it fail-closed and keep the affected Work Items separate.

## Next steps
1. Interpret the state with [Decision States](../concepts/decision-states.md).
2. Read [Cockpit Status](../reference/how-to-read-cockpit-status.md).
3. For a failed stage, use [Recovery](recovery.md).
