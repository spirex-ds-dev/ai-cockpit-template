---
author: Ray
title: "Review Remediation Loop Implementation Plan"
description: "按验收问题循环执行修复、验证、归档和本地提交的计划。"
keywords:
  - review
  - remediation
  - work-items
  - release
---

# Review Remediation Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Each task ends with verification, archive, and a local commit.

**Goal:** Resolve the current NO-GO blockers without weakening historical archive compatibility, release provenance, secret redaction, documentation correctness, or archive ownership determinism.

**Architecture:** Separate historical-evidence compatibility from strict validation of newly created v2 Work Items. Treat release tag contents as the immutable source of release evidence, centralize private-key redaction, make documentation examples executable, and replace timestamp/path ownership heuristics with explicit archive ordering evidence.

**Tech Stack:** Python 3.11/3.14, Make, pytest, Ruff, Mypy, Bandit, JSON/JSONL governance artifacts, Git tags.

## Global Constraints

- Historical archive evidence is append-only and remains readable without rewriting.
- New v2 archive evidence remains strict and fail-closed.
- Release metadata, tag contents, SBOM, provenance, lock files, and installer summaries form one immutable release unit.
- No secrets, machine paths, or credentials may enter repository evidence.
- Every task uses a v2 Work Item Contract, Summary, required checks, archive, and local commit; no push.

### Task 1: PR Archive Legacy Compatibility

**Files:** `scripts/ai_check_summary.py`, `scripts/ai_check_pr.py`, `tests/test_pr_aggregate.py`, `tests/test_ai_check_summary.py`

- Add failing fixtures for legacy archive summaries without `summaryVersion: 2` and without `worktreeDigest`.
- Add strict fixtures proving newly added v2 pairs still require v2 fields and evidence.
- Implement an explicit historical-archive compatibility path keyed by immutable archive context, not by suppressing validation globally.
- Run the target-base PR check and the full Python test suite.

### Task 2: Release Evidence and Tag Consistency

**Files:** `scripts/check_release_distribution.py`, release metadata/tests, release documentation

- Add a failing test where the worktree has evidence absent from the inspected tag.
- Make the checker inspect lock, SBOM, provenance, and release metadata from the target tag itself.
- Rebuild the release evidence as one immutable unit and verify anonymous installation/distribution checks.

### Task 3: Complete Private-Key Redaction

**Files:** `scripts/ai_common.py`, redaction tests

- Add truncation fixtures for generic, RSA, and OpenSSH private-key headers.
- Implement one header-family matcher that redacts until a matching footer or end-of-input.
- Verify Summary output contains no private-key body fragments.

### Task 4: Documentation and E2E Contract Alignment

**Files:** `README.md`, `docs/getting-started/installation.md`, `docs/reference/upgrade.md`, documentation tests

- Add executable tests for custom public repository propagation, status command output, semver downgrade rejection, and multilingual setup consistency.
- Correct implementation or documentation where behavior is wrong, then rerun five-dimensional documentation review.

### Task 5: Archive Ownership Ordering

**Files:** `scripts/ai_check_pr.py`, archive Contract/Summary schema, ownership tests

- Add same-second multi-archive fixtures that demonstrate timestamp/path ordering is insufficient.
- Add a monotonic archive sequence or explicit dependency edge to the evidence model.
- Resolve overlapping ownership using that verifiable ordering and reject missing/ambiguous ordering evidence.

### Task 6: Final GO/NO-GO Evidence Pack

**Files:** final evidence Summary and release artifacts

- Run Python 3.11 and 3.14 tests, quality gates, target-base PR gate, release distribution, documentation E2E, anonymous install/upgrade/rollback, SBOM/provenance/lock verification.
- Bind every result to the commit and immutable release tag.
- Mark GO only when all blocking checks are zero; otherwise preserve NO-GO with an owner and follow-up Work Item.
