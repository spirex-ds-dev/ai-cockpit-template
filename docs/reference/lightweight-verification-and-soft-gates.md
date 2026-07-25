---
author: Ray
title: "Lightweight Verification and Escalation"
description: "Deterministic verification levels, cache integrity, DAG ordering, and fail-closed escalation."
keywords:
  - verification
  - escalation
  - cache
  - governance
---

# Lightweight Verification and Escalation

Verification policy is evidence-derived and monotonic:

- Light may use focused checks for low-impact documentation changes.
- Standard uses the required full project gate for pull requests.
- Strict always uses the Full Gate for release, workflow, trust, installer, unknown, dependency, and other high-risk changes.

`scripts/ai_verification_policy.py` computes a content address from the base, diff, command, tool, dependency, environment, and configuration inputs. A cache entry is valid only when every input is present and identical. Missing inputs fail closed.

Checks are represented as a directed acyclic graph. Dependencies are ordered deterministically; unknown dependencies and cycles are errors. Escalation reasons include release/workflow/trust/installer/unknown changes, injection signals, unknown inputs, and test changes after a failure. An escalation can increase verification, never reduce it.

The local policy does not claim external CI execution, provider identity, release publication, or adopter installation evidence. Those remain separate evidence boundaries.
