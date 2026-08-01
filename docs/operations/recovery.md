---
author: Ray
title: "Recovery"
description: "Operational recovery model for stopped or failed governed work."
audience:
  - contributor
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Recovery

A stop is useful only when it names the evidence gap and a bounded recovery
condition. Preserve the active Contract, Summary, branch, and checkout until the
failed stage can be retried with new evidence.

- Preflight stop: correct missing or contradictory Contract evidence and rerun it.
- Verification stop: retain the failing command and output, fix within scope, and rerun only the affected route before aggregate verification.
- Hosted stop: bind the exact Head SHA and hosted run evidence; never substitute a local claim.
- Closure stop: retain or restore the Work Item checkout and retry closure after provider/base state is repaired.

Installation-specific symptoms are in
[Installation Troubleshooting](../troubleshooting/installation.md); general
operator details are in [Troubleshooting](../reference/troubleshooting.md).

