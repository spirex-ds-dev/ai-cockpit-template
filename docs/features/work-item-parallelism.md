---
author: Ray
title: "Work Item parallel processing"
description: "How to process independent Work Items concurrently while keeping scopes, evidence, and shared projections safe."
audience:
  - adopter
  - contributor
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
  - work_item_intelligence_interface
keywords: [ai-cockpit, work-item, parallelism, concurrency, evidence]
---

# Work Item parallel processing

## What this helps you do

Use this guide when you want several independent Work Items to move forward at
the same time. This is **parallel Work Item processing**, not a claim that
evaluation or every verification command can run in parallel.

The goal is simple: independent work may proceed concurrently, while anything
that shares files, generated projections, evidence, or a serialized lifecycle
decision waits its turn.

## Before you start

Before dispatching a second Work Item, confirm:

- both goals are genuinely independent;
- each Work Item has its own Contract, branch, worktree, and owned scope;
- neither task changes the same file or generated projection;
- neither task consumes mutable evidence that the other task is still producing;
- both tasks use a trusted, known base and can be verified independently;
- a human or the external Agent/Orchestrator has authority to coordinate them.

## Tell your Agent what you want

You can say:

> “Move the documentation-index task and the independent calibration-reference
> task forward at the same time. Give each its own Work Item, branch, worktree,
> scope, evidence, and final review. If they share a file or generated
> projection, serialize that part instead of merging the identities.”

The Agent/Orchestrator is responsible for dispatch, concurrency, retry, and
provider coordination. AI Cockpit governs each Work Item's local Contract,
scope, evidence, verification, Summary, Outcome, and closure; it is not the
scheduler or retry controller.

## What happens

1. The coordinator compares the two Contracts and their path/evidence ownership.
2. Compatible Work Items receive separate branch/worktree identities.
3. Each Agent works only inside its owned scope and records its own evidence.
4. Shared paths, shared generated outputs, or shared serialized projections
   are reserved and processed one at a time.
5. Each Work Item runs its own verification and produces its own Summary and
   Outcome.
6. The coordinator aggregates results without combining Work Item identities.
7. Merge and closure still follow the normal PR and `ai-close-work-item`
   lifecycle for each Work Item.

## Safe example

```text
Work Item A: update the onboarding guide in docs/getting-started/.
Work Item B: review a separate reference page in docs/security/.

Separate branches, worktrees, scopes, evidence, and PRs:
both may proceed concurrently and are reviewed independently.
```

Bounded verification may also run concurrently when the configured check graph
allows it and the checks do not write or consume the same mutable evidence.
That is a verification optimization, not parallel Work Item identity.

## Unsafe example

```text
Work Item A: regenerate docs/reference/capability-truth-matrix.json.
Work Item B: edit a capability claim whose evidence is bound to that matrix.

The evidence projection is shared. Serialize the work or amend the ownership
so one Work Item owns the complete source-bound change.
```

Do not put two tasks on one branch, one worktree, or one Contract merely because
their goals look related. Do not let a coordinator hide an overlap by assigning
the same path to two Work Items.

## What WIII does and does not do

The Work Item Intelligence Interface (WIII) is a read-only, current-worktree
machine-readable projection. It helps an Agent inspect local Work Item
intelligence; it is not a scheduler, DAG engine, retry controller, agent
manager, distributed lock service, or cross-worktree coordination service.

An external Agent or Orchestrator owns task dispatch and concurrency. A WIII
view does not prove that another worktree is clean, that a provider merged a
PR, or that a human approved the next action.

## If parallel processing stops

Stop and keep the Work Items separate when:

- a path or generated projection overlaps;
- the base commits are incompatible or stale;
- ownership of evidence is ambiguous;
- a required check writes shared state without a safe boundary;
- one Work Item needs authority or scope not declared in its Contract;
- the coordinator cannot prove which Work Item owns a changed path.

Recover by serializing the conflicting portion, amending and revalidating the
Contract before changing scope, or creating a genuinely independent successor.
Do not retry blindly and do not delete a checkout after a remote failure.

## Advanced route

The maintainer references describe the exact ownership rules and bounded
verification behavior:

- [Agent parallel Work Items](../reference/agent-parallel-work-items.md)
- [Safe parallel verification](../reference/safe-parallel-verification.md)
- [Work Item Intelligence Interface](../reference/work-item-intelligence-interface.md)
- [Work Item Lifecycle](../operations/work-item-lifecycle.md)

The current-worktree WIII projection is read with the repository's configured
status/intelligence entrypoints. It does not replace the normal Contract,
verification, PR, or closure commands.

## Related entry points

- [Capabilities and boundaries](../capabilities.md)
- [Task Outcome Report](task-outcome-report.md)
- [Recovery](../operations/recovery.md)
