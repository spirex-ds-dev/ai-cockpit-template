---
author: Ray
title: "Post-Correction Final Japanese Capability Reassessment Plan"
description: Fresh exact-source Japanese release-gate reassessment after the pre-release documentation-truth corrective.
---

# Post-Correction Final Japanese Capability Reassessment Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Objective and boundary

Produce the release-required `final_reassessment` from corrected `main`
without reusing the historical final assessment or the later
`corrective_validation` report. The result covers bounded repository-governance
Japanese handling. It does not prove general provider/model fluency,
native-human translation quality, enterprise compliance, or release
publication.

Any non-zero `blockingFindings` result stops this Work Item and creates a
separate corrective lifecycle. Documentation alignment remains paused until
this Work Item completes PR, Hosted CI, merge, `ai-close-work-item`, branch
cleanup, worktree cleanup, and synchronized `main`.

## Instruction → plan → implementation → acceptance

| Instruction | Plan | Implementation evidence | Acceptance evidence |
| --- | --- | --- | --- |
| Japanese capability is mandatory before release. | Regenerate the complete 12-domain matrix from corrected source and require `final_reassessment`. | `scripts/ai_japanese_capability.py`; canonical JSON/Markdown | identity tests; `--require-final-reassessment`; zero blockers |
| Most adopter engineers use Japanese. | Require direct executable Japanese input, CLI, Status, PR, lifecycle, and documentation evidence. | Japanese corpus and 57-file evidence inventory | Japanese capability, input-trust, adopter-lifecycle, and documentation suites |
| The documentation correction invalidated the earlier final result. | Use a new Work Item ID and directly bind corrected README, Trust Layer, release, architecture, and Capability Truth bytes. | `evidenceSource.files` and aggregate digest | inventory, byte-drift, source-mismatch, and unrelated-drift regressions |
| Every discovered problem must be corrected before continuing. | Treat each blocker as a separate corrective Work Item; do not repair it inside the assessment. | `blockingFindings` and Contract out-of-scope boundary | machine-proved empty blocker list or named corrective queue |
| Prevent instruction omissions. | Add PLAN-DIRECTIVE-044 and map user request, plan, Contract, implementation, tests, Summary, and acceptance in both directions. | traceability manifest and comprehensive plan | traceability, scope, Summary, and documentation-alignment gates |
| Complete every Work Item lifecycle. | Finish/archive, push, PR, exact-Head Hosted checks, merge, close, delete branches, remove worktree, and synchronize main before resuming alignment. | archive pair/manifest and PR | aggregate PR check, Hosted conclusions, merge record, closure output, branch absence |

## Execution tasks

1. Start from exact corrected `origin/main` and establish a clean baseline.
2. Complete the high-risk Contract, Preflight, and `before_edit` checkpoint.
3. Add red-first tests for the new Work Item identity and final role.
4. Change only the report identity, regenerate both reports, and inspect the
   complete matrix and blocker list.
5. Run focused Japanese, corpus, lifecycle, source-binding, drift,
   documentation, and release-role checks.
6. Complete Summary evidence, reverse traceability, documentation alignment,
   independent review, full quality, and `ai-finish`.
7. Commit the archive bundle, run aggregate PR verification, push one branch,
   open one PR, require exact-Head Hosted success, merge without provider branch
   deletion, and run lifecycle closure.
8. Resume documentation alignment only from the synchronized base worktree.

## Issues recorded during execution

- `JA-FINAL-ISSUE-001` (local command construction, resolved): the first
  worktree command used zsh's special `path` variable, which temporarily
  replaced `PATH` and stopped before the first Git operation. No branch,
  directory, or repository file was changed. The retry used
  `worktree_dir`/`branch_name`, created the expected worktree, and verified the
  exact base.
- `JA-DOC-FACT-002` (Japanese documentation truth, release blocking): the
  five-strategy review found that the Japanese installation guide says the
  calibration Session stores only answer and execution-state information.
  `scripts/ai_calibrate.py record-evidence` also persists structured
  `checklistEvidence`, including rationale, Candidate changes, Owner, Reviewer,
  PASS/STOP, reasons, and recheck instructions. Accuracy and Clarity reached
  consensus at the same passage. The assessment now records the blocker and
  routes it to
  `japanese-calibration-session-evidence-doc-corrective-20260729`; this final
  reassessment is paused until that corrective fully closes.
- Single-strategy readability and audience suggestions from the same review
  are retained as documentation-alignment input. They are not promoted to
  consensus blockers or silently changed inside this assessment.
- `JA-FINAL-RESUME-001` (resolved): the paused Contract predated the reusable
  Capability Truth dependency gate and did not identify the later
  `JA-DOC-FACT-002` corrective as its predecessor. The resumed Contract now
  binds PR #454 and its archive manifest, owns and regenerates the Capability
  Truth matrix, and records the exact base transition before reassessment.
- `JA-FINAL-FORMAT-001` (resolved): the first resumed `quality-fast` run found
  only Ruff formatting drift in the new fail-closed evaluator test. The test
  was formatted, Capability Truth and the Japanese report were regenerated in
  dependency order, and `quality-fast` then passed.
- `CI-WARN-001` (routed, release blocking): Hosted runs exposed a Node 20
  artifact-action warning, Go setup cache warnings without a root `go.mod`,
  and an unrelated untrusted `aws/tap` warning during Swift setup. These are
  outside this assessment scope and are queued as one independent corrective
  after this lifecycle closes and before documentation alignment resumes.

## Completion boundary

This Work Item is complete only after the repository lifecycle closes and its
work branch is absent locally and remotely. Documentation alignment,
deprecated code/logic/document cleanup, publication, and plan cleanup remain
later independent Work Items.
