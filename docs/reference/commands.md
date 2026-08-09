---
author: Ray
title: "Commands"
description: "Reference index for public AI Cockpit command families."
audience:
  - contributor
  - maintainer
status: reference
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Commands

| Need | Command family | Detailed owner |
| --- | --- | --- |
| Start and prepare work | `make ai-start`, `make ai-preflight`, `make ai-prepare-implementation`, `make ai-revalidate-contract-amendment` | [First Work Item](../getting-started/first-work-item.md) |
| Calibrate | `make cockpit-doctor`, `make cockpit-calibrate-session` | [First Calibration](../getting-started/first-calibration.md) |
| Verify | `make quality-fast`, `make quality-full`, `make quality-release`, `make ai-cockpit-quality` | [Quality Gates](../operations/quality-gates.md) |
| Finish and archive | `make ai-finish` | [Work Item Lifecycle](../operations/work-item-lifecycle.md) |
| Close after merge | `make ai-close-work-item` | [Work Item Lifecycle Closure](work-item-lifecycle-closure.md) |
| Diagnose | `make generate-cockpit-status`, `make cockpit-doctor` | [Troubleshooting](troubleshooting.md) |

Run `make help` in the exact installed revision for the executable command list.

For a code Contract with `implementationSurface`, use
`make ai-preflight CONTRACT=<contract>` before `make ai-prepare-implementation`.
The Preflight rejects an unowned, out-of-scope, malformed, forbidden, or
unapproved restricted implementation path before `before_edit` is recorded.

During an `in_progress` or `paused` calibration Session, ordinary `make
ai-start` fails closed. For a Session-discovered template/workflow defect only,
pass the complete JSON declaration through
`AI_START_CALIBRATION_CORRECTIVE`; see [Controlled corrective route during live
calibration](ai-cockpit-work-item-lifecycle.md#controlled-corrective-route-during-live-calibration).
The declaration is not a general readiness override and is checked again by
the active Contract and immutable Start Receipt.
## Active evidence and hosted snapshots

Active Work Item Contract and Summary files are committed evidence on the
dedicated Work Item branch. Do not force-add them: normal staging includes
them, while local review JSON remains ignored. Before
`ai-prepare-hosted-verification-snapshot`, commit the intended candidate and
work from a clean whole worktree. The snapshot only validates and writes its
receipt; it does not stage, commit, push, open a PR, merge, or archive.

For a hosted measurement only, after the snapshot receipt identifies the exact
branch and the human has authorized its push, dispatch the smoke workflow with
`purpose=hosted_measurement`. Retrieve the emitted
`hosted-measurement-receipt-<run-id>-<attempt>` artifact and verify its
`commitSha` equals the snapshot receipt before recording the run URL, job
conclusions, and artifact in the active Summary. This receipt has no authority
to open a PR, merge, release, archive, close a Work Item, or delete a branch.
