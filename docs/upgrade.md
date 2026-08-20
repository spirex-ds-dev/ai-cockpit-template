---
author: Ray
title: "Upgrade"
description: "Reader-first entry for updating an existing AI Cockpit installation safely."
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
keywords: [ai-cockpit, upgrade, compatibility, migration]
---

# Upgrade

## What this helps you do

Use this route when your project already has AI Cockpit and you want to update
the managed files. An upgrade is its own adopter-project Work Item. It is not
just a command and it is not proof that calibration or activation has finished.

## Tell your Agent what you want

> “Prepare an upgrade for this existing AI Cockpit installation. First show me
> the current and target versions, base branch, managed-file changes, conflicts,
> rollback evidence, and every point where I must decide.”

Before any write, review the generated Contract, the Impact Assessment, the
target release source, and the upgrade diff. Keep the existing Active
Configuration available until the Candidate activates successfully.

## Safe sequence

1. Start an independent upgrade Work Item from the adopter repository's latest
   remote default branch.
2. Record the current installation, target release tag, remote, default branch,
   and base commit.
3. Let the installer prepare a plan and conflict report; do not silently
   overwrite project-owned governance files.
4. Review the managed-file diff and rollback backup root.
5. Confirm the write only after the plan and conflicts are understood.
6. Run the adopter's calibration and local checks as separate evidence.
7. Review, commit, push, and merge through the normal Work Item lifecycle; the
   installer does not perform those external Git actions.

## Example and expected result

Request:

> “Upgrade without changing the active configuration if the candidate fails,
> and stop if there is an active Work Item or an unresolved conflict.”

Expected result: a plan identifies the source and target, a Contract and Summary
capture the change, conflicts are explicit, backups are available for rollback,
and the old active configuration remains available on a failed activation.

## Stop and recovery

Stop before writing when an active Work Item exists, the remote default branch
cannot be established, a managed file diverged, the target is a downgrade, or
the conflict report is missing or malformed. Resolve the conflict or provide
explicit base evidence before retrying. Use `--upgrade-with-active` only for an
intentional, separately reviewed recovery scenario.

## Advanced route

The exact installer options, release-source variables, rollback behavior, and
conflict report contract are in the [Reference Upgrade](reference/upgrade.md)
guide. It is the technical English reference for the command and file details.

The installer never commits, pushes, opens or merges a PR, or deletes a review
branch. Those actions require their own Work Item evidence and human/provider
decisions.

Related: [Capabilities and boundaries](capabilities.md),
[Work Item Lifecycle](operations/work-item-lifecycle.md), and
[Recovery](operations/recovery.md).
