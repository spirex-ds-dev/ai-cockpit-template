---
author: Ray
title: "WI-10 Platform Table and Calibration Checklist Corrective Plan"
description: Repair broken multilingual platform tables and deliver the omitted complete calibration checklist with fail-closed checks.
keywords:
  - installation
  - calibration
  - multilingual
  - markdown
  - traceability
---

# WI-10 Platform Table and Calibration Checklist Corrective Plan

## Objective

Close `WI-10-ISSUE-015` and `WI-10-ISSUE-016` before any later process,
release, or cleanup Work Item. This correction is complete only after its
dedicated PR is merged, the Work Item is closed, and both branches are cleaned.

## Bidirectional traceability

| Instruction | Plan | Implementation | Acceptance |
|---|---|---|---|
| Repair rows 5–7 in every language | Make each platform table one uninterrupted Markdown block | Nine files under `docs/getting-started/examples/` for iOS, Android, and Java | Structural checker rejects comments, blanks, missing rows, and misplaced markers |
| Provide the missing calibration checklist | Add a distinct ten-item completion checklist, not another explanation | `installation.md`, `installation.zh-CN.md`, `installation.ja.md` | Each item records state, evidence, answer, Candidate change, Owner/Reviewer, and PASS/STOP |
| Prevent another partial delivery | Compare stable structures across all three languages and all three platforms | `scripts/check_docs_metadata.py` | Mutation tests in `tests/test_docs_metadata.py` fail before and pass after implementation |
| Preserve novice usability and safety | Keep prompt-first instructions and fail closed on unknown evidence | All twelve named documentation files | Review confirms no invented command, evidence, capability, or automatic activation |
| Avoid version drift and invalid records | Select the highest verifiable stable release, report and stop on newer invalid evidence before any older fallback, and persist answers through the Calibration Session | Three installation guides and metadata checker | Mutations reject moving-main digest authority, hardcoded versions, missing `yes_no` mapping, and missing bounded activation |
| Preserve useful multilingual examples | Keep the Japanese seven-stage filled examples and add semantically aligned English and Chinese examples | All nine platform documents | Checker rejects missing, interrupted, malformed, or structurally incomplete filled examples |
| Expose current runtime limits | State that unknown is not machine-blocking, confirmations are not Candidate-digest-bound, the Session stores only its schema-supported answer lifecycle, and Active replacement plus Session save are not one transaction; require manual STOP pending `RFE-ISSUE-151` | Three installation guides, Summary, and comprehensive plan | Runtime, persistence, and atomicity boundary mutations fail closed and release remains blocked on the later corrective |
| Keep the novice path executable | Distinguish archive verification from installer input, use the explicit `Makefile.ai` entrypoint when Make integration is off, expose exact answer type/value, externalize actor identity, route non-adoption modes, and close CI gaps | Three installation guides and all nine filled examples | Stable boundary mutations and focused metadata tests reject every reopened path |
| Preserve lifecycle evidence | Update traceability, Summary, archive, PR, Hosted CI, merge, and closure records | Governance artifacts declared by the Contract | `ai-finish`, aggregate PR check, Hosted CI, merge, `ai-close-work-item`, and branch cleanup pass |

Every implementation file above must map back to a user instruction and an
acceptance check. A named file with no content change requires an explicit
reason in the Summary; silent omission is not allowed.

## Test-first implementation order

1. Add failing mutations for an HTML comment and blank line inside a seven-row
   platform table, plus marker placement and row-count failures.
2. Add failing checks for absent checklist, missing row, missing required field,
   and cross-language stage-order drift.
3. Move the Stage 5 marker outside all nine tables and preserve exactly seven
   consecutive rows.
4. Add aligned, independently fillable ten-stage calibration checklists to all
   three installation guides.
5. Make release discovery dynamic (highest stable release with a complete,
   mutually consistent evidence chain), stop before any older fallback, and
   route checklist answers and bounded activation through the persisted
   Calibration Session while exposing the current runtime limitation.
6. Add aligned seven-stage filled examples to every platform/language document
   and require concrete evidence-table output at Stage 7.
7. Run focused tests and documentation checks, then inspect all twelve named
   documents against the instruction-to-acceptance matrix.
8. Complete full quality, archive, PR, Hosted CI, merge, closure, and branch
   cleanup before starting `RFE-ISSUE-147`.

## Stop conditions

Stop rather than guess if a requested platform fact lacks repository evidence,
if a translation would change a safety boundary, or if the governed checks
require a new human authority decision. A normal red-first failure or an
implementation defect is not a human-decision stop.
