---
author: Codex
title: "Calibration Profiles Implementation Plan"
description: "Executable plan for WI-05 proportional calibration controls and transition evidence."
---

# Calibration Profiles Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

**Goal:** Make Lite, Standard, and Strict calibration requirements explicit,
cumulative, reviewable, and safe to transition without forcing ordinary adopters
through release-grade controls.

**Architecture:** One versioned policy owns profile order and control membership.
One validator resolves required/deferred controls, validates persisted selection
evidence, and evaluates upgrades or bounded downgrade exceptions. Existing Project
Profile and calibration proposal code consume that authority; they do not create a
second classifier or replace the durable calibration session.

## Task 1: Specify the policy and validator

1. Add failing tests for the exact Lite controls, cumulative Standard/Strict
   controls, Strict-only exclusions, malformed policy, and unknown level.
2. Add the versioned profile policy and implement strict loading plus deterministic
   required/deferred resolution.
3. Add failing schema tests for human selector, timestamp, reasons, and exact
   required/deferred evidence, then implement validation.

## Task 2: Enforce transition evidence

1. Add failing tests for Lite→Standard, Standard→Strict, skipped upward escalation,
   unrecorded downgrade, incomplete downgrade, and closed-control mismatch.
2. Implement monotonic upgrade and downgrade-exception validation with original/new
   levels, reason, closed controls, risk acceptor, and effective scope.
3. Keep transition decisions local and deterministic; do not infer external identity.

## Task 3: Integrate Project Profile and calibration proposals

1. Add red regressions proving legacy Project Profiles remain readable and malformed
   declared calibration profiles fail closed.
2. Integrate optional validation into the existing Project Profile owner.
3. Render a review-required Lite calibrationProfile in generated proposals and add
   a valid selected profile to the template repository profile.

## Task 4: Preserve adopter parity

1. Expose a narrow Make validation entrypoint backed by the same validator.
2. Register the validator in the installer catalog and verify the governed policy is
   copied with the existing `.ai` tree.
3. Add installation/adoption regression coverage without changing WI08 wizard UX.

## Task 5: Document and finish

1. Document levels, evidence fields, transition rules, recovery, limitations, and
   non-claims in English, Japanese, and Simplified Chinese.
2. Run focused tests after each behavior group, then the Contract-selected Standard
   checks and required finish gates.
3. Complete Summary evidence, archive, commit, push, PR, Hosted verification, merge,
   lifecycle closure, and branch cleanup before starting WI04.
