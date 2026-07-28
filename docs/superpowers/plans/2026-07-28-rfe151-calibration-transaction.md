---
author: Ray
title: "RFE-151 Calibration Transaction Implementation Plan"
description: TDD plan for fail-closed Calibration evidence, Candidate-bound confirmation, and Active/Session rollback.
---

# RFE-151 Calibration Transaction Implementation Plan

## Goal

Close RFE-ISSUE-151 without weakening current evidence boundaries. The finished
runtime must make Unknown and incomplete checklist evidence machine-blocking,
bind two human phase records to one prepared Candidate identity, and restore
Active plus Session exactly when either persistence step fails.

## Constraints

- Work only on
  `codex/rfe151-calibration-transactional-confirmation-20260728`.
- Use one Contract, archive bundle, PR, merge, and lifecycle closure.
- Implement with red-green-refactor tests.
- Do not start RFE-152 until this Work Item reports `ready_on_base`, both Work
  Item branches are absent, and clean `main` equals `origin/main`.
- Do not claim trusted human identity or physical multi-file atomicity.

## File responsibilities

| File | Responsibility |
| --- | --- |
| `scripts/ai_calibrate.py` | Core schema migration, blocker model, evidence record, Candidate identity, confirmation binding, and persistence transaction. |
| `scripts/ai_calibration_wizard.py` | Presentation/orchestration adapter that delegates all authority to the core. |
| `tests/test_calibration_session.py` | Core, CLI, migration, digest, and byte-restoration regressions. |
| `tests/test_calibration_wizard.py` | Wizard parity, display, stale Candidate, and transaction regressions. |
| `docs/reference/calibration-session.md` | Authoritative runtime lifecycle and non-claims. |
| `docs/getting-started/installation*.md` | Aligned beginner prompts and exact prepare/confirm/activate sequence. |
| `docs/reference/documentation-context-registry.json` | Current design/plan classification. |
| `docs/reference/remediation-instruction-traceability.json` | RFE-151 instruction-to-plan-to-test bindings. |
| `.ai/cockpit/sbom.json` | Regenerated release evidence if source digests require it. |

## Task 1: Establish red baselines

Add focused tests before production edits:

1. all ten Unknown answers incorrectly pass core completion today;
2. complete answers with no structured evidence have no deterministic blocker;
3. confirmation accepts no Candidate identity;
4. answer/evidence mutation cannot invalidate a non-existent confirmation
   binding;
5. v1 Unknown/confirmation data can load with false-complete authority;
6. Active replacement followed by Session replacement failure leaves split
   state;
7. Wizard and direct CLI do not share one activation transaction.

Run only the new node IDs and preserve their expected failures in the Summary.

## Task 2: Add schema v2 and shared blockers

Implement:

- schema version 2 Session creation;
- fail-closed v1-to-v2 in-memory migration;
- `record_checklist_evidence`;
- deterministic blocker output keyed by stage and field;
- Candidate/confirmation invalidation on answer or evidence mutation;
- review, stage/full checks, and simulation through the same predicates.

Run the Unknown, incomplete evidence, and migration tests until green. Refactor
duplicate Wizard guards out only after parity tests pass.

## Task 3: Prepare and bind Candidate identity

Implement canonical JSON bytes, SHA-256 digest, monotonic revision, explicit
`prepare_candidate`, and confirmation parameters for exact revision/digest.
Activation must recompute and compare identity.

Run stale digest, changed-after-confirmation, separate reviewer/owner, and
successful preparation tests. Confirm that old phase records are not
authorizing after migration or mutation.

## Task 4: Implement recoverable persistence

Implement atomic single-file writes and one Active/Session transaction helper.
Capture exact original bytes/existence, stage final bytes, replace in order, and
restore both paths on every exception. Provide an injectable replace/write
boundary for deterministic tests rather than production-only failure flags.

Run:

- Active replace failure;
- Session replace failure after Active success;
- pre-existing files restored byte-for-byte;
- newly created files removed;
- rollback failure emits explicit unproved-consistency error;
- successful transaction persists matching Candidate identity.

## Task 5: Align CLI and Wizard

Add direct CLI actions/arguments for evidence recording, Candidate preparation,
digest-bound confirmation, and transactional activation. Update Wizard methods
and rendering to expose Session path, blockers, Candidate revision/digest, and
state. Remove adapter-only authority checks once core parity is proven.

Extend in-process CLI and Wizard happy-path tests. Run both focused test files.

## Task 6: Align documentation and traceability

Update the runtime reference and three installation languages:

1. fill every checklist column through the schema-supported Session evidence
   interface;
2. run full self-check and Governance Simulation;
3. prepare Candidate and display Session ID/path/revision/SHA-256;
4. obtain reviewer and owner decisions separately against that exact identity;
5. activate through the transaction;
6. STOP on Unknown, missing evidence, stale Candidate, digest mismatch, or
   rollback/unproved consistency;
7. preserve the external actor-identity non-claim.

Register the design/plan, update RFE-151 traceability, and record parent-plan
status without marking closure before provider evidence exists.

## Task 7: Governed finish

1. Run focused tests, metadata/system invariants, installer distribution checks,
   and `make quality-fast`.
2. Generate required checkpoints only after Contract stability.
3. Update Summary bidirectionally for every user instruction, acceptance item,
   changed file, observed failure, and residual risk.
4. Run `make ai-finish
   TASK=rfe151-calibration-transactional-confirmation-20260728`.
5. Commit archive evidence and run
   `make check-ai-pr AI_BASE_COMMIT=3a09fc880683991762eb9e38806e5b74eb02821a`.
6. Push, open one PR, wait for all Hosted checks, merge without provider branch
   deletion, and run corrected `make ai-close-work-item`.
7. Verify branch absence and clean synchronized `main`, then advance only to
   RFE-152.
