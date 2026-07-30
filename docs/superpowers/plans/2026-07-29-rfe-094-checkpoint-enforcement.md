---
author: Ray
title: "RFE-094 Checkpoint Enforcement Implementation Plan"
description: Prevent late before-edit checkpoint evidence and replay the source-bound release projection correction.
---

# RFE-094 Checkpoint Enforcement Implementation Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent late `before_edit` checkpoint evidence, then replay the dependent source-bound release-projection correction under that enforced lifecycle.

**Architecture:** A new Make entrypoint runs the ready preflight then records the active Summary's `before_edit` checkpoint. The independent risk gate rejects a record created after required verification has started. The linked source-bound refresh is then replayed as one deterministic local transaction.

**Tech Stack:** Python standard library, GNU Make, pytest, JSON governance records.

## Global Constraints

- Never fabricate, backdate, or manually write checkpoint evidence.
- Keep provider release state, tags, archives, public assets, and version candidates out of scope.
- The refresh may change only `release.json.supplyChain.sbomDigest` and `release.json.supplyChain.provenanceDigest`.
- Do not resume Dependabot #441 until this Work Item has completed PR merge and lifecycle closure.

### Task 1: Enforce the pre-edit preparation path

**Files:** `Makefile`, `scripts/ai_checkpoint.py`, `scripts/ai_check_agent_risk.py`, `AGENTS.md`, `tests/test_ai_checkpoint.py`, `tests/test_ai_check_agent_risk.py`, and `tests/test_makefile.py`.

- [ ] Add a failing Makefile test proving `ai-prepare-implementation` exists and invokes `ai-preflight` before `ai-checkpoint STAGE=before_edit`.
- [ ] Add a failing risk-gate test where a recorded `before_edit` has `requiredChecksPassed: 1`; assert the exact rejection says the checkpoint must precede required verification.
- [ ] Run `PYTHONPATH=scripts .venv/bin/python -m pytest -q tests/test_ai_checkpoint.py tests/test_ai_check_agent_risk.py tests/test_makefile.py`; it must fail only on the new assertions.
- [ ] Implement `ai-prepare-implementation`, requiring both `CONTRACT` and `SUMMARY`, with ordered preflight then checkpoint. Document it as the only code-mode start command after a ready Contract.
- [ ] Make `validate_agent_risks` reject a required `before_edit` record whose completed-required-check count is nonzero. Do not relax `ai-finish` or any gate.
- [ ] Re-run the focused tests; they must pass. Commit as `fix: enforce pre-edit checkpoint preparation`.

### Task 2: Replay atomic source-bound candidate evidence refresh

**Files:** `scripts/check_supply_chain.py`, `Makefile`, `tests/test_supply_chain.py`, `tests/test_release_distribution.py`, `tests/test_makefile.py`, `.ai/cockpit/{sbom,provenance,release-digests}.json`, `release.json`, `docs/reference/capability-truth-matrix.json`, and Japanese assessment outputs.

- [ ] Add a failing temporary-path regression named `test_refresh_candidate_evidence_synchronizes_local_release_projection`.
- [ ] The regression must assert SBOM and Provenance byte SHA-256 values are projected into exactly the two `release.json.supplyChain` digest fields, all identity/publication/security fields are unchanged, and `supply_chain_issues` is empty.
- [ ] Run the regression; it must fail because the atomic refresh does not exist.
- [ ] Implement `refresh_candidate_evidence(source_commit)`: write SBOM, write Provenance, synchronize only the two release projection digests, then write release-digests. Expose it as `make refresh-candidate-release-evidence SOURCE_COMMIT=<sha>`; all existing check targets remain validation-only.
- [ ] Run focused supply-chain, release-distribution, and Makefile tests; they must pass.
- [ ] Regenerate bounded local evidence with the final source, then check the Japanese final reassessment source binding. Commit as `fix: synchronize candidate release evidence`.

### Task 3: Trace, validate, archive, and close

**Files:** documentation context registry, instruction traceability, comprehensive remediation plan, active Summary, generated status, and archive records.

- [ ] Add a directive mapping the user’s process-first instruction to the preparation entrypoint, late-record test, atomic refresh, and acceptance evidence. Record the old RFE-093 branch as rejected lifecycle evidence, not completed work.
- [ ] Before any Task 1 or Task 2 implementation write beyond this plan/Contract/Summary, run `make ai-prepare-implementation CONTRACT=.ai/work-items/active/rfe-094-checkpoint-enforcement-20260729.contract.json SUMMARY=.ai/work-items/active/rfe-094-checkpoint-enforcement-20260729.summary.json`. Expected record: `before_edit`, `requiredChecksPassed: 0`.
- [ ] Update the Summary with factual verification, observed process deviation, limitations, guideline compliance, and documentation alignment.
- [ ] Run `make ai-finish TASK=rfe-094-checkpoint-enforcement-20260729` once after focused validation. It must archive only after all required checks pass.
- [ ] Commit the archive bundle, run `make check-ai-pr AI_BASE_COMMIT=03c0d2c4a221665d1f480c4833fb6ed6efbbbc96`, push, open one PR, wait for Hosted CI, merge without provider branch deletion, then run `make ai-close-work-item TASK=rfe-094-checkpoint-enforcement-20260729`.

## Self-Review

- Task 1 prevents the exact omission without allowing a post-hoc substitute.
- Task 2 restores the paused corrective without release/provider mutation.
- Task 3 proves bidirectional traceability and the full lifecycle before #441 resumes.
