# Work Item Close Idempotency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `ai-close-work-item` tolerate a platform-predeleted remote Work Item branch while preserving fail-closed cleanup verification.

**Architecture:** Keep the existing cleanup ordering and final postcondition check. Introduce a small deletion helper that executes the remote delete request non-fatally, refreshes remote refs, and accepts only a verified absent branch; all other failures remain exceptions.

**Tech Stack:** Python standard library, pytest, Git CLI, Markdown.

## Global Constraints

- Do not match provider-specific deletion error text or error codes.
- Do not accept a failed delete request unless `ls-remote` proves the branch is absent.
- Keep local base synchronization, clean-worktree checks, and merged-PR authorization unchanged.
- Do not modify Makefile, installer behavior, or unrelated lifecycle paths.

### Task 1: Add regression tests for idempotent remote deletion

**Files:**
- Modify: `tests/test_work_item_lifecycle_closure.py:8-35,140-150`
- Test: `tests/test_work_item_lifecycle_closure.py`

**Interfaces:**
- Consumes: `closure.close_work_item`, `FakeGit`, and `CommandResult`.
- Produces: deterministic tests for absent, existing, and unverifiable remote branch outcomes.

- [ ] **Step 1: Extend the fake runner to model the remote branch state and deletion failure.**

  Add a constructor option for `remote_branch_exists` and return `0` from `ls-remote` when true, `2` when false. Keep the existing forced failure behavior for the delete command.

- [ ] **Step 2: Add the failing race test.**

  Configure the delete command to fail while `remote_branch_exists=False`; assert `close_work_item` returns `state == "closed"` and performs the prune plus final remote check.

- [ ] **Step 3: Add the unverifiable-state test.**

  Configure the delete command to fail and `ls-remote` to return a non-2 error; assert `close_work_item` raises and does not report success.

- [ ] **Step 4: Run the focused tests before implementation.**

  Run: `pytest tests/test_work_item_lifecycle_closure.py -q`

  Expected: the new race test fails because the current checked runner raises immediately at `push --delete`; existing tests pass.

### Task 2: Implement verified idempotent deletion

**Files:**
- Modify: `scripts/ai_close_work_item.py:166-199`

**Interfaces:**
- Consumes: existing `Runner`, `CommandResult`, `_remote_branch_absent`, and cleanup ordering.
- Produces: a private helper used by `close_work_item` that returns only after remote deletion is verified.

- [ ] **Step 1: Add a helper that runs the delete request with `check=False`.**

  The helper must always run `fetch <remote> --prune` with `check=True`, then call `_remote_branch_absent`. If the final check succeeds, return regardless of the delete request's return code. If refresh or final verification fails, propagate the failure.

- [ ] **Step 2: Replace the direct `push --delete` call with the helper.**

  Preserve local branch deletion before the helper and all final base/worktree checks after it.

- [ ] **Step 3: Run focused tests.**

  Run: `pytest tests/test_work_item_lifecycle_closure.py -q`

  Expected: all lifecycle closure tests pass, including the predeleted-branch race and fail-closed failure cases.

### Task 3: Document and verify the completed change

**Files:**
- Modify: `docs/reference/work-item-lifecycle-closure.md:25-41`

**Interfaces:**
- Consumes: the implemented helper behavior and lifecycle protocol.
- Produces: explicit documentation of the idempotent remote deletion postcondition.

- [ ] **Step 1: Update the protocol text.**

  State that a delete request racing with platform auto-deletion is accepted only when the refreshed remote ref check proves the branch is absent; all unverifiable states remain failures.

- [ ] **Step 2: Run project tests and required AI checks.**

  Run the contract-declared checks through the Make targets, then run the project test command from `.ai/cockpit/checks.yaml`.

  Expected: all required checks pass and the Summary records every result.

- [ ] **Step 3: Run `make ai-checkpoint` at `before_finish` and update Summary/Status.**

  Record changed files, test evidence, checkpoint evidence, guideline compliance, residual risks, and review readiness before `make ai-finish TASK=work_item_close_idempotency`.
