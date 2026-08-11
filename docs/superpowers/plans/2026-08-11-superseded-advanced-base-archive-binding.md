---
author: Ray
title: "Superseded Advanced-Base Archive Binding Implementation Plan"
description: TDD plan for exact remote-default-tip archive transaction binding.
status: historical
authority: implementation_record
---

# Superseded Advanced-Base Archive Binding Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

**Goal:** Archive an aged superseded predecessor without rewriting its evidence
or excluding committed Work Item changes.

### Task 1: Candidate lifecycle evidence

- [x] Add a red regression for successor-receipt ownership.
- [x] Bind successor-receipt byte changes into both candidate digests.
- [x] Preserve foreign-path rejection.

### Task 2: Alternate-base trust boundary

- [x] Add a red regression for an exact remote-default-tip transaction base.
- [x] Require report base, candidate Head, and unique remote-default tip equality.
- [x] Reject branch commits, stale tips, and ambiguous remote identity.
- [x] Preserve normal Contract-base behavior.

### Task 3: Verification and delivery

- [ ] Run affected suites, static checks, and full governed verification.
- [ ] Archive, PR, merge, and close the corrective Work Item.
- [ ] Re-run the preserved predecessor archive transaction and close it.
