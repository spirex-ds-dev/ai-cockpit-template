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
- Hosted smoke has explicit `template-smoke` (the single full-quality owner),
  `installation-smoke`, and `release-evidence` jobs. These jobs start
  independently, never invoke the full graph twice, and feed an `always()`
  terminal `ci-evidence` job that fails closed on failure, cancellation, or
  skip.
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
with wall time, total gate time, parallel efficiency, slowest gate, failures,
failure tails, skips, and the final decision.

Hosted CI uploads the complete session directory and wrapper log with
`if: always()`, so success, failure, cancellation, and timeout retain
diagnostics. Missing timing or artifact evidence is an error; a cache hit is
not final evidence.

Manual smoke dispatch must declare its purpose. Use
`gh workflow run smoke.yml --ref <measurement-branch> -f purpose=hosted_measurement`
for source-bound performance measurement. `release_preparation` remains the
strict default and runs release-state evidence checks; measurement dispatch
does not claim release intent.

## Temporary self-hosted recovery diagnostics

When GitHub reports a hosted Actions outage, a repository maintainer may use
the default-off `recovery_diagnostic` input of
`.github/workflows/compatibility.yml` for development feedback. GitHub only
discovers manually dispatched workflows that already exist on the default
branch, so this controlled job is intentionally attached to the existing
compatibility workflow rather than a standalone temporary workflow. It does
not replace hosted CI. The runner must be online and carry exactly the
standard `self-hosted`, `macOS`, and `X64` labels plus the dedicated custom
`ai-cockpit-recovery` label. Do not add hosted labels such as `ubuntu-latest`
to a macOS runner.

Dispatch the workflow from the branch containing its definition. During the
current outage it checks out only PR #723 candidate
`365f5e30c9531d8d8948079fe58b8424ecc9efa7`; it does not execute the
maintenance-branch SHA or arbitrary user-supplied code:

```bash
gh workflow run compatibility.yml \
  --ref <maintenance-branch> \
  -f recovery_diagnostic=true
```

The normal compatibility workflow also starts for this manual dispatch, while
the self-hosted job checks out and verifies the immutable PR #723 candidate,
runs `make compatibility-test` (the same lightweight compatibility command),
and emits a green or red diagnostic summary. The
self-hosted job has an explicit `workflow_dispatch && recovery_diagnostic` condition, so
it never runs for `push` or `pull_request`: public pull-request code must never
execute on a personal runner. Only a maintainer with permission to dispatch
repository workflows may use it.

Record the run URL, workflow-definition SHA, fixed PR #723 SHA, checked-out
SHA, and result in the active Work Item Summary. A green result is temporary
runner-substitution evidence only: it cannot satisfy
compatibility, merge, archive, or release gates. A red result is a failed
diagnostic and must record its failed gate and recovery condition. Neither
result authorizes a bypass.

After GitHub-hosted Actions recovers, return to the normal path and rerun the
hosted smoke and compatibility workflows for the exact candidate SHA before a
merge or release decision. Retain the recovery job only while it is needed;
remove it through a separately governed change after recovery is stable.

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
