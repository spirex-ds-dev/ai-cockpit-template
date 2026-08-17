---
author: Codex
title: "Outcome Lifecycle Green Gate Design"
description: "Design for directly visible, green-gated Outcome terminality across Finish, archive, PR, close, and adopter installation."
status: current
authority: implementation_record
lastVerifiedBy: outcome-lifecycle-green-gate-20260817
---

# Outcome Lifecycle Green Gate Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Problem

The repository can persist an Outcome and generate a status projection without making the complete result a reliable, directly visible conversation surface. Downstream lifecycle consumers also validate the shape of an Outcome without uniformly requiring a current, completed, green result. This permits a yellow or stale result to be mistaken for terminal completion.

## Decision

Introduce one project-neutral Outcome gate used by Finish, archive, PR validation, and close. The gate will:

- validate the canonical Outcome JSON and Markdown together;
- require `status=completed` and `humanStatusColor=green` for terminal lifecycle operations;
- bind the result to the current Work Item, Contract digest, Summary digest, verification digest, base commit, and candidate Head;
- fail closed on missing, malformed, stale, cross-task, yellow, or red evidence.

Finish will persist an Outcome before reporting it and will route every terminal path through one direct delivery helper. The helper prints the complete localized Outcome and human-benefit report to stdout, including the canonical traffic-light marker. Failure paths retain their non-zero exit code and print the blocked Outcome directly, so a tool artifact or folded log is never the only human-visible result.

## Rules propagation

The current repository rules and the distributed adopter rules will state that a discovered issue is repaired in the current Work Item first. A successor Work Item is justified only when the scope, authority, or base is genuinely different. Neither archive nor closure may proceed unless the current Outcome has passed the green gate and has been directly delivered to the human.

## Verification

Tests will cover the shared gate, Finish subprocess stdout and exit status, and archive/PR/close rejection of non-green or stale Outcomes. Existing historical archive evidence remains immutable; new evidence is generated only by the current lifecycle transaction.
