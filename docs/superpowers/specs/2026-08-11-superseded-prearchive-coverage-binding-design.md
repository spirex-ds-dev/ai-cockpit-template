---
author: Ray
title: "Superseded Pre-Archive Coverage Binding Design"
description: Preserve historical red Outcomes while binding current archive-candidate coverage.
status: historical
authority: implementation_record
---

# Superseded Pre-Archive Coverage Binding Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Problem

Real archive mutation requires a current changed-critical-coverage report and
an equal `preArchiveCandidateCoverage` binding in the active Outcome. Historical
blocked Outcomes created before that binding existed cannot satisfy the rule.
Adding the field changes the Outcome digest and invalidates the exact successor
receipt that authorizes supersession.

## Decision

Keep current candidate coverage mandatory and persist it in the immutable
archive manifest. Extract a canonical lifecycle-truth predicate that validates
the blocked Outcome and exact `transition=superseded` receipt independently of
Summary issue classification.

`load_pre_archive_candidate_coverage` retains its existing exact-binding path.
When the Outcome binding is absent, and only then, it may return the current
coverage binding if the canonical superseded predicate succeeds. An existing
but unequal binding remains an error. Missing or stale reports remain errors.

## Safety boundary

- The historical Outcome and receipt bytes are never rewritten.
- The current report still binds Contract base, candidate Head, candidate tree,
  and candidate diff.
- The archive manifest still records the current report digest and binding.
- Missing, malformed, quarantined, mismatched, or non-blocked successor evidence
  cannot authorize the exception.
- Normal completed Work Items continue through the existing exact Outcome
  binding path.

## Verification

Use red-first unit tests for the absent historical binding, mismatched existing
binding, invalid receipt, and normal exact-binding cases. Run the combined
archive and lifecycle suites, strict quality, hosted checks, and finally the
real historical predecessor archive/closure path.
