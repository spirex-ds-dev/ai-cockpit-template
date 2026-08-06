---
author: Ray
title: AI Cockpit Work Item Lifecycle
description: Isolated Work Item lifecycle, agent-orchestrated parallelism, budget, and release-evidence rules.
---

# AI Cockpit Work Item Lifecycle

The default execution unit is one Work Item, one dedicated branch, and one PR.
Within one Work Item its lifecycle is serial and evidence-bound:

```text
remote base → dedicated branch → Contract/Preflight → implement → ai-finish/archive
  → push → PR/review → merge → ai-close-work-item → synchronize and clean base
  → close and clean that Work Item
```

An agent or subagent may orchestrate multiple independent Work Items in parallel
when each has a separate linked worktree, `codex/<work-item-id>` branch,
Contract/Summary pair, PR, archive, and closure receipt. AI Cockpit does not
schedule those tasks and a Work Item never becomes a shared global runtime
lock. It validates the local record shape and fails closed for malformed,
unpaired, mismatched, or non-dedicated active branches.

For a start request with a different Work Item ID, a malformed foreign
linked-worktree identity is isolated rather than becoming a global start
deadlock. The foreign Work Item is never edited or cleaned automatically;
starting that same Work Item remains fail-closed until its owner repairs the
identity. Run `make ai-doctor` to see the isolated identity and its recovery
boundary before deciding on a corrective Work Item.

When a Work Item is a declared successor, it must wait for its predecessor to
have evidence for PR merge, archive, local/remote branch deletion, and base
synchronization. `make check-ai-serial-order` fails closed when that declared
dependency is incomplete; independent Work Items do not acquire that edge.

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

## Record a successor or quarantine route

When an active Work Item already has a red blocked Outcome and an authorized
corrective successor, do not write a receipt by hand. Record the limited route
with `make ai-transition-to-successor PREDECESSOR_TASK=<blocked-task>
SUCCESSOR_TASK=<new-task> SUCCESSOR_BRANCH=codex/<new-task>
SUCCESSOR_BASE=<base-sha> ISSUE=https://github.com/<owner>/<repo>/issues/<n>
AUTHORITY='<recorded human authority>' MODE=quarantined REASON='<why>'`.
The command validates the blocked Outcome, exact identities, same-repository
Issue, authority, mode, and receipt location. Status/doctor show a yellow route
while the predecessor Outcome remains red. It never authorizes archive, merge,
release, branch deletion, provider mutation, or predecessor evidence rewrite.

When a process defect pauses a Work Item, complete and close the corrective
Work Item first. Rebase the paused dedicated branch onto the latest discovered
remote default branch, replace its `predecessorWorkItem` with that corrective's
closed evidence, and run:

```text
make ai-resume-work-item CONTRACT=<active-contract> \
  BASE_REMOTE=<remote> BASE_BRANCH=<default-branch>
```

This is the supported baseline transition when a completed corrective predecessor
is the source of the new baseline. The
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

## Synchronize an active Work Item to current main

When an active dedicated Work Item is behind the live remote default branch but
does not have a completed corrective predecessor, do not run Git rebase by
hand. First fetch the target so the local tracking ref equals the live remote
head, then run:

```text
make ai-synchronize-work-item CONTRACT=<active-contract> \
  BASE_REMOTE=<remote> BASE_BRANCH=<default-branch> \
  TARGET_ROOT=<target-worktree-root>
```

The command has local-only authority: it verifies the immutable Start Receipt,
active Contract/Summary pair, dedicated branch identity, tracking-ref freshness,
and ancestry. A clean Work Item rebases directly. A dirty Work Item may proceed
only with an explicit Contract `synchronizationCheckpoint` authorization and
only when every dirty path is Contract-owned or a governed generated artifact;
it first creates a recoverable local checkpoint and records its identity and
paths in the digest-bound `synchronizationHistory` transition. It never pushes,
force-pushes, opens a PR, changes provider state, rewrites the Start Receipt,
or changes archive evidence. A conflict is automatically aborted before any
active evidence write. A successful synchronization marks prior verification
`not_run`; rerun Preflight and all required current-generation checks before
Finish. Replay, stale tracking state, detached/base/foreign branches, dirty
worktrees, unrelated histories, and malformed evidence fail closed.

`TARGET_ROOT` is optional when the target is the current checkout; it is
required for a caller acting on a distinct target worktree. The runtime treats
that root as the sole source for Contract/Summary resolution, Git operations,
validation, and evidence writes, and never reads caller active evidence as a
fallback.

## Contract readiness

Active v2 code Contracts must contain concrete problem, constraints, rationale, sources, acceptance, and verification content. Generic starter phrases are rejected by the Contract check before implementation. If Preflight reports `needs_human_confirmation` or `not_ready`, stop and report the reason; do not continue by treating advisory output as authorization.

### Contract amendment revalidation

`before_edit` proves the phase boundary at which implementation was first
authorized. It is immutable evidence: do not rerun
`make ai-prepare-implementation` after that record exists, and do not edit the
Summary to replace it. If a legitimate scope or Contract amendment is needed,
first amend the Contract through the governed review path, then run:

```text
make ai-revalidate-contract-amendment \
  CONTRACT=.ai/work-items/active/<task>.contract.json \
  SUMMARY=.ai/work-items/active/<task>.summary.json \
  PREVIOUS_CONTRACT_HASH=<immutable-before-edit-hash> \
  AMENDMENT_REASON='<why the Contract changed>'
```

The command appends a `contract_amendment_revalidation` checkpoint that binds
the original `before_edit` hash, the preceding Contract hash, the amended
Contract hash, the reason, and whether required verification had already
started. If verification had started, the revalidation must additionally
invalidate every required gate and record the prior passed-gate count; Finish
then reruns the full required gate set for the amended Contract. Missing,
malformed, stale, or cross-Contract revalidation evidence fails closed. The
record does not authorize a merge,
release, provider mutation, or a manual rewrite of lifecycle evidence.

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
release evidence. Independent review must finish while evidence is active. The order is:

```text
independent review → ai-finish/archive → commit bundle → check-ai-pr → push → PR
```

Before either Finish archive path mutates active evidence, it runs
`make check-changed-critical-coverage AI_BASE_COMMIT=<Contract baseCommit>`.
The resulting report binds the immutable Contract base plus the candidate HEAD
and worktree state observed by the coverage run. A missing or failing result
produces a blocked active Outcome and denies archive. This guard complements,
rather than replaces, the clean committed `check-ai-pr` gate.

The installer-created `adopt_ai_cockpit` Contract is the only bounded
not-applicable case: its explicit `adoptionBootstrapPaths` identify template
runtime files whose mapped template tests are intentionally not copied into an
adopter. The command records the Contract-bound applicability result and still
fails closed for malformed adoption metadata, ordinary Work Items, and missing
ordinary mappings. Its generated report remains local state and must not alter
the archive worktree digest.

If `check-ai-pr` discovers a changed-critical-coverage or archive-evidence
failure only after archive, do not rewrite its Contract, Summary, Outcome, or
manifest and do not create a duplicate Work Item solely for that repair. Start
the narrow same-Work-Item route from the clean committed candidate:

```sh
make ai-open-post-archive-recovery \
  TASK=<task> AI_BASE_COMMIT=<merge-base-sha> \
  ISSUE=<repository-issue-url> AUTHORITY='<recorded human authority>' \
  RECOVERY_PATHS='scripts/example.py tests/test_example.py'
```

The command first reproduces the failing aggregate PR audit, then writes one
append-only receipt binding the archive digests, PR base, failure output,
authority, Issue, and finite repair paths. `check-ai-pr` independently
revalidates it and grants ownership only to those paths. The receipt never
authorizes archive rewrite, merge, release, branch deletion, closure, or new
scope. Use a successor only when the Contract/base/scope itself is invalid or
a new delivery is required.

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
not change canonical content.

Do not run `make check-release-preflight` on the premerge metadata commit. That
commit carries the candidate freeze records but is not the release source identity;
the exact-source gate would correctly reject it. The gate runs only after runtime
freeze on the exact merged `SOURCE_COMMIT`, in the hosted detached checkout. After
merge, that checkout must regenerate the same tree and archive or stop before tag
mutation. `make check-release-preflight RELEASE_PREFLIGHT_SOURCE_COMMIT="$SOURCE_COMMIT"`
then fails closed when lifecycle evidence is absent or inconsistent, archive policy
blocks, or regenerated content differs.

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

Historical premerge markers and release metadata remain preparation evidence;
they do not authorize publication of a later source tree. If a later correction
changes included source bytes, preserve the old record and follow the readiness
and rehearsal sequence below rather than mutating or repeatedly regenerating it.

## Release readiness and exact-source rehearsal

For new release attempts, the committed premerge marker is historical preparation
evidence, not the authority for a later default-branch source tree. Run
`make check-release-readiness` only after there are no active Work Items. It
checks stable candidate, policy, archive-growth, and mandatory Japanese evidence,
but deliberately does not compare a historical `release-freeze.json` to current
source bytes.

The required sequence is: synchronized default branch → repository readiness →
successful same-SHA rehearsal → actual hosted release. The rehearsal uses the
same exact-source checkout, runtime freeze, strict preflight, locked dependency,
required-CI, supply-chain-evidence, and strict-smoke path as publication. It
creates a private Actions receipt, never a tag, GitHub Release, or public asset.
It is not a published release.

The actual hosted release receives the rehearsal run id, resolves the default
branch again, and rejects a missing, failed, wrong-workflow, wrong-SHA, or
wrong-tag receipt before runtime finalization or immutable mutation. The gate
still runs only after runtime freeze on the exact merged `SOURCE_COMMIT`; exact
archive, digest, installer, and identity checks remain mandatory at that boundary.

A later included-source change invalidates the rehearsal SHA and requires a new
same-SHA rehearsal, not another committed freeze. If exact-source validation
fails after a successful rehearsal, stop, preserve diagnostics, and open a
corrective Work Item; do not create a new freeze Work Item as a substitute for
root-cause repair.

Template and adopter boundary: template-maintenance branches use the template
repository's `project-format-check` and governance policy from the latest template
default branch. An installed adopter uses its own configured formatter, remote
default branch, base commit, and governance policy; it must not copy the template's
absolute line or archive budgets.
