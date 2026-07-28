---
author: Ray
title: "RFE-147 Transactional Work Item Closure Design"
description: Retry-safe branch cleanup and truthful multi-worktree readiness for ai-close-work-item.
keywords:
  - work-item
  - lifecycle
  - transaction
  - retry
  - worktree
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# RFE-147 Transactional Work Item Closure Design

## Status

Approved in conversation on 2026-07-28. Implementation remains unverified until
the owning Work Item completes its tests, archive, PR, Hosted CI, merge, closure,
and branch cleanup.

## Problem

`ai-close-work-item` currently has two coupled defects:

1. It deletes the local Work Item branch before remote deletion is proven. If
   remote deletion fails and the branch still exists, the command reports
   failure only after destroying the local branch identity required for a
   direct retry.
2. If another worktree owns the base branch, it synchronizes that worktree and
   detaches the invoking Work Item worktree. The result nevertheless always
   reports `ready_for_next_work_item`, even though the invoking worktree is not
   on the synchronized base.

The first defect occurred during PR #427 closure and required reconstruction of
the original branch at the PR Head SHA. The second occurred during the deep
performance Work Item and required manual stale-worktree cleanup. Both are
workflow defects because repeating the documented command can produce the same
failure.

## Goals

- Preserve a directly retryable local Work Item identity until remote branch
  absence is authoritative.
- Keep merged PR ownership, clean worktrees, fast-forward-only base
  synchronization, and remote absence fail closed.
- Separate lifecycle closure from invoking-worktree readiness.
- Recover the original checkout if final local cleanup fails after detaching.
- Prove multi-worktree behavior with real Git topology, not only a mocked
  command list.
- Align executable behavior, agent rules, English guidance, Japanese guidance,
  and the installed `ai-cockpit` skill.

## Non-goals

- Deleting or pruning unrelated worktrees.
- Retaining a local Work Item branch after successful closure.
- Replacing the GitHub PR adapter or introducing provider-specific transaction
  storage.
- Weakening remote absence checks when provider-side auto-deletion occurred.
- Changing archive, release, installation calibration, or unrelated lifecycle
  behavior.

## Considered approaches

### Reorder only

Delete the remote branch before the local branch and leave all other behavior
unchanged.

This preserves retry identity for the observed remote failure, but still
misreports detached worktrees and does not restore the checkout if local
deletion fails after detach. It is insufficient.

### Persistent transaction journal

Write a durable closure journal before every mutation and resume from its last
completed phase.

This provides general crash recovery, but adds a new persistent schema,
ownership, cleanup, and archive boundary for two deterministic Git mutations.
It also creates new stale-journal failure modes. The complexity is not justified
for RFE-147.

### Selected: prevalidated, retry-safe mutation

Resolve all stable facts first, preserve the local branch through remote
deletion, and make the final local deletion a recoverable boundary. Return a
structured state that distinguishes closure from next-task readiness.

This addresses both field failures without introducing a second lifecycle
store.

## Authority model

The closure command uses four authorities:

| Fact | Authority |
| --- | --- |
| Work Item completion | Valid archived Contract, Summary, Manifest/index chain, and no-active Cockpit Status |
| Branch/PR ownership | Current local branch plus merged PR head/base identity and PR Head SHA |
| Base readiness | Discovered remote default branch, fast-forward-only synchronization, clean base worktree, and local/remote SHA equality |
| Remote branch cleanup | `fetch --prune` plus `ls-remote --heads`; a delete request alone is never proof |

The local Work Item branch is retry identity, not proof of merge. The merged PR
authorizes deletion, but the local branch remains present until remote absence
is established.

## State model

Lifecycle completion and invoking-worktree readiness are separate:

| `state` | `repositoryState` | `nextWorkItemReady` | Meaning |
| --- | --- | --- | --- |
| `closed` | `ready_on_base` | `true` | The invoking worktree is clean, synchronized, and checked out on the base branch. |
| `closed` | `closed_but_current_worktree_detached` | `false` | Cleanup completed, but another verified worktree owns the base; the invoking worktree is detached. |

Failure raises an error and returns no closed state. A detached success includes
the verified base worktree path as the next-action location. Human-facing output
must explicitly say that the invoking worktree is not ready for another Work
Item.

`closed_but_current_worktree_detached` is not a weaker form of
`ready_on_base`. It is a truthful terminal closure state with an explicit
handoff to the base worktree.

## Ordered protocol

### Phase 1: read and bind

Before cleanup mutation:

1. Validate archived Contract/Summary evidence and no-active Status.
2. Require the invoking worktree to be on a non-base Work Item branch.
3. Require the invoking worktree to be clean.
4. Discover exactly one remote/default-branch pair.
5. Read the local Work Item branch tip.
6. Verify a merged PR whose head branch, base branch, merge timestamp, merge
   commit, and Head SHA match the closure target.
7. Discover whether the base branch is in the invoking worktree or another
   worktree.
8. If another worktree owns base, require that worktree to be clean.

No remote or local Work Item branch is deleted in this phase.

### Phase 2: establish base safety

1. If the invoking worktree owns neither base nor another base worktree exists,
   switch it to base.
2. Fetch and prune the discovered remote.
3. Fast-forward the base to the remote base.
4. Verify local base equals remote base.
5. Verify the selected base worktree is clean and still on base.

Switching to base is identity-preserving because the local Work Item ref still
exists. In the linked-worktree case, the invoking worktree remains on the Work
Item branch during this phase.

### Phase 3: establish remote absence

1. Request deletion of the exact remote Work Item branch.
2. Fetch with prune.
3. Require `ls-remote --heads` to prove the branch is absent.

If deletion fails or remains unverifiable, preserve the local ref. In the
linked-worktree case the invoking worktree is still on the Work Item branch. In
the normal case, switch the invoking worktree back from base to the Work Item
branch before reporting failure. If checkout restoration also fails, report
that distinct recovery failure while retaining the local ref. If the provider
already deleted the branch, verified absence is idempotent success.

### Phase 4: delete the local retry identity

For a normal single-worktree closure, delete the now-unchecked local Work Item
branch.

For a linked-base closure:

1. detach the invoking worktree at its current exact `HEAD`;
2. delete the local Work Item branch;
3. if deletion fails while the ref still exists, switch the invoking worktree
   back to that branch;
4. report a recovery-specific error, including whether restoration succeeded.

All remote and base postconditions are established before this boundary. A
retry after successful remote deletion remains legal because verified remote
absence is idempotent.

### Phase 5: classify the terminal state

For normal closure, verify the invoking worktree is clean, on base, and equal to
the remote base; return `ready_on_base`.

For linked-base closure, verify:

- the base worktree is clean, on base, and equal to the remote base;
- the invoking worktree is clean and detached;
- local and remote Work Item refs are absent.

Return `closed_but_current_worktree_detached`, `nextWorkItemReady: false`, and
the base worktree path. Do not remove or alter that worktree.

## Failure and retry semantics

| Failure boundary | Required retained state | Retry behavior |
| --- | --- | --- |
| Evidence, PR, Head SHA, clean-state, or base discovery | Original Work Item checkout and refs | Correct evidence and rerun |
| Fetch or fast-forward | Local Work Item ref remains | Correct base/worktree state and rerun |
| Remote delete with ref still present or unverifiable | Local Work Item ref remains; invoking checkout is retained or restored | Correct permissions/provider state and rerun |
| Remote delete request fails but ref is absent | Continue as idempotent success | No manual branch reconstruction |
| Detach succeeds but local delete fails | Restore Work Item checkout when ref exists | Correct local ref/worktree condition and rerun |
| Final invariant fails before local deletion | Local Work Item ref remains | Correct invariant and rerun |

The design does not claim process-crash atomicity between individual Git
commands. It guarantees deterministic retry identity for handled failures and
orders destructive mutations so that an earlier verified postcondition remains
safe on retry.

## Implementation boundaries

`scripts/ai_close_work_item.py` will:

- extend PR verification to bind the local branch tip to PR Head SHA;
- return structured readiness and base-worktree facts;
- move remote deletion before local deletion;
- isolate final detach/delete/restore behavior in a small helper;
- classify and render both success states without unconditional ready output.

`tests/test_work_item_lifecycle_closure.py` will:

- replace the old local-before-remote assertion with remote-before-local;
- assert no detach/local deletion on remote failure;
- cover already-absent retry;
- cover local-delete failure and checkout restoration;
- cover PR Head SHA mismatch before mutation;
- cover exact structured result and CLI output for both terminal states;
- create a real temporary repository, bare remote, merged Work Item branch, and
  linked base worktree to prove final Git state.

The authoritative English and Japanese lifecycle references, Cockpit guidance,
`AGENTS.md`, and the adopter rule template will describe the same ordering and
readiness distinction. After merge, the locally installed `ai-cockpit` skill
will be synchronized from this repository truth and checked so old unconditional
ready wording is not callable.

## Verification

Verification proceeds red first:

1. Add focused failing tests for each Contract scenario.
2. Confirm failures demonstrate the old local-before-remote ordering and
   detached-ready misclassification.
3. Implement the smallest cohesive transaction change.
4. Run focused lifecycle closure tests.
5. Run Contract, scope, guards, scenario coverage, documentation checks, and
   full quality.
6. Finish/archive, commit, run aggregate PR validation, push, open one PR, wait
   for all Hosted checks, merge, and run the corrected closure command.
7. Verify the Work Item branch is absent locally and remotely and `main` is
   clean/synchronized before starting RFE-151.

## Rollback

Before merge, revert this Work Item's code, test, and documentation diff.
After merge, a behavioral rollback requires a new corrective Work Item because
restoring local-before-remote deletion or unconditional detached readiness would
reintroduce a proven workflow defect.
