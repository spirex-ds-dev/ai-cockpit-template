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
