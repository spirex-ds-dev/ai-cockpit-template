---
author: Codex
title: "Stale Active Work Item Supersession"
description: "Corrective plan for repository-wide active Work Item uniqueness after the duplicate local #441 identity was found."
---

# Stale Active Work Item Supersession

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Instruction

When old local worktrees or branches remain, converge them rather than leaving a
latent hazard. If the cause is a workflow defect, fix the process and add an
executable check before the next planned Work Item continues.

## Finding

`dependabot-441-setup-dotnet-20260729` remains active in the top-level local
worktree even though the independently governed replacement
`dependabot-441-setup-dotnet-20260730` was archived and merged as PR #468.
The old branch has no remote branch and must not be merged. The previous
`ai-start` gate examined only its invoking worktree, so it did not expose this
repository-wide serial-work violation.

## Plan

1. Add red-first regressions for another linked worktree with a valid active
   Contract/Summary pair, a malformed pair, and a detached historical worktree.
2. Make `ai-start` enumerate only Git-linked worktrees before it writes any
   lifecycle artifact. A complete or malformed foreign active pair must stop
   with the exact worktree, branch, and Work Item identity.
3. Document the same supersession boundary in English and Japanese. A
   replacement archive is evidence, not silent permission to delete the old
   Work Item or user changes.
4. Record the replacement relationship and the post-closure cleanup boundary in
   this Work Item's Summary. Only after this corrective has merged and closed
   may the obsolete local #441 identity be detached and removed; then the next
   `ai-start` must prove that no active pair remains.

## Traceability

| Instruction | Plan | Implementation | Acceptance |
| --- | --- | --- | --- |
| Converge stale worktrees | 1, 4 | linked-worktree start guard; recorded cleanup boundary | A1, A3, A5, A6 |
| Prevent recurrence in process | 1, 2 | `scripts/ai_start.py`, regression tests | A1, A2, A3 |
| Preserve evidence and user changes | 3, 4 | bilingual workflow docs, Summary | A4, A5 |

The reverse Acceptance → Implementation → Plan → Instruction check must resolve
each row before archive. No archive, Provider PR, release, or user-owned change
is rewritten by this Work Item.
