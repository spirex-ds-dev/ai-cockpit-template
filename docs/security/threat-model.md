---
author: Ray
title: "Threat Model"
description: "Repository-governance threats AI Cockpit can bound and the threats it cannot prove away."
audience:
  - security_reviewer
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Threat Model

AI Cockpit addresses reviewable repository risks: undeclared scope expansion,
test weakening, unsafe removal or rename impact, missing verification, evidence
gaps, governance bypass, stale state, and lifecycle ownership mistakes.

It cannot prove agent intent, prevent every filesystem write, identify every
dynamic or external consumer, isolate production credentials, authenticate
enterprise identities, or certify a release. Those remain external controls or
explicit Unknowns.

Each gate must state its inputs, proven range, unproven range, false-positive
and false-negative risk, and recovery condition. See
[Security Boundaries](../security-boundaries.md) for the broader explanatory map.

