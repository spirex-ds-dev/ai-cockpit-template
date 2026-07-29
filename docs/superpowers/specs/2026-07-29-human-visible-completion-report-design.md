---
author: Ray
title: Human-Visible Work Item Completion Report Design
description: Decision-oriented closure handoff for AI Cockpit Work Items.
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# Human-Visible Work Item Completion Report Design

## Problem

Outcome and Closure Receipt files are necessary audit evidence, but a path-only completion message asks the human to open artifacts to learn whether work is complete, verified, merged, and cleaned up. That is the inverse of AI Cockpit's Human-Agent Trust purpose: the system must compress verified repository truth into a decision-ready human handoff.

## Decision

`ai-close-work-item` will emit a fixed, concise **Human completion report** after closure has verified the PR merge, base synchronization, and branch cleanup. It will lead with the result and state only facts held in the verified closure result:

1. delivered Work Item and its human-readable title;
2. verified local archive evidence and merged-PR identity;
3. merged PR URL and merge commit;
4. local and remote branch cleanup plus base synchronization;
5. residual-risk status;
6. next-work guidance, including the exact base worktree when the invoking checkout is detached.

Only after the direct report may the CLI list Outcome and Closure Receipt paths as optional audit evidence. The executor adds the exact-head Hosted CI conclusion it independently checked before merge when forwarding the report to the human conversation.

## Boundaries

- The report derives from `close_work_item`'s verified result. It must not query, infer, or invent provider facts after the verified boundary. In particular, merged PR identity is not a substitute for a recorded Hosted CI result.
- The report distinguishes `nextWorkItemReady: true` from a detached invoking worktree. It never says “ready” for the latter.
- A repository script cannot send an external chat message. `AGENTS.md` therefore makes copying the canonical report text into the human conversation a required executor action after successful closure.
- Existing archived Outcome and Closure Receipt files remain immutable and are not backfilled.

## Validation

`tests/test_work_item_lifecycle_closure.py` will exercise canonical report rendering with ready and detached result fixtures. It will prove that required facts appear before audit paths and that incomplete result input raises rather than emitting a partial successful report. The existing full lifecycle test continues to prove report output occurs only after closure verification.

## Non-goals

- No new external notification integration.
- No alteration of PR merge, release, provider, or cleanup behavior.
- No claim that report prose itself is security, compliance, or provider evidence.
