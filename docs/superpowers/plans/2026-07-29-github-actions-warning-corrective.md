---
author: Ray
title: "GitHub Actions Warning Corrective"
description: Remove the diagnosed Node runtime, Go cache, and Homebrew tap warnings before release.
---

# GitHub Actions Warning Corrective

## Instruction

Before release, remove the reported GitHub Actions warnings and receive the open Dependabot pull requests. This Work Item owns `CI-WARN-001` and the overlapping `actions/upload-artifact` update from Dependabot PR #443. PRs #441, #442, #444, and #445 remain separate later Work Items.

## Plan

1. Pin `actions/upload-artifact` v7.0.1 by its immutable upstream tag commit.
2. Disable setup-go dependency caching in both jobs that create their `go.mod` only later inside a disposable fixture.
3. Before both Swift Homebrew operations, conditionally remove only the unrelated `aws/tap`.
4. Add workflow regressions for every required marker and for prohibited fake manifests, broad trust, and warning-suppression approaches.
5. Run focused tests, fast and full quality, archive, PR, exact-Head Hosted checks, merge, lifecycle closure, branch deletion, worktree cleanup, and main synchronization.
6. Inspect exact-Head Hosted logs for the three original warning signatures. A green job without log inspection is not acceptance.
7. After merge, close Dependabot PR #443 as superseded by the governed replacement. Do not alter the other dependency PRs in this Work Item.

## Instruction → Plan → Implementation → Acceptance

| Requirement | Plan | Implementation | Acceptance |
| --- | --- | --- | --- |
| Remove Node.js 20 artifact warning | Step 1 | `.github/workflows/smoke.yml` | A1, A4, A6 |
| Remove false Go cache warnings | Step 2 | `.github/workflows/compatibility.yml` | A2, A4, A6 |
| Remove untrusted `aws/tap` warning without weakening trust | Step 3 | `.github/workflows/compatibility.yml` | A3, A4, A6 |
| Prevent recurrence | Step 4 | `tests/test_quality_gate_architecture.py`, `tests/test_workflows.py` | A4, A5 |
| Receive Dependabot #443 safely | Steps 1 and 7 | governed replacement PR and provider closure record | A1, A9 |
| Preserve complete lifecycle and traceability | Steps 5–7 | Contract, Summary, archive, PR and closure evidence | A5, A7–A9 |

The reverse Acceptance → Implementation → Plan → Instruction check must resolve every row before `ai-finish`. Any missing mapping blocks merge and release.

## Prohibited shortcuts

- Do not add a repository-root `go.mod` only to satisfy setup-go caching.
- Do not set `HOMEBREW_NO_REQUIRE_TAP_TRUST`.
- Do not trust all of `aws/tap`.
- Do not ignore an untap failure with `|| true`.
- Do not replace exact-Head Hosted log evidence with local YAML parsing.
- Do not merge unrelated Dependabot updates into this Work Item.

## Current state

Implementation is in progress. Red-first workflow tests reproduced all three missing protections; the narrow workflow corrections now pass the focused tests. Full governance, Hosted warning absence, merge, closure, and #443 provider cleanup remain pending.
