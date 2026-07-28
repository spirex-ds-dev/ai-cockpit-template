---
author: Ray
title: "RFE-147 Transactional Work Item Closure Implementation Plan"
description: Test-driven plan for retry-safe branch cleanup and truthful multi-worktree readiness.
keywords:
  - work-item
  - lifecycle
  - transaction
  - worktree
  - tdd
---

# RFE-147 Transactional Work Item Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `ai-close-work-item` preserve retry identity until remote absence is proven and report linked-worktree closure without falsely claiming the invoking worktree is ready.

**Architecture:** Keep the existing single closure command and Git runner abstraction. Add exact PR Head SHA binding, reorder remote deletion before local deletion, wrap linked-worktree detach/local-delete in checkout recovery, and return separate lifecycle/readiness facts. Prove the result with focused command-order tests and a real bare-remote/linked-worktree topology.

**Tech Stack:** Python 3 standard library, Git CLI, pytest, GNU Make, JSON Work Item evidence, Markdown documentation.

## Global Constraints

- Preserve the one Work Item, branch, PR, archive, merge, closure, and branch cleanup lifecycle.
- Retain merged PR ownership and remote branch absence as mandatory evidence.
- Accept provider-side auto-deletion only after `fetch --prune` and `ls-remote --heads` prove absence.
- Leave unrelated and stale worktrees untouched.
- Never report the invoking worktree next-task-ready while it is detached.
- Use red-green-refactor TDD for every behavioral change.
- Do not start RFE-151 until this Work Item completes PR, Hosted CI, merge, closure, branch deletion, and clean synchronized `main`.

## File map

| File | Responsibility |
| --- | --- |
| `scripts/ai_close_work_item.py` | Bind closure identity, order branch mutations, recover checkout, classify terminal state, and render truthful CLI output. |
| `tests/test_work_item_lifecycle_closure.py` | Unit command-order, failure, recovery, structured-state, CLI-output, and real Git topology regressions. |
| `docs/reference/work-item-lifecycle-closure.md` | Authoritative English closure protocol. |
| `docs/reference/work-item-lifecycle-closure.ja.md` | Semantically aligned Japanese closure protocol. |
| `.ai/cockpit/README.md` | Maintainer/adopter English workflow summary. |
| `.ai/cockpit/README.ja.md` | Maintainer/adopter Japanese workflow summary. |
| `AGENTS.md` | Repository agent lifecycle rule. |
| `templates/agents/AI_COCKPIT_RULES.md` | Installed adopter agent lifecycle rule. |
| `docs/reference/documentation-context-registry.json` | Classify this plan as current instruction during execution. |
| `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md` | Record RFE-147 implementation and lifecycle evidence. |
| Active Contract/Summary and generated Status | Maintain instruction → plan → implementation → acceptance evidence. |

---

### Task 1: Bind the local Work Item tip to the merged PR Head SHA

**Files:**
- Modify: `tests/test_work_item_lifecycle_closure.py`
- Modify: `scripts/ai_close_work_item.py`

**Interfaces:**
- Consumes: `Runner`, `CommandResult`, current branch name, discovered base branch.
- Produces: `_verify_pr(runner: Runner, branch: str, base_branch: str, branch_commit: str) -> dict[str, object]`.
- Produces: an early fail-closed check comparing `headRefOid` with `git rev-parse codex/example` in the focused fixture.

- [ ] **Step 1: Extend the fake Git model with a stable branch tip**

Add to `FakeGit.__init__`:

```python
self.work_branch_commit = "work123"
```

Add before the existing base `rev-parse` branch:

```python
if normalized == ("rev-parse", "codex/example"):
    return closure.CommandResult(0, f"{self.work_branch_commit}\n")
```

Update `prepare()` so its PR stub accepts `_branch_commit`:

```python
lambda _runner, _branch, _base, _branch_commit: {
    "url": "https://example.test/pr/1",
    "headRefOid": "work123",
}
```

- [ ] **Step 2: Write the failing PR Head SHA regressions**

Add:

```python
def test_verify_pr_requires_exact_local_head_sha() -> None:
    payload = {
        "state": "MERGED",
        "headRefName": "codex/example",
        "headRefOid": "other123",
        "baseRefName": "main",
        "mergedAt": "2026-07-28T00:00:00Z",
        "mergeCommit": {"oid": "merge123"},
        "url": "https://example.test/pr/1",
    }

    def runner(_args, _check):
        return closure.CommandResult(0, __import__("json").dumps(payload))

    with pytest.raises(RuntimeError, match="Head SHA"):
        closure._verify_pr(runner, "codex/example", "main", "work123")
```

Update every existing direct `_verify_pr` call to pass `"work123"`. Extend the
valid fixture with `"headRefOid": "work123"`.

- [ ] **Step 3: Run the focused red test**

Run:

```bash
.venv/bin/pytest -q \
  tests/test_work_item_lifecycle_closure.py::test_verify_pr_requires_exact_local_head_sha
```

Expected: FAIL because `_verify_pr` has no `branch_commit` parameter and does
not request or validate `headRefOid`.

- [ ] **Step 4: Implement exact Head SHA binding**

Change the signature:

```python
def _verify_pr(
    runner: Runner,
    branch: str,
    base_branch: str,
    branch_commit: str,
) -> dict[str, object]:
```

Change the adapter query to:

```python
"state,headRefName,headRefOid,baseRefName,mergedAt,mergeCommit,url",
```

Add after head branch validation:

```python
if data.get("headRefOid") != branch_commit:
    raise RuntimeError("pull request Head SHA does not match the local Work Item branch")
```

In `close_work_item`, resolve and validate the local ref before PR verification:

```python
work_commit = runner(["rev-parse", work_branch], True).stdout.strip()
if not work_commit:
    raise RuntimeError("cannot resolve the local Work Item branch commit")
pr = _verify_pr(runner, work_branch, base_branch, work_commit)
```

- [ ] **Step 5: Run all PR identity tests**

Run:

```bash
.venv/bin/pytest -q tests/test_work_item_lifecycle_closure.py \
  -k "verify_pr or branch_mapping or head_sha"
```

Expected: PASS.

- [ ] **Step 6: Commit the identity boundary**

```bash
git add scripts/ai_close_work_item.py tests/test_work_item_lifecycle_closure.py
git commit -m "fix: bind closure to pull request head"
```

---

### Task 2: Reorder deletion and recover linked-worktree checkout

**Files:**
- Modify: `tests/test_work_item_lifecycle_closure.py`
- Modify: `scripts/ai_close_work_item.py`

**Interfaces:**
- Consumes: `_delete_remote_branch`, the verified Work Item branch, and whether another worktree owns base.
- Produces: `_delete_local_branch(runner: Runner, branch: str, *, detach_required: bool) -> None`.
- Guarantees: remote absence is proven before local branch deletion; failed linked deletion restores checkout when the ref remains.

- [ ] **Step 1: Replace the old success-order expectation with the required order**

Rename the test to
`test_success_proves_remote_absence_before_local_branch_deletion` and assert:

```python
remote_delete = fake.commands.index(
    ("push", "origin", "--delete", "codex/example")
)
remote_absence = fake.commands.index(
    ("ls-remote", "--exit-code", "--heads", "origin", "codex/example")
)
local_delete = fake.commands.index(("branch", "-D", "codex/example"))

assert remote_delete < remote_absence < local_delete
```

- [ ] **Step 2: Strengthen the remote-failure regression**

Replace the old assertion that accepted local deletion with:

```python
assert ("branch", "-D", "codex/example") not in fake.commands
assert ("switch", "--detach", "HEAD") not in fake.commands
assert fake.current_branch == "codex/example"
```

This requires normal single-worktree failure to restore the checkout from
`main` to `codex/example`; linked-worktree failure never leaves the Work Item
checkout.

- [ ] **Step 3: Add a red detach rollback regression**

Add:

```python
def test_linked_worktree_local_delete_failure_restores_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeGit(fail_on=("branch", "-D"))
    fake.base_worktree_path = "/tmp/base-worktree"
    prepare(monkeypatch, fake)

    with pytest.raises(RuntimeError, match="checkout restored"):
        closure.close_work_item("example", fake)

    detach = fake.commands.index(("switch", "--detach", "HEAD"))
    restore = fake.commands.index(("switch", "codex/example"))
    assert detach < restore
    assert fake.current_branch == "codex/example"
```

Teach `FakeGit` to process a generic branch switch:

```python
if normalized == ("switch", "codex/example"):
    self.current_branch = "codex/example"
    return closure.CommandResult(0, "")
```

- [ ] **Step 4: Run the three red transaction tests**

Run:

```bash
.venv/bin/pytest -q \
  tests/test_work_item_lifecycle_closure.py::test_success_proves_remote_absence_before_local_branch_deletion \
  tests/test_work_item_lifecycle_closure.py::test_remote_deletion_failure_does_not_report_closed \
  tests/test_work_item_lifecycle_closure.py::test_linked_worktree_local_delete_failure_restores_checkout
```

Expected: all three FAIL against local-before-remote deletion and missing
checkout recovery.

- [ ] **Step 5: Implement recoverable local deletion**

Add:

```python
def _delete_local_branch(
    runner: Runner,
    branch: str,
    *,
    detach_required: bool,
) -> None:
    if not detach_required:
        runner(["branch", "-D", branch], True)
        return

    runner(["switch", "--detach", "HEAD"], True)
    try:
        runner(["branch", "-D", branch], True)
    except RuntimeError as exc:
        restored = runner(["switch", branch], False)
        if restored.returncode != 0:
            raise RuntimeError(
                "local Work Item branch deletion failed after detach; "
                "checkout restoration also failed"
            ) from exc
        raise RuntimeError(
            "local Work Item branch deletion failed after detach; "
            "the Work Item checkout was restored for retry"
        ) from exc
```

In `close_work_item`, complete clean/base/equality checks before destructive
cleanup. Wrap remote cleanup so normal single-worktree failure restores the
Work Item checkout:

```python
try:
    _delete_remote_branch(runner, remote, work_branch)
except RuntimeError as exc:
    if base_path is None:
        restored = runner(["switch", work_branch], False)
        if restored.returncode != 0:
            raise RuntimeError(
                f"{exc}; local Work Item branch remains, but checkout "
                "restoration also failed"
            ) from exc
        raise RuntimeError(
            f"{exc}; the Work Item checkout was restored for retry"
        ) from exc
    raise

_delete_local_branch(
    runner,
    work_branch,
    detach_required=base_path is not None,
)
```

Remove the old unconditional detach and local-before-remote sequence.

- [ ] **Step 6: Run transaction and existing failure tests**

Run:

```bash
.venv/bin/pytest -q tests/test_work_item_lifecycle_closure.py \
  -k "deletion or delete or fast_forward or dirty or unmerged or mismatch or occupancy"
```

Expected: PASS, including the already-absent remote race.

- [ ] **Step 7: Commit the transaction boundary**

```bash
git add scripts/ai_close_work_item.py tests/test_work_item_lifecycle_closure.py
git commit -m "fix: make closure branch deletion retry safe"
```

---

### Task 3: Return and render truthful terminal states

**Files:**
- Modify: `tests/test_work_item_lifecycle_closure.py`
- Modify: `scripts/ai_close_work_item.py`

**Interfaces:**
- Consumes: the verified `base_path`, synchronized base commit, and completed local/remote cleanup.
- Produces: `close_work_item(...) -> dict[str, object]`.
- Produces result keys: `state`, `repositoryState`, `nextWorkItemReady`, `baseWorktree`, `baseBranch`, and `baseCommit`.

- [ ] **Step 1: Add red structured-state assertions**

In normal success:

```python
assert result["repositoryState"] == "ready_on_base"
assert result["nextWorkItemReady"] is True
assert result["baseWorktree"] == ""
```

In linked-base success:

```python
assert result["repositoryState"] == "closed_but_current_worktree_detached"
assert result["nextWorkItemReady"] is False
assert result["baseWorktree"] == "/tmp/base-worktree"
assert fake.current_branch == ""
```

- [ ] **Step 2: Add red CLI output tests**

Add:

```python
def test_main_reports_ready_only_for_ready_on_base(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        closure,
        "parse_args",
        lambda: type("Args", (), {"task": "example"})(),
    )
    monkeypatch.setattr(
        closure,
        "close_work_item",
        lambda *_args: {
            "pullRequest": "https://example.test/pr/1",
            "workBranch": "codex/example",
            "baseRemote": "origin",
            "baseBranch": "main",
            "baseWorktree": "",
            "repositoryState": "ready_on_base",
            "nextWorkItemReady": True,
        },
    )

    assert closure.main() == 0
    assert "Repository state: ready for next Work Item" in capsys.readouterr().out
```

Add a second test with:

```python
"baseWorktree": "/tmp/base-worktree",
"repositoryState": "closed_but_current_worktree_detached",
"nextWorkItemReady": False,
```

and assert:

```python
assert "Current worktree: detached; not ready for the next Work Item" in output
assert "Continue from synchronized base worktree: /tmp/base-worktree" in output
assert "Repository state: ready for next Work Item" not in output
```

- [ ] **Step 3: Run the state tests red**

Run:

```bash
.venv/bin/pytest -q tests/test_work_item_lifecycle_closure.py \
  -k "ready_on_base or current_worktree or base_branch_worktree_occupancy"
```

Expected: FAIL because the result and CLI currently expose one unconditional
ready state.

- [ ] **Step 4: Implement the structured result**

Change the return annotation:

```python
def close_work_item(task: str, runner: Runner = _run_git) -> dict[str, object]:
```

After successful cleanup:

```python
linked_base = base_path is not None
repository_state = (
    "closed_but_current_worktree_detached"
    if linked_base
    else "ready_on_base"
)
```

Return:

```python
"state": "closed",
"repositoryState": repository_state,
"nextWorkItemReady": not linked_base,
"baseWorktree": base_path or "",
```

In `main()`, retain the existing ready line only when
`nextWorkItemReady is True`. Otherwise print:

```python
print("Current worktree: detached; not ready for the next Work Item")
print(f"Continue from synchronized base worktree: {result['baseWorktree']}")
```

- [ ] **Step 5: Run all lifecycle closure unit tests**

Run:

```bash
.venv/bin/pytest -q tests/test_work_item_lifecycle_closure.py
```

Expected: PASS.

- [ ] **Step 6: Commit state reporting**

```bash
git add scripts/ai_close_work_item.py tests/test_work_item_lifecycle_closure.py
git commit -m "fix: report linked worktree closure truthfully"
```

---

### Task 4: Prove the behavior with a real linked-worktree repository

**Files:**
- Modify: `tests/test_work_item_lifecycle_closure.py`

**Interfaces:**
- Consumes: public `close_work_item`, a real Git runner rooted at the invoking Work Item worktree, and monkeypatched archive/PR evidence adapters.
- Produces: `test_real_linked_worktree_closure_is_closed_but_not_ready`.

- [ ] **Step 1: Add real Git helpers**

Add imports:

```python
import json
import os
import subprocess
from pathlib import Path
```

Add:

```python
def run_command(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )


def repository_runner(cwd: Path) -> closure.Runner:
    def run(args, check=False):
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        converted = closure.CommandResult(
            result.returncode,
            result.stdout,
            result.stderr,
        )
        if check and converted.returncode != 0:
            raise RuntimeError(converted.stderr.strip() or "git command failed")
        return converted

    return run
```

- [ ] **Step 2: Write the real topology regression**

Create:

```python
def test_real_linked_worktree_closure_is_closed_but_not_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    remote = tmp_path / "remote.git"
    repository = tmp_path / "repository"
    base_worktree = tmp_path / "base-worktree"

    run_command(tmp_path, "git", "init", "--bare", str(remote))
    run_command(tmp_path, "git", "clone", str(remote), str(repository))
    run_command(repository, "git", "config", "user.name", "Test User")
    run_command(repository, "git", "config", "user.email", "test@example.test")
    run_command(repository, "git", "switch", "-c", "main")
    (repository / "tracked.txt").write_text("base\n", encoding="utf-8")
    run_command(repository, "git", "add", "tracked.txt")
    run_command(repository, "git", "commit", "-m", "base")
    run_command(repository, "git", "push", "-u", "origin", "main")
    run_command(remote, "git", "symbolic-ref", "HEAD", "refs/heads/main")

    run_command(repository, "git", "switch", "-c", "codex/example")
    (repository / "tracked.txt").write_text("work\n", encoding="utf-8")
    run_command(repository, "git", "commit", "-am", "work")
    work_commit = run_command(repository, "git", "rev-parse", "HEAD").stdout.strip()
    run_command(repository, "git", "push", "-u", "origin", "codex/example")
    run_command(repository, "git", "worktree", "add", str(base_worktree), "main")
    run_command(base_worktree, "git", "merge", "--no-ff", "codex/example", "-m", "merge")
    run_command(base_worktree, "git", "push", "origin", "main")

    monkeypatch.setattr(
        closure,
        "_verify_archived_evidence",
        lambda _task: closure.PROJECT_ROOT
        / ".ai/work-items/archive/2026/example.contract.json",
    )
    monkeypatch.setattr(
        closure,
        "_verify_pr",
        lambda _runner, _branch, _base, _head: {
            "url": "https://example.test/pr/1",
            "headRefOid": work_commit,
        },
    )

    result = closure.close_work_item("example", repository_runner(repository))

    assert result["repositoryState"] == "closed_but_current_worktree_detached"
    assert result["nextWorkItemReady"] is False
    assert run_command(repository, "git", "branch", "--show-current").stdout.strip() == ""
    assert run_command(base_worktree, "git", "branch", "--show-current").stdout.strip() == "main"
    assert (
        run_command(base_worktree, "git", "rev-parse", "main").stdout
        == run_command(base_worktree, "git", "rev-parse", "origin/main").stdout
    )
    local_branches = run_command(repository, "git", "branch", "--format=%(refname:short)").stdout
    assert "codex/example" not in local_branches.splitlines()
    remote_heads = run_command(repository, "git", "ls-remote", "--heads", "origin", "codex/example").stdout
    assert remote_heads == ""
```

- [ ] **Step 3: Run the integration regression**

Run:

```bash
.venv/bin/pytest -q \
  tests/test_work_item_lifecycle_closure.py::test_real_linked_worktree_closure_is_closed_but_not_ready
```

Expected: PASS only after Tasks 1–3. If Git rejects setup, correct the fixture
without weakening final branch/ref assertions.

- [ ] **Step 4: Run the whole focused file with coverage**

Run:

```bash
.venv/bin/pytest -q tests/test_work_item_lifecycle_closure.py \
  --cov=ai_close_work_item --cov-report=term-missing
```

Expected: PASS and all newly added branches appear in the report.

- [ ] **Step 5: Commit real-topology evidence**

```bash
git add tests/test_work_item_lifecycle_closure.py
git commit -m "test: prove linked worktree closure state"
```

---

### Task 5: Align repository rules and bilingual documentation

**Files:**
- Modify: `docs/reference/work-item-lifecycle-closure.md`
- Modify: `docs/reference/work-item-lifecycle-closure.ja.md`
- Modify: `.ai/cockpit/README.md`
- Modify: `.ai/cockpit/README.ja.md`
- Modify: `AGENTS.md`
- Modify: `templates/agents/AI_COCKPIT_RULES.md`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`

**Interfaces:**
- Consumes: the exact states and ordering implemented in Tasks 1–4.
- Produces: one authoritative English protocol, semantically aligned Japanese guidance, and matching agent rules.

- [ ] **Step 1: Update the authoritative English protocol**

Replace the lifecycle sequence with:

```text
verify evidence, local Work Item Head, and merged PR Head SHA
→ synchronize and verify the discovered base worktree
→ request remote Work Item branch deletion
→ fetch/prune and prove remote branch absence
→ detach only when another worktree owns base
→ delete the local Work Item branch
→ restore the Work Item checkout if linked local deletion fails
→ report ready_on_base or closed_but_current_worktree_detached
```

State explicitly that remote failure preserves local retry identity and that a
detached terminal state is closed but not ready in the invoking worktree.

- [ ] **Step 2: Apply the same semantics in Japanese**

Use the exact state names and explain:

```text
ready_on_base
closed_but_current_worktree_detached
```

The Japanese text must say that the second state requires continuing from the
reported synchronized base worktree and must not be read as next-task-ready in
the invoking worktree.

- [ ] **Step 3: Update Cockpit and agent rules**

In both Cockpit READMEs, replace local-before-remote wording and unconditional
ready claims. In `AGENTS.md` and `templates/agents/AI_COCKPIT_RULES.md`, require:

```text
Remote absence must be proven before deleting the local retry identity.
A closed-but-detached invoking worktree is not ready for the next Work Item;
continue from the reported synchronized base worktree.
```

- [ ] **Step 4: Record RFE-147 closure evidence in the comprehensive plan**

Update the existing RFE-147 entries with:

- selected transaction ordering;
- PR Head SHA binding;
- detach rollback;
- real linked-worktree regression;
- distinct terminal states;
- final PR, Hosted run, merge commit, and closure evidence when available.

Do not mark the issue fully closed before the external lifecycle is complete.

- [ ] **Step 5: Run documentation and template checks**

Run:

```bash
make check-docs-metadata
make check-ai-system-invariants
.venv/bin/pytest -q \
  tests/test_installer.py::test_installed_distribution_contains_adoption_files \
  tests/test_work_item_lifecycle_closure.py
```

Expected: PASS.

- [ ] **Step 6: Commit documentation alignment**

```bash
git add \
  AGENTS.md \
  templates/agents/AI_COCKPIT_RULES.md \
  .ai/cockpit/README.md \
  .ai/cockpit/README.ja.md \
  docs/reference/work-item-lifecycle-closure.md \
  docs/reference/work-item-lifecycle-closure.ja.md \
  docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md
git commit -m "docs: align transactional closure guidance"
```

---

### Task 6: Complete traceability, verification, and lifecycle closure

**Files:**
- Modify: `.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.contract.json`
- Modify: `.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.summary.json`
- Modify/generated: `.ai/cockpit/current_status.md`
- Generate/archive: `.ai/work-items/archive/2026/rfe147-transactional-work-item-closure-20260728.*`
- Modify/generated: `.ai/work-items/archive/index.json`

**Interfaces:**
- Consumes: all implementation, tests, documentation, and verification output.
- Produces: six verified Contract scenarios, complete Summary evidence, immutable archive pair/manifest, one PR, Hosted success, merged commit, corrected closure output, and clean synchronized `main`.

- [ ] **Step 1: Mark each scenario only with exact test evidence**

Change each `scenarioCoverage.status` from `unverified` to `verified` only after
its named test passes. Use exact node IDs, including:

```text
tests/test_work_item_lifecycle_closure.py::test_remote_deletion_failure_does_not_report_closed
tests/test_work_item_lifecycle_closure.py::test_remote_deletion_race_is_accepted_when_postcondition_is_absent
tests/test_work_item_lifecycle_closure.py::test_real_linked_worktree_closure_is_closed_but_not_ready
tests/test_work_item_lifecycle_closure.py::test_linked_worktree_local_delete_failure_restores_checkout
tests/test_work_item_lifecycle_closure.py::test_success_proves_remote_absence_before_local_branch_deletion
tests/test_work_item_lifecycle_closure.py::test_verify_pr_requires_exact_local_head_sha
```

- [ ] **Step 2: Complete the Summary bidirectionally**

Record every changed file or an explicit no-change reason, all commands and
results, user corrections, RFE-147 observations/resolution, residual risks,
guideline compliance, boundary checks, Intent Alignment, and documentation
alignment. Remove skeleton text and do not mark Hosted/PR/merge evidence as
passed before it exists.

- [ ] **Step 3: Record the before-edit checkpoint**

Run:

```bash
make ai-checkpoint \
  CONTRACT=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.contract.json \
  SUMMARY=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.summary.json \
  STAGE=before_edit
```

Expected: PASS with checkpoint evidence appended to the active Summary.

- [ ] **Step 4: Run focused and governance checks**

Run:

```bash
.venv/bin/pytest -q tests/test_work_item_lifecycle_closure.py
make check-ai-contract CONTRACT=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.contract.json
make check-ai-scope CONTRACT=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.contract.json
make check-ai-guards CONTRACT=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.contract.json
make check-ai-agent-risk CONTRACT=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.contract.json SUMMARY=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.summary.json
make check-ai-scenario-coverage CONTRACT=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.contract.json SUMMARY=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.summary.json
```

Expected: PASS.

- [ ] **Step 5: Run full quality**

Run:

```bash
make quality
```

Expected: every fast/heavy gate PASS, project tests pass, coverage is at least
the repository executable threshold, and the quality summary points to the
outer session.

- [ ] **Step 6: Record the before-finish checkpoint and finish**

Run:

```bash
make ai-checkpoint \
  CONTRACT=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.contract.json \
  SUMMARY=.ai/work-items/active/rfe147-transactional-work-item-closure-20260728.summary.json \
  STAGE=before_finish

make ai-finish TASK=rfe147-transactional-work-item-closure-20260728
```

Expected: immutable archive evidence generated and Cockpit Status changed to
`no_active_work_item`.

- [ ] **Step 7: Commit archive and validate the complete PR diff**

Run:

```bash
git add -A
git commit -m "fix: close RFE-147 transactionally"
make check-ai-pr AI_BASE_COMMIT=34590a2ee75c05eee17e250509ff47b96f83da27
```

Expected: exactly one Work Item owns the complete diff and aggregate validation
passes.

- [ ] **Step 8: Push and create one PR without deleting the branch**

Run with the authorized GitHub account:

```bash
git push -u origin codex/rfe147-transactional-work-item-closure-20260728
gh pr create \
  --base main \
  --head codex/rfe147-transactional-work-item-closure-20260728 \
  --title "Fix transactional Work Item closure" \
  --body "## Summary
- preserve retry identity until remote branch absence is proven
- distinguish ready-on-base from closed-but-detached worktrees
- add unit and real linked-worktree regressions

## Verification
- make quality
- make check-ai-pr AI_BASE_COMMIT=34590a2ee75c05eee17e250509ff47b96f83da27"
```

Do not enable provider-side branch auto-deletion.

- [ ] **Step 9: Wait for Hosted CI and merge**

Require every required Hosted check to succeed on the exact PR Head SHA.
Inspect failures before rerunning. Merge the PR and record the authoritative
merge commit in the plan/Summary-derived external report; do not edit immutable
archive evidence.

- [ ] **Step 10: Run the corrected closure and verify cleanup**

Run:

```bash
make ai-close-work-item TASK=rfe147-transactional-work-item-closure-20260728
git status --short --branch
git branch --list codex/rfe147-transactional-work-item-closure-20260728
git ls-remote --heads origin codex/rfe147-transactional-work-item-closure-20260728
git rev-parse main
git rev-parse origin/main
```

Expected:

- lifecycle reports `closed`;
- local and remote Work Item branch queries are empty;
- invoking repository reports `ready_on_base`;
- worktree is clean;
- local `main` equals `origin/main`.

- [ ] **Step 11: Synchronize the installed skill from merged truth**

Update the installed `ai-cockpit` skill lifecycle wording so it requires remote
absence before local retry-identity deletion and rejects detached next-task
readiness. Verify:

```bash
installed_skill_file="$(
  find "${CODEX_HOME:-${HOME}/.codex}/skills" \
    -path '*/ai-cockpit/SKILL.md' -print -quit
)"
test -n "$installed_skill_file"
rg -n "remote absence|closed-but-detached|next Work Item" \
  "$installed_skill_file"
```

The installed skill must contain the merged semantics and no old unconditional
ready instruction.

- [ ] **Step 12: Advance only after final audit**

Confirm the Contract acceptance items, six scenarios, changed-file mapping,
archive, PR, Hosted checks, merge, closure output, skill synchronization, branch
absence, and synchronized clean base. Then mark RFE-147 complete in the parent
execution plan and start RFE-151 from the latest `origin/main`.
