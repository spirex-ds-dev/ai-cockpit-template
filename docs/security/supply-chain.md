---
author: Ray
title: "Supply Chain"
description: "Ownership boundary for release, provenance, SBOM, signature, and vulnerability evidence."
audience:
  - security_reviewer
  - maintainer
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Supply Chain

AI Cockpit can require, cite, validate, and aggregate supply-chain evidence. It
does not replace the tools or external systems that create provenance,
signatures, SBOMs, vulnerability results, trusted release identities, or branch
protection evidence.

Template-hosted evidence does not prove an adopter's repository or release.
Adopters must bind external evidence to the exact source, tag, asset digest,
commit, workflow run, and trust root used for their decision.

Use [Security and Release Verification](../getting-started/security-release-verification.md)
for the operational path and [CI Release Evidence](../reference/ci-release-evidence.md)
for evidence ownership.

