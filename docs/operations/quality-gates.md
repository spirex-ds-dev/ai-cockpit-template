---
author: Ray
title: "Quality Gate Operations"
description: Operating model, evidence, and traceability for AI Cockpit quality gates.
audience:
  - maintainer
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - risk_based_quality_routing
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

## Adopter quality configuration

The installed template always provides `make quality`; it delegates the actual
formatter, linter, and test work to the adopter-owned
`Makefile.ai.stack` variables `PROJECT_FORMAT_CHECK`, `PROJECT_LINT`, and
`PROJECT_TEST`. Configure all three with the project's commands. Missing or
empty values fail closed with the variable-specific recovery message.

Hosted snapshot preparation requires this same entrypoint. It writes no receipt
when quality fails. Recover by setting the missing variable in
`Makefile.ai.stack`, then run `make quality` followed by
`make ai-prepare-hosted-verification-snapshot CONTRACT=<active-contract>`.

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
- Hosted smoke assigns every complete `project-test` entry one owner: the
  duration-balanced `project-test-core`, `project-test-governance`,
  `project-test-installer`, `project-test-lifecycle`, and `project-test-release`
  runners. Each uploads source-bound JUnit, coverage, timing, log, and receipt
  artifacts. `template-smoke` itself is the `always()` fail-closed aggregate
  consumer: it rejects missing, cancelled, failed, stale, wrong-SHA, or
  incomplete shard evidence before it runs the remaining quality gates. Local
  `make project-test` remains the serial diagnostic equivalent.
- The release-blocking full-history secret scan has one independent owner,
  `secret-scan`, and starts alongside the project-test graph. `template-smoke`
  waits for both the successful source checkout scan and all shard evidence,
  then merges coverage and runs the remaining quality gates in that same
  runner. This removes only avoidable tail waiting, not a security
  verification.
- The adopter distribution contains runtime skeletons, policies, and required
  baselines, but not template-maintenance Work Item starts, decision history,
  or archive history. The installer prunes those trees before traversal and
  reuses an immutable per-invocation source inventory.

## Evidence and failure behavior

Each `make quality` invocation creates a fresh directory under
`target/quality/sessions/`, bound to the commit, hosted run/attempt, or a
unique local identity. `scripts/run_quality_gate.py` streams gate output while
recording one JSON timing record and one complete log per gate, including the
session/run identity, command, commit, duration, exit code, timeout or
cancellation state, cache status, output digest, and bounded tail.
The top-level invocation rebinds `current-session.txt` on exit, so a nested
dry-run or test fixture cannot become the session selected by hosted
publication. Valid Make jobserver descriptors are preserved through the
telemetry wrapper; invalid or unavailable descriptors are not forwarded.
`project-test` also writes JUnit evidence and the log contains its slowest-test
report. `scripts/summarize_quality_gates.py` writes JSON and Markdown summaries
with source and runner identity, per-gate wall time, CPU/cache facts, total
gate time, parallel efficiency, slowest gate, failures, failure tails, skips,
and the final decision.

Hosted CI uploads the complete session directory and wrapper log with
`if: always()`, so success, failure, cancellation, and timeout retain
diagnostics. Missing timing or artifact evidence is an error; a cache hit is
not final evidence.

`template-smoke` gives its remaining quality invocation a 25-minute
execution limit. `timeout` then has a finite 30-second forced-termination
grace for a descendant that ignores the initial signal. The result is a
terminal failed gate with the same heartbeat and retained diagnostics, never an
indefinite in-progress PR state. This bound is not permission to skip or
downgrade any quality gate.

Manual smoke dispatch must declare its purpose. Use
`gh workflow run smoke.yml --ref <measurement-branch> -f purpose=hosted_measurement`
for source-bound performance measurement. `release_preparation` remains the
strict default and runs release-state evidence checks; measurement dispatch
does not claim release intent.

Baseline and candidate samples are separate receipts. Each comparison requires
at least five successful, unique workflow run/attempt samples on one exact
SHA/tree and runner class; a cache hit is never verification evidence.

Hosted before/after timing is an evidence claim, not an assumption. If a WI-20
baseline or a hosted run cannot be retrieved, record a structured `not-run`
reason, run ID and limitation; do not report an improvement.

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
