---
author: Ray
title: "RFE-096 Resume Verification Generation Corrective Implementation Plan"
description: Bind resumed Work Item verification evidence to the latest trusted resume transition.
---

# RFE-096 Resume Verification Generation Corrective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure resumed Work Items cannot satisfy current checkpoints or required gates with verification records retained from an earlier execution generation.

**Architecture:** Add one deterministic helper in `scripts/ai_common.py` that derives the latest valid resume cutoff and filters Summary verification records by `executedAt`. Both `ai_checkpoint` and `ai_check_agent_risk` consume that helper. No Contract revision model or new lifecycle command is introduced.

**Tech Stack:** Python standard library, pytest, JSON governance records, GNU Make lifecycle.

## Global Constraints

- Preserve the dirty RFE-095 worktree as failed investigation evidence until this replacement closes.
- Do not introduce `contractRevisionHistory`, `ai-revise-work-item`, or another Contract mutation protocol.
- The latest `resumeHistory[].recordedAt` is the only current-generation cutoff.
- A malformed non-empty resume history fails closed.
- Do not resume Dependabot #441 until PR, Hosted CI, merge, `ai-close-work-item`, and branch cleanup complete.

## Operator Guidance / 運用ガイダンス

After a successful resume, historical verification records remain reviewable
audit history, but only records executed at or after the latest trusted
`resumeHistory.recordedAt` may satisfy checkpoints or required gates. Missing
or malformed generation timestamps fail closed.

再開後も過去の検証記録はレビュー可能な監査履歴として残ります。ただし、
checkpoint や必須 gate を満たせるのは、最新の信頼済み
`resumeHistory.recordedAt` 以降に実行された記録だけです。検証世代の timestamp
が欠落または不正な場合は fail closed です。

### Task 1: Prove the stale-generation defect

**Files:** `tests/test_ai_checkpoint.py`, `tests/test_ai_check_agent_risk.py`.

**Interfaces:**
- Consumes: existing `ai_checkpoint.record_checkpoint(summary, contract, stage, contract_path, summary_path)` and `ai_check_agent_risk.validate_agent_risks(contract, summary, expected_contract_hash="")`.
- Produces: red-first behavioral fixtures for pre-resume history, post-resume late verification, repeated resumes, malformed timestamps, and non-resumed compatibility.

- [ ] Add a checkpoint test with a passed verification at `2026-07-29T07:00:00+00:00` and a resume transition at `2026-07-29T07:30:00+00:00`; assert `before_edit.requiredChecksPassed == 0`.
- [ ] Add a checkpoint test with a passed verification at `2026-07-29T07:31:00+00:00`; assert `before_edit.requiredChecksPassed == 1`.
- [ ] Add a two-transition fixture whose latest transition is `2026-07-29T08:00:00+00:00`; assert a `07:45` pass is stale and an `08:01` pass is current.
- [ ] Add malformed-latest-transition fixtures and assert checkpoint/risk validation fails closed with `latest resumeHistory.recordedAt is invalid`.
- [ ] Add an ordinary Contract without `resumeHistory`; assert its existing passed verification remains eligible.
- [ ] Run `PYTHONPATH=scripts /Users/sei-rinn/dev/workspace_python/ai-cockpit-template/.venv/bin/python -m pytest -q tests/test_ai_checkpoint.py tests/test_ai_check_agent_risk.py`; verify the new resume-generation assertions fail because current code reads all records.

### Task 2: Implement one current-generation evidence boundary

**Files:** `scripts/ai_common.py`, `scripts/ai_checkpoint.py`, `scripts/ai_check_agent_risk.py`.

**Interfaces:**
- Produces: `verification_status_for_generation(summary: dict[str, Any] | None, contract: dict[str, Any]) -> dict[str, str]`.
- Consumes: each verification record's `executedAt` and the latest transition's `recordedAt`; records at or after the cutoff are current.
- Error contract: raises `ValueError("latest resumeHistory.recordedAt is invalid")` or `ValueError("verification record executedAt is required after resume")` when current-generation identity cannot be proven.

- [ ] Parse the latest non-empty resume transition with timezone-aware `datetime.fromisoformat`; reject missing, malformed, or timezone-naive values.
- [ ] If no `resumeHistory` key exists, retain the existing last-record-per-check behavior.
- [ ] If resume history exists, require every candidate verification record to have a valid timezone-aware `executedAt`, ignore records before the latest cutoff, and preserve the last current record per check.
- [ ] Replace checkpoint display, next-action, and checkpoint-record counting with the shared helper.
- [ ] Replace agent-risk required-gate status extraction with the same helper; convert parsing failures into one precise validation issue.
- [ ] Re-run the two focused test files; all tests must pass.

### Task 3: Align durable process documentation and traceability

**Files:** `.ai/cockpit/README.md`, `.ai/cockpit/README.ja.md`, `docs/reference/capability-truth-matrix.json`, `docs/reference/documentation-context-registry.json`, `docs/reference/remediation-instruction-traceability.json`, `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`, and the active Summary.

**Interfaces:**
- Produces: English/Japanese guidance that historical verification remains audit evidence but cannot satisfy gates after the latest resume.
- Produces: one traceability directive linking user instruction, Contract, helper, consumers, tests, and lifecycle commands.

- [ ] Document the latest-resume generation boundary in English and Japanese without claiming #441 is complete.
- [ ] Regenerate Capability Truth JSON because `.ai/cockpit/README.md` is source evidence for `repository_governance_layer`; do not change capability status.
- [ ] Register this focused plan as `current_instruction`.
- [ ] Add a new traceability directive that records RFE-095 as rejected overdesign and RFE-096 as the bounded replacement.
- [ ] Update the comprehensive plan to place RFE-096 closure before #441 resume.
- [ ] Complete Summary changed-file reasons, source use, scenarios, guideline compliance, observed issue, residual risk, and documentation alignment.

### Task 4: Verify and complete the full lifecycle

**Files:** active Summary, generated status, archive Contract/Summary/manifest/index.

**Interfaces:**
- Consumes: canonical `make` entrypoint resolved for this worktree.
- Produces: exact-Head local and Hosted evidence, merged PR ownership, closure receipt, and branch cleanup.

- [ ] Before Task 1 test edits, run `make ai-prepare-implementation CONTRACT=.ai/work-items/active/rfe-096-resume-verification-generation-corrective-20260729.contract.json SUMMARY=.ai/work-items/active/rfe-096-resume-verification-generation-corrective-20260729.summary.json`; assert `before_edit.requiredChecksPassed == 0`.
- [ ] Run focused tests and all required Contract checks, then run `make ai-finish TASK=rfe-096-resume-verification-generation-corrective-20260729`.
- [ ] Commit the archive bundle and run `make check-ai-pr AI_BASE_COMMIT=49b1d726b4cf158208dbab11f5c81d9e1a3408fa`.
- [ ] Push one dedicated branch, open one PR, wait for every required Hosted check, and merge without provider-side branch deletion.
- [ ] Run `make ai-close-work-item TASK=rfe-096-resume-verification-generation-corrective-20260729`; prove remote branch absence, local branch cleanup, and synchronized base.
- [ ] Only after closure, rebase #441 onto the new `origin/main`, run `make ai-resume-work-item`, and replay its canonical `before_edit` plus all current-generation checks.

## Self-Review

- Every acceptance item maps to a behavioral test, shared implementation boundary, documentation change, or lifecycle postcondition.
- No step introduces the rejected Contract revision design.
- The test expectations use literal timestamps and observable outputs rather than source-text assertions.
- The plan keeps #441, dependency intake, installation restructuring, and release work outside this corrective PR.
