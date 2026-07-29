---
author: Ray
title: RFE-098 Human-Visible Completion Report Implementation Plan
description: Implement a direct, decision-oriented closure handoff for every Work Item.
---

# RFE-098 Human-Visible Completion Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make verified Work Item closure results immediately understandable in the human conversation, with evidence paths retained only as optional audit detail.

**Architecture:** Add a deterministic report renderer beside the close lifecycle output. It consumes only the verified `close_work_item` result, rejects incomplete facts, and formats a fixed decision-first report. Repository rules require executors to forward that canonical text after closure.

**Tech Stack:** Python standard library, pytest, Markdown, AI Cockpit lifecycle.

## Global Constraints

- Do not alter provider, PR merge, release, tag, or branch-cleanup semantics.
- Do not edit historical archives.
- Generate report prose only from verified closure-result values.
- Audit paths remain available after the human summary, not before it.

---

### Task 1: Define failing report-rendering behavior

**Files:**
- Modify: `tests/test_work_item_lifecycle_closure.py`
- Modify: `scripts/ai_close_work_item.py`

- [ ] **Step 1: Write failing tests for ready and detached results**

```python
def test_render_human_completion_report_leads_with_verified_decision_facts():
    report = render_human_completion_report(ready_result)
    assert report.index("## Human completion report") < report.index("Optional audit evidence")
    assert "Hosted CI: passed" in report
    assert "Repository state: ready for the next Work Item" in report

def test_render_human_completion_report_names_base_worktree_when_detached():
    report = render_human_completion_report(detached_result)
    assert "Current worktree: detached" in report
    assert detached_result["baseWorktree"] in report

def test_render_human_completion_report_rejects_missing_verified_fact():
    with pytest.raises(RuntimeError, match="Human completion report requires"):
        render_human_completion_report({"pullRequest": "https://example.invalid/pr/1"})
```

- [ ] **Step 2: Run focused tests and observe expected failures**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_work_item_lifecycle_closure.py -k human_completion_report`

Expected: FAIL because the renderer does not yet exist.

### Task 2: Implement the minimal deterministic renderer and CLI handoff

**Files:**
- Modify: `scripts/ai_close_work_item.py`
- Modify: `tests/test_work_item_lifecycle_closure.py`

- [ ] **Step 1: Implement `render_human_completion_report(result)`**

It validates the closure result fields, then produces fixed Markdown-like stdout text containing delivered scope, verified local archive evidence, verified merged PR/commit, cleanup/base state, residual-risk statement, and next-work guidance before optional audit paths. It does not claim a Hosted CI conclusion that is not in the closure result.

- [ ] **Step 2: Call the renderer only after successful `close_work_item`**

Keep failure output unchanged: a failed closure must not emit a success report.

- [ ] **Step 3: Run focused lifecycle tests**

Run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_work_item_lifecycle_closure.py`

Expected: PASS.

### Task 3: Codify direct human delivery and traceability

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/features/task-outcome-report.md`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`
- Modify: `docs/reference/remediation-instruction-traceability.json`
- Modify: `docs/reference/capability-truth-matrix.json`

- [ ] **Step 1: Require forwarding report text to the conversation**

State that the executor sends the canonical report directly after successful closure and adds the independently checked exact-head Hosted CI conclusion; Outcome/Receipt paths are optional links, not the report body.

- [ ] **Step 2: Update plan and traceability evidence**

Record RFE-098 as a blocking corrective before #441 resumption and map the user instruction to Contract, implementation, tests, local verification, Hosted CI, and closure evidence.

- [ ] **Step 3: Run relevant documentation and traceability checks**

Run: `make check-docs-metadata && make check-instruction-traceability`

Expected: PASS.

### Task 4: Complete governed lifecycle

- [ ] **Step 1: Run `make ai-prepare-implementation` before implementation**
- [ ] **Step 2: Run `make ai-finish TASK=rfe-098-human-visible-completion-report-20260729`**
- [ ] **Step 3: Run `make check-ai-pr AI_BASE_COMMIT=8b20fafb817d85e7f932a0997e00ed5140598afb`**
- [ ] **Step 4: Push one PR, verify exact-head Hosted CI, merge without provider branch deletion, and run `make ai-close-work-item TASK=rfe-098-human-visible-completion-report-20260729`**
- [ ] **Step 5: Forward the canonical Human completion report text to the user, then resume #441 from the synchronized base**

## Plan Self-Review

- Coverage: direct human report, truthful ready/detached behavior, incomplete-fact rejection, mandatory conversation handoff, and full lifecycle are all explicit.
- Boundaries: no external chat automation or lifecycle-provider mutation is proposed.
- Test quality: report assertions observe rendered user-facing behavior, not source text alone.
