---
author: Codex
title: "Synchronization Conflict Outcome Implementation Plan"
description: "Implementation plan for #709 canonical blocked Outcome recovery evidence."
---

# Synchronization Conflict Outcome Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a real, automatically aborted governed synchronization conflict emit canonical red Outcome and Human Benefit Report evidence so the existing conflict-successor route can bind it.

**Architecture:** Keep rebase detection and automatic abort in `ai_resume_work_item`. Make the existing blocked-Outcome writer in `ai_finish` target-root aware, then invoke it only when the rebase helper reports a safely aborted conflict. The command still fails; it now leaves the required recovery evidence in the source worktree.

**Tech Stack:** Python 3 standard library, pytest, local Git fixtures, repository Make lifecycle targets.

## Global Constraints

- Use Issue #709; do not create a new Issue for this omission.
- Never handwrite an Outcome, resolve a rebase manually, force-push, merge, release, or mutate provider state.
- Emit only after automatic conflict abort; successful synchronization must not emit a blocked Outcome.
- Resolve Contract, Summary, Outcome, report, and status paths from the explicit synchronization target root.
- Preserve the Start Receipt and source Contract; commit the generated blocked
  Outcome, Summary state, and report through the existing authorized
  checkpoint boundary so the conflict-successor validator receives a clean
  source worktree.

---

### Task 1: Make canonical blocked Outcome persistence target-root aware

**Files:**
- Modify: `scripts/ai_finish.py:586-900`
- Test: `tests/test_task_outcome_ai_finish_integration.py`

**Interfaces:**
- Consumes: active Work Item ID, Contract path, Summary path, failed gate, failure message, explicit `project_root: Path`.
- Produces: `(bool, str)` from `write_blocked_outcome`, JSON/Markdown Outcome paths and a derived Human Benefit Report inside `project_root`.

- [ ] **Step 1: Write the failing test**

```python
def test_write_blocked_outcome_uses_explicit_target_root(tmp_path: Path) -> None:
    target = _active_work_item_root(tmp_path, task="source")
    ok, message = ai_finish.write_blocked_outcome(
        "source", target / ".ai/work-items/active/source.contract.json",
        target / ".ai/work-items/active/source.summary.json",
        failed_check="synchronization_conflict", failure_message="rebase conflicted and was aborted",
        project_root=target,
    )
    assert ok, message
    assert (target / ".ai/work-items/active/source.outcome.json").is_file()
    assert not (Path.cwd() / ".ai/work-items/active/source.outcome.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_task_outcome_ai_finish_integration.py::test_write_blocked_outcome_uses_explicit_target_root -q`

Expected: FAIL because `write_blocked_outcome` has no `project_root` parameter or writes relative to its module root.

- [ ] **Step 3: Write minimal implementation**

```python
def write_blocked_outcome(..., project_root: Path = PROJECT_ROOT) -> tuple[bool, str]:
    project_root = project_root.resolve()
    json_path = project_root / ".ai/work-items/active" / f"{task}.outcome.json"
    markdown_path = project_root / ".ai/work-items/active" / f"{task}.outcome.md"
    payload = _pre_merge_outcome_input(
        task, contract_path, summary_path, project_root=project_root
    )
```

Thread `project_root` through `_outcome_paths`, `_pre_merge_outcome_input`,
`run_human_report_pipeline`, and any status/report helpers used by the blocked
writer. Preserve existing callers through the default argument.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_task_outcome_ai_finish_integration.py::test_write_blocked_outcome_uses_explicit_target_root -q`

Expected: PASS; JSON, Markdown, and report are inside the target root.

### Task 2: Emit the Outcome only after an aborted synchronization conflict

**Files:**
- Modify: `scripts/ai_resume_work_item.py:264-340`
- Test: `tests/test_start_and_archive.py:790-930`

**Interfaces:**
- Consumes: `synchronize_contract(..., project_root=source)` and a real local Git conflict.
- Produces: a raised `ResumeError`, a clean source checkpoint head, and canonical source Outcome evidence with `failedGate == "synchronization_conflict"`.

- [ ] **Step 1: Write the failing test**

```python
with pytest.raises(ResumeError, match="rebase conflicted and was aborted"):
    synchronize_contract(..., project_root=source)

outcome = json.loads((source / ".ai/work-items/active/paused-task.outcome.json").read_text())
assert outcome["status"] == "blocked"
assert outcome["failedGate"] == "synchronization_conflict"
assert (source / ".ai/work-items/active/paused-task.outcome.md").is_file()
```

Remove the fixture's handwritten Outcome before this assertion so the test
fails only because production code does not yet persist it.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_start_and_archive.py::test_conflicted_synchronization_binds_a_current_main_successor_without_source_mutation -q`

Expected: FAIL because no Outcome file exists after the production conflict.

- [ ] **Step 3: Write minimal implementation**

```python
try:
    _rebase_onto(project_root, target)
except ResumeError as exc:
    if str(exc) != "rebase conflicted and was aborted":
        raise
    ok, detail = write_blocked_outcome(
        work_item_id, contract_path, summary_path,
        failed_check="synchronization_conflict", failure_message=str(exc),
        project_root=project_root,
    )
    if not ok:
        raise ResumeError(f"{exc}; blocked Outcome persistence failed: {detail}")
    raise
```

Import only the canonical writer. Do not write JSON directly and do not catch
or alter any non-conflict validation/rebase failure.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_start_and_archive.py::test_conflicted_synchronization_binds_a_current_main_successor_without_source_mutation -q`

Expected: PASS; the transition receipt binds the generated Outcome, while the
source Contract/Summary and checkpoint head remain unchanged after the abort.

### Task 3: Preserve the successful path and publish lifecycle documentation

**Files:**
- Modify: `tests/test_start_and_archive.py`
- Modify: `docs/reference/ai-cockpit-work-item-lifecycle.md`
- Modify: `docs/reference/capability-truth-matrix.json`
- Modify: `docs/reference/japanese-capability-assessment.json`
- Modify: `docs/reference/japanese-capability-assessment.md`
- Modify: `docs/reference/pre-release-documentation-alignment.json`
- Modify: `docs/reference/pre-release-documentation-alignment.md`

**Interfaces:**
- Consumes: successful `synchronize_contract` fixture and canonical documentation generators.
- Produces: proof that success writes no blocked Outcome and documentation stating the conflict-only recovery boundary.

- [ ] **Step 1: Write the failing success-path assertion**

```python
transition = synchronize_contract(..., project_root=root)
assert transition["toBaseCommit"] == target
assert not (root / ".ai/work-items/active/paused-task.outcome.json").exists()
```

- [ ] **Step 2: Run test to verify it fails or demonstrates missing coverage**

Run: `pytest tests/test_start_and_archive.py -k synchronization -q`

Expected: the new assertion is the explicit regression guard for the success
path; if it already passes, record that it proves no code change is needed for
this boundary.

- [ ] **Step 3: Regenerate documentation projections**

```text
python3 scripts/ai_capability_truth.py --write
python3 scripts/ai_japanese_capability.py --write
python3 scripts/check_pre_release_documentation_alignment.py --write
```

Update the lifecycle reference to state: an automatically aborted
synchronization conflict writes a red `synchronization_conflict` Outcome before
the conflict-successor route may run; it does not authorize archive, merge,
release, or manual conflict resolution.

- [ ] **Step 4: Run focused verification**

Run: `pytest tests/test_start_and_archive.py -k synchronization -q`

Expected: PASS; successful synchronization has no blocked Outcome and the
conflict path remains evidence-bound.

### Task 4: Finish governed verification and delivery

**Files:**
- Modify: `.ai/work-items/active/conflict-successor-outcome-709-current-main.summary.json`
- Generate: `.ai/cockpit/current_status.md`, task report, archived Work Item evidence

- [ ] **Step 1: Update the Summary**

Record the exact red/green focused test commands, generated documentation
command, root-isolation evidence, and the fact that the #662 checkpoint source
remained untouched after conflict abort.

- [ ] **Step 2: Run required lifecycle checks**

Run: `make ai-finish TASK=conflict-successor-outcome-709-current-main`

Expected: every declared governance check and Contract-required quality check
passes; archive only after the active green Outcome is reported.

- [ ] **Step 3: Deliver through the canonical PR lifecycle**

Run: `make check-ai-pr AI_BASE_COMMIT=2308627944e1867a1abb63f8bdc68befbe9d4b99`

Expected: clean PR audit before push, hosted verification, merge, and
`make ai-close-work-item TASK=conflict-successor-outcome-709-current-main`.
