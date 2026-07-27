---
author: Ray
title: "Quality Gate Operations"
description: Operating model, evidence, and traceability for AI Cockpit quality gates.
keywords:
  - ai-cockpit
  - quality-gates
  - ci
  - evidence
---

# Quality Gate Operations

AI Cockpit keeps `make quality` backward-compatible: it is an alias for
`make quality-full`. The shorter local feedback path is `make quality-fast`,
and release preparation uses `make quality-release`.

## Ownership

- `quality-fast` owns formatting, lint, diff, schemas, documentation metadata,
  project-profile and status policy checks.
- `quality-full` adds the complete test, evidence, supply-chain, and project
  consistency groups. Specialized trust tests remain available as standalone
  debugging targets; they are not rerun after the full pytest owner.
- `quality-release` adds installation and release-evidence checks. Fast or
  cached results never substitute for release evidence.
- Compatibility jobs validate the interpreter/platform matrix and do not run
  the full quality graph.

## Evidence and failure behavior

`scripts/run_quality_gate.py` records one JSON timing record and one log per
gate, including the command, commit, duration, exit code, timeout state,
cache status, and output digest. `scripts/summarize_quality_gates.py` writes
JSON and Markdown summaries with wall time, total gate time, parallel
efficiency, slowest gate, failures, skips, and the final decision. Missing
timing evidence is an error; a cache hit is not final evidence.

`scripts/determine_quality_scope.py` selects Fast, Full, or Release from the
changed paths. Unknown or mixed paths default to Full. Parallel groups may
only run when their declared outputs in `.ai/quality/gates.yaml` do not
conflict.

## Traceability requirement

Every Work Item must verify both directions of the instruction → plan →
implementation → acceptance chain before PR, merge, archive, and branch
cleanup. An acceptance item without implementation evidence, or an
implemented instruction without a planned acceptance item, is an omission and
must be recorded and corrected before the Work Item proceeds.

The full lifecycle remains: Contract, implementation, verification and
Summary, PR, merge, `make ai-close-work-item`, then local and remote branch
cleanup. This document describes execution evidence; it does not claim that
AI Cockpit is a security sandbox or independently guarantees enterprise
compliance.
