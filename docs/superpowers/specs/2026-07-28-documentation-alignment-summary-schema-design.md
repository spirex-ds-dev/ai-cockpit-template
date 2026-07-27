---
author: Codex
title: "Documentation Alignment Summary Schema Design"
description: "Design for source-bound Work Item documentation alignment evidence."
keywords:
  - ai-cockpit
  - documentation-alignment
  - summary
  - traceability
---

# Documentation Alignment Summary Schema Design

## Problem

The remediation plan requires every Work Item to confirm documentation
alignment before closure, but the canonical Summary validator previously
rejected `documentationAlignment` as unknown. Prose in unrelated Summary fields
could describe the review but could not prove that every required domain was
checked or that named files were not omitted.

## Decision

Every current Contract v2 Summary carries `documentationAlignment` schema
version 1. Its root status must be `aligned` before Finish and its `checkedAt`
must be an offset-aware ISO-8601 timestamp. It contains exactly one check for
each area:

1. `plan`
2. `contractSummaryEvidence`
3. `documentationCommandsCapability`
4. `multilingualSemantics`
5. `limitationsUnknownsHistory`

An area is either `aligned` with at least one repository evidence path, or
`not_applicable` with an empty evidence list and a concrete reason. Missing,
duplicate, unknown, `not_checked`, or `misaligned` areas fail closed.

## Evidence binding

Evidence must be a normalized repository-relative path, must exist, and must
also appear in `changedFiles` or `sourcesUsed`. URLs, absolute or home-relative
paths, backslashes, parent traversal, missing files, and undeclared paths are
rejected.

The validator also walks `changedFiles` in the reverse direction. Changed
Markdown, README, Makefile, `.mk`, and `templates/make/` surfaces—excluding the
generated Cockpit status and Work Item records—must appear in alignment
evidence. This turns a user-named documentation or command file omission into a
deterministic gate failure.

## Generation and compatibility

`ai-start`, installer adoption, installer upgrade, and the checked Summary
example use one canonical `not_checked` skeleton from
`scripts/ai_check_summary.py`. The skeleton is intentionally not finish-ready.
After an installer has assembled its final adoption or upgrade `changedFiles`,
its bounded finalization step deterministically replaces that skeleton with an
aligned record covering the generated Contract, every written documentation or
command surface, multilingual files when present, and retained boundaries.
This lets the one-step adopter journey reach Finish without a human-authored
schema bypass.

Archived Summaries created before this field remain immutable. Validation in
explicit legacy-archive mode accepts an absent field; a current v2 Summary does
not. A historical archive that already contains the field is still validated
when read.

For the Work Item currently being archived, the archive transaction rewrites
exact active Contract/Summary artifact references inside
`documentationAlignment` to their durable archive paths. It does not rewrite
`verification.command`, `executionContractPath`, or other execution-time
evidence: those fields describe where and how the check actually ran, while
documentation alignment must remain a resolvable current evidence map.

## Boundaries

Documentation alignment is not test execution, hosted evidence, identity,
branch protection, release authorization, or capability implementation. It
maps repository evidence and exposes drift; existing evidence-producing tools
and the Capability Truth Matrix remain authoritative for their domains.
