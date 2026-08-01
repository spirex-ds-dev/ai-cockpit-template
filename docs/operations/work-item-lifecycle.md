---
author: Ray
title: "Work Item Lifecycle"
description: "Canonical operational sequence for one governed change."
audience:
  - contributor
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
---

# Work Item Lifecycle

<!-- governance-flow: install,configure-work-item,onboard,doctor,calibrate,confirm,validate,readiness,develop -->

The review unit is one Work Item, one dedicated branch, and one PR:

```text
latest remote base → Contract → preflight → implementation → verification
→ Summary/Outcome → archive → commit/push → PR → merge → closure → cleanup
```

`ai-finish` creates and archives completion evidence before the PR. After the
provider reports the PR merged, `make ai-close-work-item TASK=<task>` verifies
archive ownership, merged Head SHA, base synchronization, clean worktrees, and
remote branch absence before deleting the retry identity.

Use [Work Item Lifecycle Closure](../reference/work-item-lifecycle-closure.md)
for the complete fail-closed states and retry rules.
