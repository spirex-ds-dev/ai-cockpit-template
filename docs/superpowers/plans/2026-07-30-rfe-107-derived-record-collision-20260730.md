---
author: Ray
title: "RFE-107 Derived Archive-Record Collision Prevention"
description: "Prevent delayed archived Work Items from colliding with newer archive sequences or traceability identifiers during recovery."
---

# RFE-107: Derived archive-record collision prevention

## Purpose

Prevent a delayed or parallel Work Item from silently reusing an archive
sequence or instruction-traceability identifier that was allocated on a newer
base. This corrective Work Item was discovered while attempting to revalidate
RFE-104 after RFE-106 merged.

## Constraints

- Preserve RFE-104 and RFE-106 archived evidence; do not rewrite history to
  resolve a rebase conflict.
- Fail before archive or PR acceptance when derived identifiers are stale or
  duplicated.
- Require an explicit, evidence-bound successor/recovery path for any
  redelivery.

## Implementation and verification

1. Add deterministic stale-base/archive-sequence detection before archive
   mutation, with an actionable recovery result.
2. Reject duplicate traceability IDs independently from missing-path errors.
3. Reject trailing whitespace in every active artifact before archive mutation,
   because ignored active files are invisible to ordinary Git diff checks.
4. Add regression coverage for stale allocation, duplicate IDs, valid
   recovery lineage, and archive whitespace preflight.
5. Update the remediation traceability and run the complete governance and
   quality gates.
6. Report while active, then archive, PR, hosted CI, merge, closure, and
   branch cleanup. Only then begin a clean successor delivery for RFE-104.
