---
author: Ray
title: "RFE-104 Independent Pre-Archive Outcome Gate"
description: "Independently deliver active-state, localized Task Outcome reporting before explicit archive after the combined RFE-101/RFE-102 draft and RFE-103 dependency exposed lifecycle defects."
---

# RFE-104: independent pre-archive Outcome gate

## Problem

Current `main` automatically archives a Work Item in `ai-finish`. That prevents
the required direct conversation report while the Work Item remains active.
The earlier implementation was technically verified but placed with a second
Work Item in draft PR #462, so it cannot be merged. RFE-103 then demonstrated
the dependency: without this behavior on `main`, its Outcome was archived
before it could be directly reported.

## Plan

1. Make ordinary `ai-finish` preserve a validated active Outcome by default.
2. Render a safe-to-relay English, Chinese, or Japanese report boundary from
   evidence-bound Outcome facts; keep archive an explicit command.
3. Prove active preservation, explicit archive, report ordering, localization,
   adopter flow, and complete governed lifecycle with executable regressions.
4. Regenerate traceability and source-bound Capability Truth/Japanese evidence.
5. Deliver through this branch alone: direct active Outcome report, archive,
   PR, hosted CI, merge, closure receipt, and cleanup.

## Non-goals

- Output alone does not prove that an agent actually relayed it to a human.
- No arbitrary evidence prose is machine-translated.
- No immutable prior archive or draft PR #462 evidence is rewritten.
