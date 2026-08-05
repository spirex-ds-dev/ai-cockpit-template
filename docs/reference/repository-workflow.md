---
author: Ray
title: "Repository Workflow"
description: Repository-role-aware Work Item, branch, and pull or merge request workflow.
keywords:
  - ai-cockpit
  - work-item
  - branch
  - pull-request
  - adopter-project
---

# Repository Workflow
AI Cockpit uses one Work Item, one dedicated work branch, and one pull or merge request as its default review unit.
## Template repository
Template maintenance uses the template repository's protected default branch:

```text
latest origin/main → Work Item branch → ai-start + Start Receipt → one PR → merge → cleanup
```

The complete closure order is:

```text
latest remote base → dedicated Work Item branch → finish/archive → push → PR → merge → ai-close-work-item → synchronized clean base
```

Do not merge the Work Item branch into local `main` before opening or merging the PR. That makes local `main` appear ahead of `origin/main` and bypasses the review unit. Do not delete the Work Item branch as part of PR merge before running `ai-close-work-item`; closure needs the merged branch identity to verify ownership before it synchronizes the base and removes both branch copies.

### Pre-finish hosted measurement

The normal archive-before-push order remains authoritative. A Work Item may
use one narrower stage only when its active Contract explicitly requires
hosted evidence that cannot be produced from an unpublished commit:

```text
implement and verify locally → authorized local snapshot commit
  → ai-prepare-hosted-verification-snapshot → push exact branch for measurement
  → record hosted evidence in active Summary → canonical finish/archive and review
```

`make ai-prepare-hosted-verification-snapshot CONTRACT=<active-contract>`
runs local quality and writes a source-bound receipt. It performs no Git or
provider mutation. A valid receipt identifies a push of the exact committed
dedicated branch for hosted measurement as the only eligible next action but
provides no human authorization; it never permits a PR, merge,
release, archive mutation, closure, or deletion. Those actions remain blocked
until hosted evidence is recorded and the Work Item completes the canonical
Finish, final push, PR, merge, closure, and cleanup lifecycle.

Required Review is a hosting-platform control, not a Contract field. This
repository's `.github/CODEOWNERS` names `@xinglun` as the owner for the
template repository. The repository administrator must enable branch
protection on the default branch with at least one approving review from a
CODEOWNER, stale-review dismissal, and conversation resolution. The
`restrictedWriteApproval` Contract field records authorization to change
governance files; it must never be treated as proof that a platform review was
approved. Platform API evidence remains the source of truth for that boundary.

## Work Item Start Receipt

`make ai-start` creates a Git-tracked
`.ai/work-items/starts/<work-item-id>.json` before implementation begins. The
Receipt records the Work Item ID, Contract base commit, start timestamp, initial
Scope digest, and Contract skeleton digest. The active Contract keeps a binding
to those values. `make check-ai-start-receipt` and the Contract/PR checks fail
closed for a missing, malformed, digest-mismatched, base-mismatched, or
untracked Receipt. The Receipt proves creation-time lifecycle state only; it
does not prove implementation success, review approval, or merge status.

### Dependabot source candidates

Raw Dependabot PRs are not Work Item delivery branches. Hosted CI rejects a
`dependabot[bot]` candidate before quality and PR-ownership checks. Preserve
source facts, start a separate current-main Work Item, and bind its evidence to
the exact raw URL/head/diff digest. The gate never mutates a provider PR or
authorizes a successor merge. See [Dependabot Intake](dependabot-intake.md).

### Repository-wide active Work Item boundary

Before `ai-start` writes a Contract, Summary, Start Receipt, or Cockpit Status,
it enumerates linked Git worktrees. A different non-detached worktree with an
active Contract/Summary pair blocks the start and identifies its path, branch,
and Work Item ID. A malformed one-sided pair also blocks; it is not ignored as
historical noise. This makes the serial Work Item rule repository-wide rather
than merely a property of the current directory.

A later replacement delivery does not silently retire an earlier active Work
Item. Preserve the replacement's archived PR evidence, record the predecessor
and cleanup decision in a dedicated corrective Work Item, and clean the stale
local identity only within that authorized boundary. Do not rewrite an archive,
merge the stale branch, or discard user changes to make the check pass.

If a mandatory corrective Work Item closes while another Work Item is paused,
rebase the paused dedicated branch and use `make ai-resume-work-item
CONTRACT=<active-contract> BASE_REMOTE=<remote>
BASE_BRANCH=<default-branch>`. A valid append-only `resumeHistory` explains the
new Contract baseline while the original Receipt remains unchanged. Manual
Receipt, baseline, or history edits are rejected; the command requires the
exact predecessor merge, complete closure, archive manifest and digest
bindings, Git ancestry, and the original dedicated branch.

If no completed corrective predecessor is required but an active dedicated Work
Item must move to current main, do not perform a manual rebase. Fetch the
remote default branch, then use `make ai-synchronize-work-item
CONTRACT=<active-contract> BASE_REMOTE=<remote> BASE_BRANCH=<default-branch>`.
It is a local-only, fail-closed transition: it verifies a clean dedicated
worktree, immutable Start Receipt, live/tracking-ref equality, and ancestry;
it writes digest-bound `synchronizationHistory` evidence and invalidates prior
verification. It cannot push, force-push, open a PR, mutate provider state, or
rewrite archive/Start Receipt evidence.

`make ai-lifecycle-facts` is the machine-readable source for repository lifecycle state. Consumers should use its `state`, active Work Item counts, and explicit `notRun` fields instead of re-deriving lifecycle facts. It does not claim readiness or enterprise assurance.
## Adopter project
An adopter project keeps its own Git history and branch policy:

1. Identify the remote and platform-configured default branch.
2. Fetch it and create the work branch from its latest default-branch commit.
3. Record `baseRemote`, `baseBranch`, and `baseCommit` in the Contract.
4. Use a published release tag for installation or upgrade, not a moving template branch.
5. Finish and archive locally, then wait for human approval before commit and push.
6. Open one adopter-project PR and require manual review and merge.
7. After merge, wait for human approval before running `make ai-close-work-item TASK=<task>`; do not delete the remote or local branch directly.

The remote does not have to be named `origin`, and the default branch does not have to be `main`.

## Lifecycle closure

After the Work Item is archived and its PR is merged, run `make ai-close-work-item TASK=<task>`. The command discovers the repository base remote and default branch, verifies the current branch and PR mapping, switches to the base branch, fetches, and synchronizes with `git merge --ff-only`. Only then does it delete the local work branch and remote work branch. It finishes by verifying a clean worktree and identical local/remote base commits. `make ai-finish` alone is not closure; it is the archive milestone before push, PR, merge, and final cleanup.

The command is fail closed: an unmerged PR, inconsistent archived evidence, dirty state, non-fast-forward update, branch mismatch, deletion failure, or final synchronization mismatch prevents a successful closed result. The remote deletion is deliberately last so a failure leaves the local base branch safe for recovery.
## Installation and upgrade boundary
The template repository publishes a release; the adopter project consumes it and owns the resulting changes:

- template release preparation belongs to a template Work Item and template PR;
- adoption or upgrade belongs to an adopter-project Work Item and adopter-project PR;
- the two PRs have separate branches, base commits, reviews, and cleanup;
- record the release tag and source identity in the adopter Work Item.

Platform-specific facts such as PR number, approval state, and merge queue state belong to the hosting platform adapter. Repository-local Contract evidence records the branch base and source release without pretending to prove platform identity.
Review policy is adapter-driven: the template reports review focus, while the
adopter owns the choice among single-maintainer, CODEOWNERS, dual approval, or
protected environments. Review evidence must not be presented as an approval
performed by the template repository.
