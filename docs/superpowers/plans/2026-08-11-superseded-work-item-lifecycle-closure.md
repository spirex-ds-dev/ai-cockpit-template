---
author: Ray
title: "Superseded Work Item Lifecycle Closure Implementation Plan"
description: "TDD plan for one fail-closed successor-receipt rule across archive and closure."
status: historical
authority: implementation_record
---

# Superseded Work Item Lifecycle Closure Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let archive and closure consume one exact successor-bound superseded predecessor rule without weakening any provider or branch-cleanup gate.

**Architecture:** Move the narrow Summary-issue and successor-receipt predicate into `ai_lifecycle_truth.py`, retaining an archive compatibility wrapper. Apply the same predicate only after independent strict Contract and Summary validation in `ai_close_work_item.py`.

**Tech Stack:** Python 3.11+, pytest, repository AI Cockpit gates.

## Global Constraints

- Preserve the blocked predecessor Outcome and failed verification evidence exactly.
- Accept only `transition=superseded`; quarantined and every malformed or mismatched receipt remain ineligible.
- Do not change PR identity, exact Head SHA, clean-worktree, fast-forward synchronization, remote absence, or local branch deletion behavior.
- Use red-first tests before each production change.

---

### Task 1: Canonical superseded Summary exception

**Files:**
- Modify: `tests/test_ai_archive_work_item.py`
- Modify: `scripts/ai_lifecycle_truth.py`
- Modify: `scripts/ai_archive_work_item.py`

**Interfaces:**
- Consumes: `validate_successor_receipt(predecessor_outcome: Path, predecessor_work_item_id: str, receipt: object) -> str | None`
- Produces: `superseded_summary_validation_exception(contract_path: Path, work_item_id: str, summary_issues: list[str]) -> bool`
- Preserves: `ai_archive_work_item.superseded_archive_validation_exception(...) -> bool`

- [ ] **Step 1: Write the failing canonical-predicate tests**

Add tests that create a blocked Outcome plus a fully bound superseded receipt and assert the new lifecycle-truth predicate accepts only the two permitted Summary-error prefixes. Parameterize missing receipt, malformed JSON, `transition=quarantined`, wrong digest, wrong predecessor, non-blocked Outcome, foreign issue, missing authority, missing reason, and an unrelated Summary error as false cases.

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_ai_archive_work_item.py
```

Expected: failure because `ai_lifecycle_truth.superseded_summary_validation_exception` does not exist.

- [ ] **Step 3: Implement the shared predicate**

Add the predicate to `ai_lifecycle_truth.py`. It must load sibling `<task>.outcome.json` and `<task>.successor-receipt.json`, require only the exact Summary-error prefixes, require `transition=superseded`, and return true only when `validate_successor_receipt(...)` returns `None`.

Change `ai_archive_work_item.superseded_archive_validation_exception` into a thin call to the shared predicate. Do not retain a second receipt parser or error-prefix allowlist in the archive module.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_ai_archive_work_item.py
.venv/bin/python -m ruff check scripts/ai_lifecycle_truth.py scripts/ai_archive_work_item.py tests/test_ai_archive_work_item.py
```

Expected: all focused tests and lint pass.

### Task 2: Closure evidence integration

**Files:**
- Modify: `tests/test_work_item_lifecycle_closure.py`
- Modify: `scripts/ai_close_work_item.py`

**Interfaces:**
- Consumes: `superseded_summary_validation_exception(...) -> bool`
- Preserves: `_verify_archived_evidence(task: str) -> Path`

- [ ] **Step 1: Write the failing closure tests**

Add a test that uses a real archived Contract/Summary/red Outcome/superseded receipt and proves `_verify_archived_evidence` accepts the pair when strict Summary validation returns only the permitted required-verification failures. Add a paired test showing that an unrelated Summary issue remains fatal even with the valid receipt.

- [ ] **Step 2: Run the closure tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_work_item_lifecycle_closure.py -k 'superseded and archived_evidence'
```

Expected: the valid superseded case fails with `archived Work Item evidence is invalid`.

- [ ] **Step 3: Implement the narrow closure exception**

Import the shared predicate in `ai_close_work_item.py`. Keep Contract issues separate from Summary issues. Raise on any Contract issue. Raise on Summary issues unless the shared predicate accepts the exact archived sibling artifacts. Leave status and all later provider/cleanup code unchanged.

- [ ] **Step 4: Run focused and full closure regressions**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_work_item_lifecycle_closure.py tests/test_ai_archive_work_item.py
.venv/bin/python -m ruff check scripts/ai_lifecycle_truth.py scripts/ai_archive_work_item.py scripts/ai_close_work_item.py tests/test_ai_archive_work_item.py tests/test_work_item_lifecycle_closure.py
.venv/bin/python -m mypy scripts/ai_lifecycle_truth.py scripts/ai_archive_work_item.py scripts/ai_close_work_item.py
```

Expected: all tests and static checks pass.

### Task 3: Documentation and governed verification

**Files:**
- Modify: `docs/reference/work-item-lifecycle-closure.md`
- Modify: `.ai/work-items/active/superseded-work-item-lifecycle-closure.summary.json`
- Generated at finish: `.ai/cockpit/current_status.md`, `.ai/cockpit/task_report.json`, `.ai/cockpit/task_report.md`, `.ai/work-items/archive/**`

**Interfaces:**
- Consumes: focused test evidence from Tasks 1 and 2
- Produces: reviewer-facing lifecycle semantics and complete Work Item evidence

- [ ] **Step 1: Document the exceptional eligibility boundary**

State that a superseded predecessor retains a red Outcome and may pass archive/closure evidence validation only through an exact bound receipt; explicitly state that the cleanup preconditions remain unchanged.

- [ ] **Step 2: Update Summary scenario and verification evidence**

Record each changed file, red/green test result, the four verified Contract scenarios, guideline compliance, no open unknowns, and the user-authorized destructive scope. Do not mark full quality passed before the command completes.

- [ ] **Step 3: Run required verification and finish**

Run focused checks first, then the Contract-required AI gates, `make quality-fast`, `make quality-full`, `make quality-release`, `make ai-checkpoint ... STAGE=before_finish`, and `make ai-finish TASK=superseded-work-item-lifecycle-closure`. Archive, commit the evidence bundle, and run `make check-ai-pr AI_BASE_COMMIT=fc1cd030b0ab620f250cfe8db0dcc8429e4fc1d9`.

- [ ] **Step 4: Deliver and close**

Push the exact branch, open one PR against `main`, wait for every required hosted check, merge without provider-side branch deletion, then run `make ai-close-work-item TASK=superseded-work-item-lifecycle-closure`. Delete the exact remote ref through the configured authorized provider identity only if the standard Git identity again lacks delete permission and the closure postcondition proves the ref is the merged PR Head.
