---
author: Ray
title: "How to Read Cockpit Status"
description: Reviewer-facing guide to interpreting AI Cockpit current_status.md during V2.5/V2.6 stabilization.
keywords:
  - ai-cockpit
  - cockpit-status
  - reviewer-guide
  - release-hardening
  - v2.5
---

# How to Read Cockpit Status

This page explains how to read the generated Cockpit Status during V2.5/V2.6 stabilization and release hardening.
It is written for reviewers, maintainers, and approvers who want the shortest path from status to decision.
If you are about to start implementation, read the latest Preflight Review first. Cockpit Status is for reviewer visibility; it does not replace the pre-implementation pause.

## Validated Japanese View

The committed `.ai/cockpit/current_status.md` remains the canonical generated Status artifact. A reviewer can create and validate an on-demand Japanese projection without adding a second lifecycle artifact:

```sh
make generate-cockpit-status-ja CONTRACT=<contract.json> SUMMARY=<summary.json>
make check-ai-status-ja CONTRACT=<contract.json> SUMMARY=<summary.json>
```

The generated view is `target/ai_cockpit_status.ja.md`. Both views come from the same governance model and canonical rendering. The Japanese projection localizes presentation chrome such as headings, conclusions, and action labels; it does not independently derive or translate paths, commands, identifiers, statuses, counts, or arbitrary evidence values. Backtick-delimited values remain byte-identical and ordered. Do not edit either generated view by hand: the paired check rejects stale or changed Japanese output.

This derived view proves bounded repository-output parity. It does not prove general Japanese fluency, translate adopter evidence, or authorize commit, merge, release, or external operations.

## Read Order

Start with these fields in order:

1. `Preflight Review` if present in the active Work Item workflow
2. `Key Conclusion` (Color, Conclusion, Evidence Basis, and Next Action)
3. `Recommendation`
4. `Decision Drivers`
5. `Governance Signals`
6. `Evidence`
7. `Scenario Coverage` if present in the signals list

`Preflight Review` derives implementation readiness from Contract evidence. This
repository enforces it before coding starts: `needs_human_confirmation` and
`not_ready` block implementation. An adopter may choose the explicit advisory
compatibility profile, but that is not this repository's default.

`Recommendation` gives the decision state. `Decision Drivers` explains why that state was chosen.
`Governance Signals` show the compressed judgment, and `Evidence` points back to the repository truth.

## Key Conclusion and Color Semantics

`Key Conclusion` is a deterministic summary of the canonical recommendation. The
colors are semantic review signals, not scores, confidence levels, quality ratings,
or claims that the agent performed well:

| Color | Meaning | Required next action |
| --- | --- | --- |
| `Green` | Evidence is sufficient for human review. | Review evidence and make the human commit or merge decision. |
| `Yellow` | Review may continue only with recorded residual risks understood. | Read Residual Risk and Decision Drivers before deciding. |
| `Red` | Evidence is incomplete/ambiguous or a hard blocker exists. | Investigate or stop until the blocker is resolved. |

`Evidence Basis` names the generated sections derived from Contract, Summary, and
verification evidence. It is a drill-down pointer, not a second source of truth.
`Next Action` is procedural guidance and does not authorize a merge, release, or
external operation.

## Active Task Outcome

Every active Status includes a `Task Outcome` projection. It is a separate
lifecycle signal from `Key Conclusion`: use it to determine whether `ai-finish`
has emitted an Outcome for the current Work Item.

The two signals deliberately answer different questions and can have different
colors while Finish is stabilizing evidence. `Signal Domain: governance_review`
answers whether the Contract/Summary evidence is ready for review;
`Signal Domain: work_item_lifecycle` answers whether Finish emitted an Outcome.
Read each color only within its declared domain; neither overrides the other.

| Presence / traffic light | Meaning | Recovery boundary |
| --- | --- | --- |
| `absent` / `yellow` | Finish has not yet persisted an Outcome. This is normal while implementation or verification is in progress. | Continue the declared verification or run `make ai-finish`; do not treat the Work Item as archive-ready. |
| `present` / `red` | A bound blocked or failed Outcome records its failed gate and recovery condition. | Complete the stated recovery and rerun the failed gate. A red Outcome never authorizes archive, merge, or release. |
| `present` / `green` | A bound completed Outcome was produced for this exact Work Item. | Continue the canonical review and archive lifecycle; green is not merge or release authorization. |

The projection is generated from the active Contract, Summary, and the
same-task Outcome JSON/Markdown evidence. A malformed, stale, cross-task, or
Summary-contradictory Outcome causes status generation/checking to fail closed;
never repair `current_status.md` by hand or copy another Work Item's Outcome.
If a later Finish gate blocks after an earlier green projection, Finish regenerates
the Status from the blocked Outcome before returning. If that refresh cannot be
validated, it removes the stale generated Status rather than leaving a false green
signal; read the task-bound blocked Outcome and repair the reported gate.

## What the Preflight Review Means

| Status | Meaning |
| --- | --- |
| `ready` | The Contract evidence is sufficient to begin implementation without a human clarification pause. |
| `needs_human_confirmation` | The Contract evidence is usable, but the reviewer should clarify the missing or weak signals before coding continues. |
| `not_ready` | The Contract evidence does not yet support implementation, so the pause should continue until the gap is resolved. |

The review is an advisory view, not an AI confidence statement. It is derived from existing Contract evidence such as `intent`, `unknowns`, `sources`, `acceptance`, `scope`, `outOfScope`, `riskAssessment`, `scenarioCoverage`, and `verification`.

### Explicit blockers

The report is `not_ready` immediately when `notCodable` is `true`; when `executionDecision.status` is `block`, `defer`, or `needs_human_decision`; or when a declared `agentCapability` cannot implement, cannot verify, or needs a human decision. For example, `{"notCodable": true}` is not a request for more confidence: implementation must pause until the Contract changes.

## No Active Work Item

`no_active_work_item` means no Contract/Summary pair is active. It does **not** mean the worktree is unchanged. The generated marker intentionally omits transient paths and records zero changes. `check-ai-status-consistency` separately accepts the brief archive-before-first-commit transition only when a current valid manifest binds the archive pair and its archived Summary `changedFiles` owns every live path. Any omitted or unrelated path fails with guidance to restore it or create/resume a Work Item; `repair-ai-status` cannot create ownership. Use `make check-ai-diff-ownership` for a local ownership preview and `make check-ai-pr AI_BASE_COMMIT=<merge-base>` for final PR audit. In PR mode the audit resolves overlapping archive claims deterministically, with the latest matching archive pair winning.

## What the Recommendation Means

| Recommendation | Meaning |
| --- | --- |
| `ready_for_review` | The work is complete, evidence is present, and review can focus on correctness. |
| `ready_with_risks` | The work is ready, but a reviewer should confirm the stated residual risks. |
| `needs_investigation` | The status is incomplete or ambiguous, so a human should resolve the open questions first. |
| `blocked` | A hard blocker exists and review should stop until it is resolved. |

## What to Check Next

- If `Recommendation` is `ready_for_review`, scan `Decision Drivers` for any remaining caveats and then inspect `Evidence` if you need detail.
- If `Recommendation` is `ready_with_risks`, read the `Residual Risk` signal first.
- If `Recommendation` is `needs_investigation`, read `Verification`, `Unknowns`, and `Acceptance` before making a merge decision.
- If `Recommendation` is `blocked`, stop at `Decision Drivers`; the status is already telling you not to proceed.
- If `Scenario Coverage` is `incomplete`, decide whether the Work Item has explicit `ready_with_risks` acknowledgement plus `residualRisks`, `followUps`, or `unverifiedScenarios`. If it does, the task may still be reviewable with risks; if it does not, treat the missing coverage as investigation work.
- If the Preflight Review is `needs_human_confirmation` or `not_ready`, pause implementation and report the review to the user before continuing, even if Cockpit Status is otherwise visible and readable.

## Reviewer-Facing Examples

These examples use the same structure as the generated status file.

### 1. Clean Ready

```text
Recommendation: ready_for_review
Governance Signals:
- Intent: resolved
- Acceptance: complete
- Unknowns: resolved
- Verification: passed
- Guidelines: satisfied
- Checkpoints: complete
- Residual Risk: low
- Scenario Coverage: not_required

Decision Drivers:
- none
```

Use this when the task is complete, the checks passed, and there is no meaningful residual risk.

### 2. Ready With Medium Residual Risk

```text
Recommendation: ready_with_risks
Governance Signals:
- Intent: resolved
- Acceptance: complete
- Unknowns: resolved
- Verification: passed
- Guidelines: satisfied
- Checkpoints: complete
- Residual Risk: medium
- Scenario Coverage: complete

Decision Drivers:
- highest residual risk: medium
```

Use this when the implementation is ready, but the reviewer should consciously accept the stated risk.

### 3. Scenario Coverage Incomplete but Ready With Risks

```text
Recommendation: ready_with_risks
Governance Signals:
- Intent: resolved
- Acceptance: complete
- Unknowns: resolved
- Verification: passed
- Scenario Coverage: incomplete
- Guidelines: satisfied
- Checkpoints: complete
- Residual Risk: medium

Decision Drivers:
- required scenario unverified: GitHub Actions checkout extraheader reuse
```

Use this when the task is ready for review, but one or more required scenarios remain unverified and the Summary explicitly records the residual risk, follow-up path, or unverified scenario list.

### 4. Missing Verification

```text
Recommendation: needs_investigation
Governance Signals:
- Intent: resolved
- Acceptance: incomplete
- Unknowns: resolved
- Verification: incomplete
- Guidelines: satisfied
- Checkpoints: incomplete
- Residual Risk: low
- Scenario Coverage: not_required

Decision Drivers:
- required verification incomplete (missing: aiSummary; not_run: aiStatusCheck)
```

Use this when required checks are still missing or have not been recorded as passed.

### 5. Unknowns Remaining

```text
Recommendation: needs_investigation
Governance Signals:
- Intent: resolved
- Acceptance: incomplete
- Unknowns: open
- Verification: passed
- Guidelines: satisfied
- Checkpoints: complete
- Residual Risk: low
- Scenario Coverage: not_required

Decision Drivers:
- contract unknowns: 1
- summary unknownsRemaining: 2
```

Use this when the Work Item still has open questions and the reviewer should not treat it as finished.

### 6. Intent Unresolved

```text
Recommendation: needs_investigation
Governance Signals:
- Intent: unresolved
- Acceptance: incomplete
- Unknowns: resolved
- Verification: passed
- Guidelines: satisfied
- Checkpoints: complete
- Residual Risk: low
- Scenario Coverage: not_required

Decision Drivers:
- intent alignment unresolved for: problem, constraints
```

Use this when the task has a meaningful intent but the Summary does not yet prove that the declared intent was satisfied.

## Stabilization Rule

V2.5 stabilization should validate these examples against real Work Items before V3 is considered.
If the model starts needing more fields or longer output to explain itself, that is a signal to refine the review process, not to expand the status surface.
