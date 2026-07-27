---
author: Ray
title: "Documentation Alignment Hosted Recovery"
description: Governed recovery plan for hosted documentation-alignment CI failures.
keywords:
  - ai-cockpit
  - work-item
  - ci
  - documentation
---

# Documentation Alignment Hosted Recovery

## Purpose

Recover `documentation-alignment-summary-schema-20260728` without rewriting its
archived evidence. PR #415 passed full local quality twice, but hosted run
`30302291885` failed twice at `project-test` on the same source commit. The
quality wrapper retained the detailed output only in a runner-local gate log,
so the Actions record showed the failing gate and duration but not the exact
pytest or coverage failure.

## Governed recovery

This replacement Work Item is an adjacent recovery pair:

- predecessor: archive sequence 620, closed PR #415, never amended;
- recovery: archive sequence 621, human-authorized and source-linked to the
  predecessor;
- replacement delivery: one new PR containing both the predecessor bundle and
  recovery bundle, accepted only by the repository's recovery-pair validation.

The recovery does not lower the coverage floor, exclude production files,
reopen PR #415, perform general performance optimization, or prepare a release.

## Implementation and acceptance

1. Reproduce the predecessor payload in a clean Linux Python 3.12 checkout and
   retain the complete result.
2. Add a red-first workflow regression proving a failed quality gate publishes
   its detailed log before runner teardown.
3. Print every non-passing gate log from `target/quality/logs`; if the wrapper
   exits before a gate writes timing evidence, print the wrapper log instead.
4. Add behavior-focused tests for empty, fallback, multilingual, nested, and
   scalar documentation-alignment paths so coverage has a stable margin without
   weakening policy.
5. Re-run focused tests, full local quality, archive/PR validation, and every
   hosted required Job.
6. Merge, run `ai-close-work-item`, delete local and remote recovery branches,
   synchronize `main`, then remove the superseded predecessor branch.

## Traceability

The Contract owns every modified path. The Summary must map each instruction to
implementation and acceptance evidence, record PR #415 and both failed attempts,
and preserve limitations and unresolved performance work. The comprehensive
remediation plan and traceability manifest must point to the final archive path
after Finish.

## Process issue

`RFE-ISSUE-126`: the hosted quality wrapper emitted only heartbeat and timing
metadata while the detailed failed Gate output remained in an ephemeral file.
The corrective is durable workflow behavior plus a static regression, not a
one-off rerun or manual log copy.

`RFE-ISSUE-127`: a documentation-alignment unit test used the predecessor's
active Contract as an undeclared filesystem fixture. Full quality passed before
Finish because the active file existed, but the same test necessarily failed in
the post-archive clean checkout used by hosted CI. The recovery binds the fixture
to the immutable archived Contract and requires post-archive clean-checkout
verification, closing the lifecycle gap instead of treating it as runner
variance or adding retries.

`RFE-ISSUE-128`: the first recovery draft misstated the predecessor archive
sequence. The immutable Summary, Manifest, and index agree on sequence 620, so
only the active recovery records were corrected to request sequence 621.
