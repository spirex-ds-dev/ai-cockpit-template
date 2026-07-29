---
author: Ray
title: "Pre-archive Human Report Design"
description: Decision-first Work Item report before archive, push, or PR.
---

# Pre-archive Human Report Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Decision

Every Work Item reports while it is still active: after local verification and Outcome generation, before archive, push, or provider PR creation. This timing is identical whether a later PR is manually opened or separately permitted automation opens it.

## Report contract

The direct report names the Work Item, delivered local changes, verified local evidence, residual risks, and `Provider PR: not created`. It leads with these facts; Outcome paths are optional audit links. It never claims provider approval, Hosted CI, merge, or cleanup.

## Control point

`ai-finish` completes local validation and leaves the active Contract and Summary in place. It prints the report and a stop state. The executor sends it to the human and waits. Only an explicit post-report confirmation may invoke the archive path; then the usual push → PR → merge → closure lifecycle continues.

## Verification

Integration tests prove the report occurs after a valid Outcome, before archive, and rejects incomplete/provider facts. Archive tests prove the confirmation gate is fail-closed. Repository rules and user documentation make conversation delivery and confirmation an executor obligation because a repository script cannot authenticate or post to external chat.
