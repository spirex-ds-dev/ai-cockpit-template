---
author: AI Cockpit maintainers
title: "Adding or Classifying a Verification Check"
description: "Maintainer guidance for checker IDs, impact domains, gate types, and skipped evidence."
keywords:
  - checker
  - verification
  - governance
---

# Adding or Classifying a Verification Check

Choose a stable checker ID and register it once in the run. Assign the narrowest impact domain: docs, project code, tests, governance/trust, dependency, installer, lifecycle, release, workflow, or unknown. Unknown paths are reviewable evidence, not permission to skip.

Use `hard` only for safety and integrity properties: secrets, dependency cycles, evidence/commit binding, unauthorized paths, trust-boundary removal, fail-closed behavior, validator failures, and release identity. Use `soft` for normal trend changes and human-review recommendations. Use `informational` for context that does not decide the gate.

When a checker is not applicable, emit `status: skipped` and a reason code. Do not omit the result or invent a stage decision in the caller. Test the checker in Task, PR, and Release contexts where it applies, and test that a hard failure cannot become Green merely because a soft warning is present.

Add dependencies to the verification DAG explicitly and keep them acyclic. The policy rejects unknown dependencies and cycles. If a checker uses cached evidence, bind the cache key to every relevant base, diff, command, tool, dependency, environment, and configuration input; missing input is a cache miss/error, never a cache hit. Escalation signals may select a stricter level or Full scope, but no checker may use efficiency as a reason to downgrade a high-risk change.
