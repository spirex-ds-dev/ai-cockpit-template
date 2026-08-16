---
author: Ray
title: "Agent Parallel Work Items"
description: "Reference procedure for Agent-owned parallel Work Item orchestration."
audience:
  - contributor
  - maintainer
status: reference
authority: reference
lastVerifiedBy: agent-parallel-work-items-skill
capabilityClaims:
  - agent_parallel_work_item_planning
---

# Agent Parallel Work Items

The locally discoverable `agent-parallel-work-items` Skill evaluates a request
for safe parallel execution. It does not add a scheduler to AI Cockpit or WIII.
The Agent owns dispatch, capacity, aggregation, retries, and cancellation.

## Boundary

`Task = Work Item = dedicated branch = dedicated worktree = PR`. Every Work
Item has its own Contract, Summary, verification, archive, merge, and closure.
AI Cockpit and WIII stay current-worktree-local: each worktree has at most one
active Contract/Summary pair and one generated Cockpit report. An Agent queries
each owned worktree separately and keeps any aggregate view ephemeral.

## Automatic decision

The Skill triggers for requests with multiple deliverables or possible Agent,
subagent, branch, worktree, or PR parallelism. It first maps each candidate's
acceptance, writable paths, generated evidence, base requirements, verification,
and lifecycle dependencies.

Parallel execution is allowed only for candidates with no shared writable path,
no shared generated evidence, no ordered dependency, and no required common
external authority. Otherwise the Agent serializes the affected Work Items and
records why. Uncertainty is a reason to serialize, not to assume independence.

Generated Cockpit status, active evidence, archive indexes, and release or
documentation projections are shared evidence until their producing Work Item
has archived and merged. Candidates that would write any of those paths are
serial, even if their source-code paths differ. Each dispatched candidate uses
its own dedicated worktree; no Agent writes a sibling Work Item's checkout.

## Integration rule

Isolation does not prove compatibility. Before archive, each Work Item must
reconcile with the latest target base and run its declared integration checks.
An archive is immutable: never rebase an archived Work Item or regenerate its
frozen evidence. If a parallel merge makes it incompatible, preserve that audit
record and create a fresh replacement Work Item from current main.

## Recovery boundary

When a Work Item is blocked, its Contract, Summary, Outcome, worktree, and
branch remain evidence. Do not repair it with cross-worktree edits, manual
rebase, stash, temporary commit, environment substitution, archive rewrite, or
provider-state mutation. First identify whether the failure is a process
defect. If it is, open and complete its corrective Work Item. Then use the
governed successor or quarantine transition where applicable, create the
replacement from current main, and bind the predecessor receipt in the new
Contract. The replacement is independently verified, archived, reviewed,
merged, and closed; it does not retroactively turn the predecessor Outcome
green.

After a group of Work Items closes, the Agent records reusable lessons and
improves the Skill or reference documentation in its own governed Work Item.
Final delivery runs a separate audit–repair–re-audit loop before a separately
governed release workflow.

## Human conversation handoff

An archived Outcome or a `task_report` file is durable repository evidence,
not proof that a human saw the result. Every owning Agent must therefore relay
its completion to the human conversation (or have the parent orchestrator do
so) immediately after the governed finish/closure boundary. The handoff must
include:

- one visible traffic-light marker: 🟢, 🟡, or 🔴;
- the Work Item id and Outcome status;
- the concise delivered/finding/limitation summary; and
- the next safe action or explicit recovery condition.

The relay is required for every Agent and subagent, not only the root Codex
conversation. If the execution surface cannot expose a conversation receipt,
the status remains yellow with `conversationUiReceipt=not_observable`; the
Agent must not claim delivery merely because stdout, Markdown, or JSON exists.
