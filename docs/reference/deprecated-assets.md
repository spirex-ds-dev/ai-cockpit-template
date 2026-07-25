---
author: Ray
title: "Deprecated Assets and Archive Hygiene"
description: "Registry and fail-closed boundaries for deprecation candidates and immutable archive evidence."
keywords:
  - ai-cockpit
  - deprecated-assets
  - archive
  - governance
---

# Deprecated Assets and Archive Hygiene

[`deprecated-assets-registry.json`](deprecated-assets-registry.json) is the
machine-readable inventory for deprecation candidates. Each entry records its
replacement, dates, references, runtime use, migration need, and reason.

Run `make check-deprecated-assets` before proposing cleanup. The check validates
references and stale dates, and it fails closed when protected archive evidence
could be treated as deletable. Passing this check does not delete anything and
does not complete the execution-plan cleanup reserved for WI-18.

Contracts, Summaries, Events, Manifests, release evidence, decision evidence,
and other historical records remain preserved. Any future deletion requires a
separate Work Item with explicit scope, recovery path, replacement evidence,
PR review, merge, and lifecycle closure.
