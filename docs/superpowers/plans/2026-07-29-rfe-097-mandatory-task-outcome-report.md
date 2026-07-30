---
author: Ray
title: "RFE-097 Mandatory Task Outcome and Closure Receipt Implementation Plan"
description: Make every closed Work Item produce validated, visible reporting without inventing pre-merge provider facts.
---

# RFE-097 Mandatory Task Outcome and Closure Receipt Implementation Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every code-mode Work Item must archive a complete evidence-backed Task Outcome and, after merge, emit a validated Closure Receipt before branch cleanup.

**Architecture:** `ai-finish` deterministically derives a pre-merge Outcome from Contract and Summary evidence, validates and archives it, and never requires a manual opt-in. `ai-close-work-item` then creates a separate Closure Receipt from authoritative merged-PR and cleanup facts before any branch deletion. This preserves archive immutability and does not pretend that merge facts exist before the PR exists.

**Tech Stack:** Python standard library, pytest, JSON governance records, Markdown renderer, GNU Make lifecycle.

## Global Constraints

- Do not backfill or modify historical archive bundles.
- Do not invent PR, merge, release, or hosted-CI facts in the pre-merge Outcome.
- Outcome generation and validation must fail closed before archive; Closure Receipt generation and validation must fail closed before branch deletion.
- Retain the existing locale policy; this Work Item does not silently translate user-provided evidence.
- Do not resume #441 or change release state until this corrective PR is merged and closed.

### Task 1: Prove the current optional-report defect and define pre-merge bindings

**Files:** `tests/test_task_outcome_ai_finish_integration.py`, `tests/test_task_outcome.py`, `scripts/ai_check_task_outcome.py`, `scripts/ai_generate_task_outcome.py`.

**Interfaces:**
- Consumes: Contract v2, Summary v2, `ai_finish.run_task_outcome_pipeline`.
- Produces: a mandatory deterministic outcome input and validator support for `lifecycleStage: "pre_merge"` with explicit unavailable PR facts.

- [ ] **Step 1: Write failing no-opt-in Outcome tests**

```python
ok, _ = ai_finish.run_task_outcome_pipeline(task, summary_path, contract_path)
assert ok
assert json.loads(summary_path.read_text())["taskOutcome"]["markdownPath"] == "outcome.md"
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `PYTHONPATH=scripts /Users/sei-rinn/dev/workspace_python/ai-cockpit-template/.venv/bin/python -m pytest -q tests/test_task_outcome_ai_finish_integration.py`

Expected: FAIL because the current implementation returns `Outcome integration not requested`.

- [ ] **Step 3: Implement deterministic pre-merge evidence derivation**

```python
def build_pre_merge_outcome_input(contract: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    return {"taskId": contract["workItemId"], "bindings": {..., "lifecycleStage": "pre_merge", "pullRequest": {"state": "not_created"}}}
```

The bindings must contain Contract/Summary/verification digests and exact base/head commits. Derive Delivered Changes, warnings, observed issues, residual risks, human decisions, and evidence references from existing Summary fields without fabricating claims.

- [ ] **Step 4: Make validator and generator accept only explicit pre-merge provenance**

```python
assert outcome["bindings"]["lifecycleStage"] == "pre_merge"
assert outcome["bindings"]["pullRequest"] == {"state": "not_created"}
```

Keep merged/PR bindings strict when they are supplied. Reject missing lifecycle stage, invalid digest/commit bindings, or an ambiguous PR object.

- [ ] **Step 5: Run focused Outcome tests**

Run: `PYTHONPATH=scripts /Users/sei-rinn/dev/workspace_python/ai-cockpit-template/.venv/bin/python -m pytest -q tests/test_task_outcome.py tests/test_task_outcome_ai_finish_integration.py`

Expected: PASS, including no-opt-in generation and malformed binding failures.

### Task 2: Enforce the Outcome before archive

**Files:** `scripts/ai_finish.py`, `tests/test_task_outcome_ai_finish_integration.py`.

**Interfaces:**
- Consumes: active Contract and Summary.
- Produces: `.ai/work-items/active/<task>.outcome.json`, derived Markdown, and `Summary.taskOutcome` before status/archive.

- [ ] **Step 1: Replace optional-skip behavior with a mandatory pipeline**

```python
outcome_ok, outcome_message = run_task_outcome_pipeline(task, summary_path, contract_path)
if not outcome_ok:
    return 1
```

Run this before `aiStatus`, so the generated status and archive manifest can reference the validated Outcome.

- [ ] **Step 2: Add a failing generation/validation test**

```python
monkeypatch.setattr(ai_finish, "run", lambda *_args, **_kwargs: (1, 0, "invalid"))
assert not ok
assert state["status"] == "failed"
```

Assert the active raw evidence and Contract/Summary remain for retry; no archive helper is invoked.

- [ ] **Step 3: Run focused finish tests**

Run: `PYTHONPATH=scripts /Users/sei-rinn/dev/workspace_python/ai-cockpit-template/.venv/bin/python -m pytest -q tests/test_task_outcome_ai_finish_integration.py tests/test_start_and_archive.py`

Expected: PASS with archived Outcome JSON/Markdown manifest bindings retained.

### Task 3: Generate a fail-closed post-merge Closure Receipt

**Files:** `scripts/ai_close_work_item.py`, `tests/test_work_item_lifecycle_closure.py`.

**Interfaces:**
- Consumes: archived Outcome, archived Contract/Summary, verified merged PR facts, synchronized base facts.
- Produces: `target/task-closure-receipts/<task>.closure.md`, then returns its path in `close_work_item`.

- [ ] **Step 1: Write a failing receipt-before-deletion test**

```python
assert receipt_call_index < fake.commands.index(("push", "origin", "--delete", "codex/example"))
assert result["closureReceipt"].endswith("example.closure.md")
```

- [ ] **Step 2: Implement deterministic receipt generation and validation**

```python
def generate_closure_receipt(task, contract_path, outcome_path, pr, base, cleanup) -> tuple[Path, Path]:
    ...
```

The receipt must name the Work Item, archived Outcome path, merged PR URL/Head/merge commit, final base commit, remote/local cleanup intent, repository state, and next base worktree. It must refuse a missing Outcome or invalid PR facts.

- [ ] **Step 3: Insert receipt generation after authoritative PR/base verification and before `_delete_remote_branch`**

```python
receipt = generate_closure_receipt(...)
validate_closure_receipt(receipt)
_delete_remote_branch(...)
```

- [ ] **Step 4: Add receipt-failure regression**

```python
with pytest.raises(RuntimeError, match="Closure Receipt"):
    closure.close_work_item("example", fake)
assert not any(command[:3] == ("push", "origin", "--delete") for command in fake.commands)
```

- [ ] **Step 5: Run closure tests**

Run: `PYTHONPATH=scripts /Users/sei-rinn/dev/workspace_python/ai-cockpit-template/.venv/bin/python -m pytest -q tests/test_work_item_lifecycle_closure.py`

Expected: PASS with receipt-before-deletion ordering and failure preservation.

### Task 4: Align docs, traceability, and full lifecycle

**Files:** `docs/features/task-outcome-report.md`, `docs/features/task-outcome-report-self-check.md`, `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`, active Summary, generated status, archive bundle.

**Interfaces:**
- Produces: one explicit prospective rule: every code-mode Work Item has pre-merge Outcome and closure receipt; the assistant must surface the latter in its completion response.

- [ ] **Step 1: Document the two-stage fact boundary**

State that pre-merge Outcome is archived and bound to local evidence, while the Closure Receipt is generated only after authoritative provider merge/cleanup facts. State that historical reports are not retroactively rewritten.

- [ ] **Step 2: Preserve resolved evidence paths during archive**

Modify `scripts/ai_archive_work_item.py` and its archive tests so exact active Contract/Summary paths stored in Outcome evidence are rewritten to the same archive destination before the manifest digests the moved Outcome. Do not rewrite arbitrary prose or historical archives.

- [ ] **Step 3: Record RFE-ISSUE-097 in the authoritative plan**

Place RFE-097 before #441 resume, with the root cause (optional outcome), the bounded fix, and the exact lifecycle requirement.

- [ ] **Step 4: Complete Contract/Summary traceability**

Record changed-file reasons, focused and full verification, scenarios, guideline compliance, documentation alignment, residual risks, and user correction solidification. Include the specific no-change reason for each user-named source not modified.

- [ ] **Step 5: Run canonical verification and lifecycle**

Run `make ai-prepare-implementation` before implementation edits, focused tests after each task, all Contract gates, `make ai-finish`, archive, `make check-ai-pr`, one PR, exact-Head Hosted CI, merge, and `make ai-close-work-item`.

- [ ] **Step 6: Deliver the closing report to the user**

Use the generated Outcome and Closure Receipt to report: Work Item/PR, implementation, acceptance and Hosted evidence, discovered issues, documentation alignment, merge/branch/worktree cleanup, residual risk, and the next Work Item. Do not merely link a raw Summary.

## Self-Review

- Every requested report field maps to a machine artifact, lifecycle fact, or final user-facing receipt.
- Pre-merge Outcome cannot claim a PR, merge, release, or hosted result that does not yet exist.
- Closure failures occur before any branch deletion and preserve retryability.
- The plan does not backfill historical archives or broaden into #441, installation, Dependabot, release, or locale-policy work.
