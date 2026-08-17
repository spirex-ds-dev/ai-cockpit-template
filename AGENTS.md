---
author: Ray
title: "Agent Operating Rules"
description: Codex and generic agent operating rules for AI Cockpit governed repositories.
keywords:
  - codex
  - ai-agents
  - ai-cockpit
  - governance
  - agent-rules
---

# Agent Operating Rules

This repository is an AI Governance Template. It is meant to be copied into other codebases and adapted. Agents work here inside a collaborative engineering environment, not only under a list of restrictions.

## Required Workflow

### Repository and Review Unit

The default unit of governed work is one Work Item, one dedicated work branch, and one pull or merge request. Do not combine unrelated Work Items on one branch or use one PR to deliver multiple independent Work Items.

This repository is the AI Cockpit template repository. Template-maintenance branches must be created from the latest `origin/main`. When these rules are installed into another repository, that repository is the adopter project: its work branch must be created from the latest commit on its own remote default branch. Do not assume that the adopter uses `origin` or `main`; discover and record its remote, default branch, and base commit in the Work Item Contract.

Installation and upgrade changes belong to the adopter project's history. They must use a published template release tag, not a moving template work branch. After the PR is merged, delete the remote and local work branch unless an explicitly documented recovery procedure requires retaining it.

Work Item completion is a lifecycle closure, not merely branch deletion. Run `make ai-close-work-item TASK=<task>` only after the Work Item is archived and the corresponding PR is merged. Closure must verify archived evidence, local branch/PR Head SHA ownership, fast-forward-only base synchronization, clean worktrees, and remote branch absence before deleting the local retry identity. Any failed step is fail closed and must not report the Work Item as closed. A remote failure must retain or restore the Work Item checkout for retry.

Only `ready_on_base` means the invoking worktree can start the next Work Item. `closed_but_current_worktree_detached` means closure succeeded while another worktree owns the synchronized base; continue from the reported base worktree and do not treat the detached invoking worktree as ready.

The canonical order is: latest remote base → dedicated Work Item branch → implement → `ai-finish`/archive → push branch → PR → merge PR → `make ai-close-work-item` → synchronize and clean the local base. Do not merge the feature branch into local `main` before the PR; that creates local commits that are not on `origin/main`. Do not use a PR merge option or provider setting that deletes the Work Item branch before `ai-close-work-item` can identify it. Branch deletion belongs to lifecycle closure.

Outcome is a terminality hard boundary: `ai-finish` must print a separate complete conversation result beginning with `Outcome: 🟢`, `Outcome: 🟡`, or `Outcome: 🔴`. Only `status=completed` together with `humanStatusColor=green`, current Contract/Summary/verification bindings, and direct human-visible delivery may authorize archive, PR readiness, closure, or release progression. Missing, folded-only, stale, yellow, red, or malformed Outcome evidence fails closed.

When a problem is discovered, repair it in the current Work Item first and preserve the blocked/retry evidence. Create a new Work Item only when the scope, authority, or base genuinely differs; do not create a new Work Item merely to avoid resolving a defect found in the current one.

One narrow exception exists when an active Contract explicitly requires hosted
verification that cannot run from an unpublished commit. After implementation
and local verification, create a local snapshot commit only with explicit human
authorization, then run `make ai-prepare-hosted-verification-snapshot
CONTRACT=<active-contract>`. A successful receipt identifies pushing that
exact dedicated branch for hosted measurement as the only eligible next
action; the receipt provides no human authorization itself. It does not permit
a PR, merge, release, archive mutation, closure, or branch deletion. Record the hosted
results in the active Summary, then return to the canonical
`ai-finish`/archive → final push → PR → merge → `ai-close-work-item` → cleanup
order. The snapshot command must never perform Git or provider mutations.

Before changing code, docs, CI, build files, or AI governance files:

1. Create or identify a Work Item Contract in `.ai/work-items/active/`.
   - **Contract Versions**: The framework enforces `contractVersion: 2`. Historic archived `v1` Contract files are preserved and parsed for backward-compatibility checks but new task contracts must use version 2 format.
2. Confirm the Contract has explicit `scope`, `outOfScope`, `sources`, `acceptance`, and `verification`.
   Contract is both delegation and description: it assigns task boundaries and makes the intended work legible before implementation.
   - **Intent (recommended)**: If the Contract contains an `intent` section, read it before implementing. If you have sufficient context, fill in at least `intent.problem` (detailed background), `intent.constraints` (constraints to respect), and `intent.rationale` (why this approach). All fields are optional — do not invent content when context is not provided.
3. Read `.ai/glossary.md` to align terminology and architectural boundaries before implementing.
4. For a `MODE=code` Work Item whose Preflight Review is `ready`, run `make ai-prepare-implementation CONTRACT=<contract> SUMMARY=<summary>` before changing implementation files. This is the only canonical way to record the required `before_edit` checkpoint; do not add it after verification has started.
5. Adhere strictly to the guidelines defined in the `guidelines` section of the Contract, and record compliance evidence in the Summary's `guidelinesCompliance` section.
6. Do not edit files outside the declared scope unless you first update the Contract.
7. Do not remove tests, snapshots, or Work Item records without documenting the reason in the Summary.
8. Update the AI Change Summary before finishing.
   Summary is not only an audit artifact; it is also the handoff record for reviewers and the next collaborator.
9. Run the AI checks and project checks declared in the Contract.
10. When `make ai-start ... MODE=code` or `make ai-preflight` reports `needs_human_confirmation` or `not_ready`, pause and report the Preflight Review to the user before coding continues. Advisory mode means the command may exit successfully; it does not permit silent implementation.

### Documentation Authority Boundary

For documentation that may be treated as an instruction source, start with the
machine-readable default read set from `make ai-documentation-read-set`.
Reference material requires explicit `INCLUDE_REFERENCE=1`; documents under
`docs/archive/` are historical context and cannot grant current instruction.
This routing rule complements, and never replaces, this `AGENTS.md` file.

`unknowns` and `notCodable` are valid outputs when the task is not ready for coding. `make ai-checkpoint` is environment support against long-task drift, not paperwork.

## Safety Rules

- Never revert user changes unless the user explicitly asks.
- Never include secrets, personal paths, local credentials, API keys, or machine-specific configuration in template files.
- Keep rules language-neutral and project-neutral.
- Prefer modifying `checks.yaml`, guard YAML, and Makefile targets over hardcoding repository-specific behavior in scripts.
- Generated status files must be generated by command, not hand-edited.

## Finish Criteria

A Work Item is ready for review only when:

- `make check-ai-contract` passes.
- `make check-ai-scope` passes.
- `make check-ai-guards` passes.
- `make ai-checkpoint` passes (at `before_finish` stage).
- `make check-ai-agent-risk` passes.
- `make check-ai-review-policy` passes.
- `make check-ai-backtrack` passes.
- `make check-ai-coverage-guard` passes.
- `make check-ai-guidelines` passes.
- `make check-ai-change-summary` passes.
- `make generate-cockpit-status` has been run.
- `make check-ai-status` passes.
- `make check-ai-status-consistency` passes.
- Required project verification commands have passed or are explicitly documented as not run with a reason.
- Verification results for stabilization steps are fully captured and logged in the Summary's verification fields (for contractVersion 2).
