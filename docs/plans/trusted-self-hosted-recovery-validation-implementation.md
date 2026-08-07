---
author: Codex
title: "Trusted Self-hosted Recovery Validation Implementation Plan"
description: "Test-first replacement plan for a temporary self-hosted recovery diagnostic."
keywords:
  - ai-cockpit
  - self-hosted-runner
  - ci
  - verification
---

# Trusted Self-hosted Recovery Validation Implementation Plan

## Bootstrap finding

The first design introduced a standalone `self-hosted-recovery.yml` workflow.
GitHub rejected its dispatch with `404 workflow ... not found on the default
branch`: a workflow must already be registered on the default branch before
the provider exposes it to `workflow_dispatch`. That design cannot unblock the
current outage and is removed rather than retained as dead code.

## Approved replacement

1. Add default-off boolean `recovery_diagnostic` to the existing,
   default-branch-registered `compatibility.yml` `workflow_dispatch` inputs.
2. Add one isolated job conditional on both `workflow_dispatch` and that input.
   It runs only on `[self-hosted, macOS, X64, ai-cockpit-recovery]`, checks out
   and verifies only PR #723 candidate
   `365f5e30c9531d8d8948079fe58b8424ecc9efa7`, runs its
   `make compatibility-test`, and
   writes an explicit temporary-runner-substitution red/green summary.
3. Do not change any existing compatibility job, `push`, `pull_request`,
   required-check, smoke, or release behavior. Manual compatibility dispatch
   still starts its normal jobs; the diagnostic job is independent and has no
   `needs` dependency.
4. Remove the obsolete standalone workflow and all documents that reference
   it. Refresh supply-chain and generated documentation evidence.
5. After a clean candidate snapshot, push only for diagnostic validation and
   dispatch:

   ```bash
   gh workflow run compatibility.yml \
     --ref codex/trusted-self-hosted-recovery-validation-724 \
     -f recovery_diagnostic=true
   ```

6. Record the run URL, workflow-definition SHA, exact PR #723 SHA, and outcome
   as temporary runner-substitution evidence only.
   After official Actions recovery, rerun normal hosted smoke and compatibility
   before any merge or release decision. Remove this job through a separate
   governed Work Item once recovery is stable.

## Test-first evidence

- The topology test first failed because `compatibility.yml` had no
  `recovery_diagnostic` input or self-hosted job.
- The implementation must make the test pass while preserving the existing
  compatibility workflow regression suite.
- `make quality` and the hosted snapshot are required before pushing a
  measurement candidate.
