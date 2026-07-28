---
author: Ray
title: AI Cockpit Work Item Lifecycle
description: Deterministic serial execution, budget, and release-evidence rules for governed Work Items.
---

# AI Cockpit Work Item Lifecycle

The default execution unit is one Work Item, one dedicated branch, and one PR. Work Items in a plan are executed serially:

```text
remote base → dedicated branch → Contract/Preflight → implement → ai-finish/archive
  → push → PR/review → merge → ai-close-work-item → synchronize and clean base
  → next Work Item
```

The next Work Item must not start until the predecessor has evidence for all of the following: PR merged, archive succeeded, local branch deleted, remote branch deleted, and local base synchronized with the remote base. A successor Contract may record this evidence in `predecessorWorkItem`; `make check-ai-serial-order` fails closed when any field is absent or false.

Create the dedicated Work Item branch before running `make ai-start`.
When one remote default branch can be identified, `ai-start` rejects execution
from that base branch before it writes a Contract, Summary, Start Receipt,
Cockpit Status, or task event. Repositories without one discoverable remote
default branch retain fixture/bootstrap behavior, but that absence is not
evidence that the current branch is safe.

## Pre-finish hosted verification snapshot

Some performance or environment-specific acceptance criteria require hosted
execution from a committed source before the final Summary can truthfully
report completion. For only that case, the active Contract must explicitly
require hosted verification and register pending `hostedPerformanceEvidence`.
After local implementation and verification, create a local snapshot commit
with explicit human authorization and run:

```text
make ai-prepare-hosted-verification-snapshot \
  CONTRACT=.ai/work-items/active/<task>.contract.json
```

The validator reruns local quality, binds a receipt to the branch, base,
commit, tree, active Contract and Summary, and confirms that Git refs and the
worktree were not mutated. The receipt identifies only pushing that exact
branch for hosted measurement as eligible and provides no human authorization.
It is not review readiness and cannot authorize a PR,
merge, tag, release, archive mutation, closure, or branch deletion. Release
intent, an archived Work Item, complete hosted evidence, a dirty/detached/base
state, baseline mismatch, or failed quality stops the stage. Once hosted
results are recorded in the active Summary, the Work Item must return to the
full `ai-finish`/archive → final push → PR → merge → `ai-close-work-item` →
cleanup lifecycle.

## Resume after a corrective predecessor

When a process defect pauses a Work Item, complete and close the corrective
Work Item first. Rebase the paused dedicated branch onto the latest discovered
remote default branch, replace its `predecessorWorkItem` with that corrective's
closed evidence, and run:

```text
make ai-resume-work-item CONTRACT=<active-contract> \
  BASE_REMOTE=<remote> BASE_BRANCH=<default-branch>
```

This is the only supported baseline transition for an existing Work Item. The
writer preserves the immutable Start Receipt, verifies the exact remote ref,
Git ancestry, original dedicated branch, predecessor merge identity, closure
postconditions, archive-manifest identity and digests, then atomically appends
one `resumeHistory` edge and advances Contract `baseCommit`. Repeated corrective
cycles append edges; they do not rewrite prior edges. Direct edits, broken
chains, or incomplete closure evidence fail closed. Afterward, rerun Preflight
and every verification made stale by the new baseline.

Version-1 Start Receipts created before the dedicated-branch start guard may
truthfully record the remote default branch in `baseBranch`. They are not
rewritten. A bounded compatibility resume accepts such evidence only when the
requested base branch equals the Receipt value, the current non-base branch is
exactly `codex/<work-item-id>`, every resume edge retains that same work branch,
and all ordinary ancestry, predecessor, archive-manifest,
digest, and closure checks pass. This recovery is not the normal start path and
does not permit new Work Items to start on the default branch.

## Contract readiness

Active v2 code Contracts must contain concrete problem, constraints, rationale, sources, acceptance, and verification content. Generic starter phrases are rejected by the Contract check before implementation. If Preflight reports `needs_human_confirmation` or `not_ready`, stop and report the reason; do not continue by treating advisory output as authorization.

## Complexity budget

Before implementation, estimate expected changes in the Contract's `budgetImpact`. At finish, `make check-ai-budget-impact` compares the generated complexity report with `.ai/guards/governance_complexity_policy.yaml`. An overrun is permitted only when the Contract explicitly records approval, a repayment Work Item, and repayment records. A separate budget-repair Work Item/PR is the appropriate repayment path when the current Work Item cannot repay its own increase.

## Release evidence states

Release evidence uses three distinct states:

- Historical: an existing archived Work Item or prior release record; preserve it as evidence and do not rewrite it.
- Candidate: a release commit/tag and its generated artifacts are prepared, but publication and source binding are not yet proven.
- Published: the public tag, source commit, release assets, checksums, SBOM, provenance, and release-state checks all point to the same source-bound release.

Do not report a candidate as published. `check-release-distribution` remains the source-bound verification for public release evidence.

## Closure rule

Only after the PR is merged and the Work Item is archived may `make ai-close-work-item TASK=<task>` run. The command owns branch deletion and must fail closed on any lifecycle mismatch. After closure, verify the local base equals the remote base and only then begin the next serial Work Item.
## Preflight hard gates before PR and release

After `make ai-finish TASK=<task>` archives the Work Item, commit the complete
Work Item bundle, then run `make check-ai-pr AI_BASE_COMMIT=<latest-default-branch-sha>`.
Do not run the aggregate PR check against an uncommitted archive or generated
release evidence. Independent review must finish while evidence is active;
post-archive fixes require a fresh Work Item and replacement PR. The order is:

```text
independent review → ai-finish/archive → commit bundle → check-ai-pr → push → PR
```

Before the `before_finish` checkpoint, complete the current v2 Summary's
`documentationAlignment` record. It must cover the plan,
Contract/Summary evidence relationship, documentation/commands/capability
language, multilingual semantics, and limitations/unknowns/history. Every
aligned evidence path must exist in the repository and also be declared by
`changedFiles` or `sourcesUsed`; changed documentation and command surfaces
must be recoverable in the opposite direction from that evidence. An
unreviewed, incomplete, misaligned, machine-local, missing, or undeclared
record blocks Finish.

Documentation alignment is a close-out evidence map, not a capability claim or
a replacement for tests, hosted evidence, provider controls, or the Capability
Truth Matrix. Historical archived Summaries that predate the field remain
immutable and readable; they are not backfilled.

During the current Work Item's archive transaction, exact active artifact paths
in `documentationAlignment` are migrated to their durable archive locations.
Execution-time evidence such as recorded commands and `executionContractPath`
remains unchanged because it describes the actual check context rather than a
current resolvable documentation reference.

The same archive transaction loads the registered instruction-traceability
manifest before moving any active artifact. If that JSON is malformed, archive
fails closed without moving the Contract or Summary. Every value exactly equal
to the current active Contract path is migrated to the generated archive
Contract path; lookalike paths, command strings that merely contain the path,
unrelated Work Items, and historical archive paths are not rewritten. A
manifest with no exact reference is a byte-for-byte no-op. When a rewrite is
needed, the archived Summary owns that generated change. If any later archive,
index, manifest, or status step fails, the transaction restores the original
active artifacts and traceability bytes before reporting failure.

This gate first runs the project formatter and, when the governance script and policy
are installed, the governance complexity/budget check; only then does it validate PR
ownership. This catches formatting drift and budget overflow before remote CI.
The PR must contain exactly one newly maintained Work Item and must be based on the
latest remote default branch; a branch derived from another unmerged Work Item is
invalid even when its tests pass.

When CI or PR checks block a change, pause before retrying. Perform a process-root-
cause review for missing preflight gates, wrong ordering, late formatter or budget
checks, template/adopter boundary errors, and source-bound evidence design. If the
failure is preventable in the workflow, open and complete a corrective Work Item
that adds an executable fail-closed gate before resuming the original operation.

Hosted quality failures must preserve their diagnostic payload before runner
teardown. A workflow that buffers individual Gate output may keep heartbeat
notices for liveness, but on failure it must also emit every non-passing Gate's
durable log. If the wrapper exits before per-Gate timing is written, it must emit
the wrapper log as the fallback. Timing metadata without the exact failing output
is not sufficient evidence for root-cause analysis.

Before release evidence is generated, run
`make finalize-release-freeze-premerge TASK=<task>` on the dedicated Work Item
branch after `ai-finish` has archived the Work Item and before committing the
release metadata. This is the only supported premerge freeze writer for a release
preparation PR: it requires the archived Work Item evidence, a clean branch, and
source-bound candidate metadata. Its canonical `sourceTree` and `archiveSha256`
are calculated from the clean candidate branch `HEAD`. The controlled
`SOURCE_COMMIT` reference is retained separately so the hosted release workflow
can resolve the exact merged default-branch identity. Both `.ai/work-items/active` and
`.ai/work-items/archive` are export-ignored, so moving evidence during Finish does
not change canonical content. After merge, the hosted detached checkout must
regenerate the same tree and archive or stop before tag mutation. Then run
`make check-release-preflight`; it fails closed when lifecycle evidence is absent
or inconsistent, archive policy blocks, or regenerated content differs.

```json
{
  "state": "frozen",
  "sourceTree": "<exact-default-branch-tree-sha>",
  "archiveSha256": "<regenerated-canonical-archive-sha256>",
  "lifecycle": {
    "state": "closed_and_synchronized",
    "command": "make ai-close-work-item",
    "baseCommit": "<exact-default-branch-tree-sha>",
    "worktreeClean": true
  }
}
```

After the marker and release metadata are bound, no new Work Item may be archived
until publication is complete. If any check fails, return to the candidate phase
and regenerate the source-bound evidence.

Template and adopter boundary: template-maintenance branches use the template
repository's `project-format-check` and governance policy from the latest template
default branch. An installed adopter uses its own configured formatter, remote
default branch, base commit, and governance policy; it must not copy the template's
absolute line or archive budgets.
