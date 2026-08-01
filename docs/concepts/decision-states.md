---
author: Ray
title: "Decision States"
description: "The three human-facing states derived from governance evidence."
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Decision States

AI Cockpit compresses repository evidence into three human-facing states:

| State | Meaning | Human action |
| --- | --- | --- |
| Green | Required evidence is current and the bounded next action is supported. | Review and continue. |
| Yellow | Evidence is incomplete, stale, contradictory, or carries explicit residual risk. | Investigate or decide; do not infer success. |
| Red | A required control failed, scope was exceeded, or the requested action is not authorized. | Stop and satisfy the stated recovery condition. |

These states are decision aids, not guarantees of semantic safety. See
[How to Read Cockpit Status](../reference/how-to-read-cockpit-status.md) for the
generated signal model.

