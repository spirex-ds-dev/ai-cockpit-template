---
author: Ray
title: "Archive Summary Evidence Path Rewrite"
description: Prevent archived Summary evidence from retaining stale active Work Item paths.
---

# Archive Summary Evidence Path Rewrite
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Problem

WI-10 completed `ai-finish`, but the committed aggregate PR gate rejected three
`acceptanceEvidence` entries because they still pointed to the active Summary
after that file had moved to archive. The archive transaction already owns the
complete active-to-archive identity map, but applies it only to selected Summary
fields. A field-specific list can repeat this omission whenever the Summary
schema gains another evidence structure.

## Boundaries

- Do not edit an immutable archive bundle in place.
- Do not weaken missing-evidence validation in `check-ai-pr`.
- Replace only exact repository-relative artifact paths.
- Keep verification commands, execution Contract/Summary paths, and captured
  output immutable as execution provenance.
- Deliver this correction as an independent Work Item and PR before resuming
  WI-10.

## Implementation

1. Add a red archive regression reproducing lifecycle `acceptanceEvidence`
   pointing to the active Summary.
2. Apply one recursive exact-path migration to mutable Summary evidence before
   Summary hashing and Archive Manifest generation.
3. Exclude immutable verification provenance fields from migration.
4. Verify representative nested evidence, genuinely missing evidence, and
   archive rollback behavior.
5. Record the user instruction and this implementation in the bidirectional
   traceability manifest.

Independent review added three required corrections before finish:

- replace the initial protected-key denylist with structural path/evidence
  conventions and preserve the complete verification subtree;
- exercise the generated archive pair through aggregate PR bundle validation;
- restore the exact pre-transaction generated Status bytes when a late archive
  failure occurs.

## Acceptance

- Archived lifecycle acceptance evidence resolves to the archived Summary.
- Nested evidence uses the same migration mechanism.
- Immutable command and execution provenance retains the original active path.
- Ordinary prose and future verification provenance fields remain unchanged.
- A genuinely absent evidence path is still rejected.
- A late failure restores the original generated Status bytes.
- Focused archive and aggregate PR tests, full quality, `ai-finish`, aggregate
  PR validation, Hosted CI, merge, `ai-close-work-item`, and branch cleanup pass.

## Recovery

If any archive transaction step fails, restore the exact active files,
traceability manifest, archive index, and generated status through the existing
transaction rollback. Do not repair the resulting archive JSON manually.
