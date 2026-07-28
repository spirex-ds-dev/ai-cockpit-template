---
author: Ray
title: "Preflight Planned Scenario Transition Design"
description: Fail-closed design for implementation-ready scenario plans and atomic ai-start failure.
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# Preflight Planned Scenario Transition Design

## Problem

The enforced Preflight currently treats every required `unverified` scenario as incomplete
implementation evidence. That creates a dead end for medium- and high-risk code Work Items:
the scenario can only be verified after implementation, but implementation cannot start until
the scenario is verified. Matching Human Decision Evidence changes the state to
`human_decision_recorded`, which remains blocked by design and must not become a general bypass.

The same reproduction exposed a second lifecycle defect. When `ai-start` attempts to refresh a
stale no-active status and consistency still fails, the command leaves the tracked status file
rewritten even though no Work Item was created.

## Decision

Preflight will distinguish implementation planning from completion evidence.

A required `unverified` Contract scenario is implementation-ready only when it declares:

- a non-empty `scenario`;
- `required: true`;
- `status: unverified`;
- a non-empty `expected`;
- a non-empty `verificationPlan`.

When every required scenario is either `verified`, justified `not_applicable`, or an explicit
planned-verification entry, the Preflight Scenario Coverage signal is `Ready`. Its evidence text
must say that scenarios are planned, not verified.

This transition does not affect completion. The Summary Scenario Coverage Guard continues to
reject every required `unverified` scenario unless the existing explicit residual-risk path
applies. Human Decision Evidence remains hash-bound and does not override missing intent,
unknowns, scope, sources, acceptance, verification, capability, or execution decisions.

## Atomic Start

`refresh_stale_no_active_status` snapshots the existing status bytes before regeneration. If
regeneration does not produce a consistent state, it restores the exact prior bytes (or removes
the newly created file when none existed). A rejected start therefore leaves no tracked status
change and creates no Contract, Summary, receipt, or Decision Evidence.

## Alternatives Rejected

1. Treat `human_decision_recorded` as ready: rejected because approval would bypass incomplete
   evidence.
2. Mark future scenarios verified before implementation: rejected because it would misstate
   repository truth.
3. Make scenarios optional until finish: rejected because mutating requiredness hides the risk
   instead of governing it.

## Verification

- Preflight derives ready for explicit planned verification.
- Missing `expected` or `verificationPlan` remains blocked.
- Conservative and Decision Evidence regressions remain blocked.
- Summary Scenario Coverage still rejects required unverified evidence.
- Failed no-active refresh restores status byte-for-byte.
- Runtime documentation and canonical glossary define the boundary consistently.

