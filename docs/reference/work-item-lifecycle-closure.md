---
author: Ray
title: "Work Item Lifecycle Closure"
description: Fail-closed closure protocol for returning a repository to the next-task-ready state.
keywords:
  - ai-cockpit
  - work-item
  - lifecycle
  - closure
  - cleanup
---

# Work Item Lifecycle Closure

Closure means the Work Item lifecycle is complete, its local and remote work
branch identities are removed, and a clean synchronized base worktree is
verified. It is not equivalent to deleting a branch, and it does not imply
that the invoking worktree is ready when another worktree owns the base.

Run:

```sh
make ai-close-work-item TASK=<task>
```

The command requires the Work Item Contract and Summary to be archived, no
active Work Item evidence, a consistent no-active Cockpit Status, and a merged
PR whose head branch and Head SHA match the current local Work Item branch.

## Superseded predecessor evidence

A blocked predecessor does not become successful when a corrective successor
replaces it. Its Outcome remains red and its failed verification remains in the
archived Summary. Archive and closure may accept that failed Summary only when
all reported Summary issues are missing or failed required-verification items
and a sibling `transition=superseded` receipt exactly binds the blocked Outcome,
predecessor identity, successor Work Item/branch/base, Outcome digest,
repository Issue, human authority, and reason.

A missing, malformed, quarantined, mismatched, non-blocked, stale-digest, or
foreign receipt remains fail closed. A valid receipt also cannot mask a
Contract error or any unrelated Summary error. This exception changes only the
archived-evidence eligibility check; the merged PR, exact Head SHA, clean
worktree, fast-forward base synchronization, closure receipt, remote absence,
and local branch cleanup checks below remain mandatory and unchanged.

Its ordered protocol is:

```text
verify evidence, local Work Item Head, and merged PR Head SHA
→ synchronize and verify the discovered base worktree
→ request remote Work Item branch deletion
→ fetch/prune and prove remote Work Item branch absence
→ detach only when another worktree owns base
→ delete the local Work Item branch
→ restore the Work Item checkout if linked local deletion fails
→ report ready_on_base or closed_but_current_worktree_detached
```

The command stops at the first unverified failure. It establishes base safety,
then proves remote absence before deleting the local retry identity. If remote
deletion fails or cannot be verified, the local branch is retained and the
invoking Work Item checkout is retained or restored for direct retry. If
GitHub or another platform has already deleted the branch, the redundant
delete request may return non-zero; after `fetch --prune`, a verified absent
remote ref is the idempotent success state. A branch that still exists, or a
remote state that cannot be verified, remains fail closed. Squash and rebase
PRs are supported because the merged PR, rather than local ancestry,
authorizes deletion of the source branch.

`ready_on_base` means the invoking worktree is clean, synchronized, and checked
out on the discovered base; it is ready for the next Work Item.
`closed_but_current_worktree_detached` means closure completed while another
verified worktree owns the base. The invoking worktree is deliberately
detached and is not ready for the next Work Item. Continue from the base
worktree path printed by the command. Closure never removes that worktree.

`make ai-finish TASK=<task>` is an archive milestone, not lifecycle closure. Its successful output explicitly directs the operator to push the Work Item branch, open and merge the PR, and then run `ai-close-work-item`. Historical local branches or detached worktrees outside the current Work Item are not deleted automatically because their ownership cannot be established safely from a branch name alone; audit and remove them only with explicit operator authorization.

## Exceptional stacked-PR executor

Normally, run closure from the merged Work Item branch. If a corrective child PR
was merged into an active parent Work Item branch and the child worktree still
contains an older closure implementation, run the current parent-branch policy
against that exact registered child worktree:

```sh
make ai-close-work-item TASK=<child-task> ARGS="--worktree /absolute/path/to/child-worktree"
```

This is a narrow recovery command, not a general branch-deletion interface. It
accepts only an existing Git-worktree root registered in the same repository.
`ARGS` is forwarded unchanged by the Makefile. Before any provider query,
receipt write, base switch, or branch mutation, the CLI requires the selected
worktree to be checked out on exactly `codex/<child-task>`. A task/worktree
mismatch stops fail closed; it cannot create a receipt for one Work Item while
using another Work Item's PR or branch. Git operations are scoped to that child
checkout; provider `gh` discovery explicitly names that selected child branch,
so it cannot infer the current policy checkout's PR.
All normal merged-PR, Head-SHA, parent-retention, clean-worktree, receipt, and
remote-absence checks remain mandatory.

## Historical stacked-PR chain receipt

An archive is immutable. If a corrective Work Item was already archived without
an explicit predecessor source, the aggregate PR check does not permit editing
that archive or using a task-name exception. A narrowly scoped append-only
receipt under `.ai/work-items/recovery-receipts/` may instead bind the exact
consecutive archive prefix: each Work Item ID, Contract and Summary paths,
SHA-256 digests, archive sequence, base commit, and the PR merge-base.

The checker recomputes every binding and each base-commit ancestry edge. It
accepts only the receipt's exact compatible prefix; subsequent entries must
still meet the ordinary adjacent-source recovery rule.

An already merged child Work Item may also appear after that immutable prefix,
but only when repository history proves all of the following: its canonical
Start Receipt remains valid; its Contract and Summary were added together in
one immutable archive commit; and that commit entered the checked parent-PR
history through the second parent of a two-parent merge after the parent PR
base. Reachability from `HEAD`, a task name, a local Closure Receipt, or a
direct addition to the parent branch is not enough. This permits a real child
PR without letting it hide independent Work Items in the parent PR.

A missing, reordered, incompatible, unmerged, or unrelated entry leaves the
default one-new-Work-Item-per-PR rule in force.

Archived evidence has one immutable root: `archive-manifest.json` is generated only after the Contract and Summary are frozen, and records their SHA-256 digests. The Summary does not hash itself, and generated `current_status.md` is excluded from this chain. The archive index records the manifest path and digest; records predating this protocol remain readable as legacy evidence.

## Same-Work-Item post-archive PR recovery

For a failed post-archive `check-ai-pr` coverage or archive-evidence gate,
`make ai-open-post-archive-recovery` is the only same-Work-Item repair route.
It starts only from a clean committed candidate and writes one append-only
receipt under `.ai/work-items/recovery-receipts/`. The receipt binds the exact
archived Contract, Summary, Outcome, and manifest digests, the PR base, the
failed aggregate command/output digest, the repository Issue, human authority,
and a finite list of recovery paths. `check-ai-pr` independently recomputes
each binding and grants ownership only to those paths. A stale, forged,
incomplete, different-base, archive-mutating, or out-of-scope receipt remains
unowned and fails the PR audit. It is never a merge, release, branch deletion,
or closure authorization.

For a hosted-only GitHub Actions aggregate coverage failure, the local
`check-ai-pr` need not fail. Supply all five `HOSTED_*` arguments to the same
command. It obtains the exact provider run, `template-smoke` job, and log using
authenticated GitHub API access, binds their repository/PR/Head/run/job/log
facts and parsed actual/required coverage to the receipt, and rechecks them in
`check-ai-pr`. A pasted log, missing credentials, stale or rerun provider
state, mismatched Head or PR, a non-coverage failure, archive mutation, or a
path outside `RECOVERY_PATHS` remains fail-closed. This route is neither a
provider mutation nor authorization to merge, release, close, or delete.

The repository's remote name and default branch are discovered from Git's remote HEAD. Adopter projects therefore do not need to use `origin/main`.

## Exceptional provider merge-state recovery

`ai-close-work-item` has no fallback for an open, closed, skipped, or otherwise
incomplete provider PR. It continues to require the provider's authoritative
`MERGED` state, matching branch and Head SHA, merge commit, and merge timestamp.
That normal rule prevents ordinary open PRs from being cleaned up.

If a provider has demonstrably performed a partial transaction — for example,
an exact GitHub-verified signed two-parent merge commit is on the base but the
PR API remains `OPEN` with no normal merge facts — use the separate, read-only
assessment boundary:

```sh
make ai-assess-provider-merge-state-recovery \
  ARGS="--evidence provider-anomaly.json --human-confirmed --output target/provider-recovery.md"
```

The evidence must bind the original PR number, URL, branch and Head SHA; the
observed base SHA; the exact merge parents `[base, head]`; GitHub signature
verification; base reachability; and each required hosted job succeeding on
that Head. The assessment emits a recovery-specific receipt which explicitly
records the provider's inconsistent state and unavailable normal merge facts.
It never deletes a branch, changes the PR, or turns the PR into `MERGED`.
A later recovery action needs a separate explicit human decision and must keep
the receipt as audit evidence.
