---
author: Ray
title: "Final Japanese Capability Reassessment Plan"
description: Exact-source final Japanese release-gate reassessment after every capability and process corrective has closed.
---

# Final Japanese Capability Reassessment Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Objective

Complete WI-16 with a fresh assessment on the synchronized post-corrective
`main`, without reusing a corrective Work Item as final-assessment evidence.
The result must remain bounded to repository-governance Japanese handling and
must not claim general provider/model fluency or native-human translation
quality.

## Instruction → plan → implementation → acceptance

| Instruction | Plan | Implementation evidence | Acceptance evidence |
| --- | --- | --- | --- |
| Japanese capability is mandatory before release. | Run the complete matrix as an exact-source release gate. | `scripts/ai_japanese_capability.py`; canonical JSON/Markdown | focused Japanese suites; committed-Head `make check-japanese-capability` |
| Every discovered problem must be corrected before continuing. | Treat every non-zero blocker as a separate corrective Work Item and stop this reassessment. | `blockingFindings`; comprehensive plan | zero-blocker assertion or named corrective queue |
| Do not reuse stale or corrective evidence as the final assessment. | Change the canonical report identity to this final reassessment and regenerate from current bytes. | report `workItemId` and `workItemRole` | identity and drift regressions |
| Preserve the bounded claim. | Keep general fluency and translation quality as explicit limitations. | JSON/Markdown limitations | non-claim regression |
| Use bidirectional traceability for every Work Item. | Add PLAN-DIRECTIVE-039 and map Contract, report, tests, Summary, and lifecycle evidence. | traceability manifest; comprehensive plan | traceability and Summary gates |
| Complete the full lifecycle. | Finish, archive, PR, Hosted CI, merge, closure, branch deletion, and synchronized main before documentation alignment. | Contract/Summary/Manifest and PR | aggregate PR, Hosted checks, `ai-close-work-item` |

## Tasks

1. Complete the high-risk Contract, Preflight, plan registration, and
   `before_edit` checkpoint.
2. Write red-first tests requiring
   `workItemId=japanese-final-reassessment-20260729`,
   `workItemRole=final_reassessment`, and final-assessment Markdown wording.
3. Update only the assessment identity/wording, regenerate both reports, and
   verify the 12-case, 45-file matrix remains deterministic and zero-blocker.
4. Run Japanese input-trust, corpus, CLI/Status/PR/lifecycle, documentation,
   source-binding, report-drift, and exact-source checks. If any blocker exists,
   record it and create a separate corrective before resuming.
5. Complete reverse traceability, Summary acceptance evidence, independent
   review, fast/full quality, and `ai-finish`.
6. Commit the immutable archive, run the aggregate PR check, push one PR, wait
   for exact-Head Hosted checks, merge, and run `ai-close-work-item`.
7. Start documentation alignment only from the newly synchronized `main`.

## Completion boundary

This Work Item proves the final bounded Japanese assessment lifecycle only.
Documentation alignment, deprecated-assets cleanup, release publication, and
plan cleanup remain later independent Work Items.
