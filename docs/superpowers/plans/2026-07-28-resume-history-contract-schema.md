---
author: Ray
title: "Resume History Contract Schema Corrective"
description: Close the writer-reader schema mismatch in governed Work Item resume.
keywords:
  - ai-cockpit
  - work-item
  - resume
  - contract
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# Resume History Contract Schema Corrective

## Problem

`make ai-resume-work-item` atomically generated a valid, source-bound
`resumeHistory` transition for the paused performance Work Item. The immediately
following canonical Contract check rejected that same field as unknown because
`ai_check_work_item.ALLOWED_FIELDS` did not include the writer-owned field.

This is `RFE-ISSUE-129`. Deleting the generated lineage or rewriting the
immutable Start Receipt would bypass the intended control and is forbidden.

## Correction

1. Add a red-first regression proving `resumeHistory` is currently rejected.
2. Add only `resumeHistory` to the canonical Contract allowlist.
3. Preserve the existing negative assertion for unrelated unknown fields.
4. Run the full resumeHistory semantic/ancestry/digest/predecessor/manifest
   regression matrix unchanged.
5. Complete full quality, archive sequence 622, aggregate PR validation, hosted
   CI, merge, closure, and branch cleanup.
6. Return to the paused performance branch, update predecessor closure to this
   corrective, and prove its generated lineage passes Contract and Preflight.

## Non-goals

This Work Item does not change lineage semantics, the resume writer, the
performance implementation, release metadata, candidate identity, or public
release state.
