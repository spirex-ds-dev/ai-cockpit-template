---
author: Ray
title: Governance Remediation Implementation Plan
description: Execution plan for the three approved governance remediation work items.
keywords:
  - governance
  - work-item
  - remediation
---

# Governance Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise measured governance coverage to at least 85% and execute two follow-up PRs that control complexity and adopter configuration without weakening template boundaries.

**Architecture:** Three isolated Work Items share one approved design. The first is test-only and establishes the coverage baseline. The second adds read-only complexity inventory and lifecycle guidance. The third strengthens adopter-facing readiness evidence while preserving generic placeholders.

**Tech Stack:** Python, pytest, coverage.py, Markdown, Make targets, AI Cockpit Work Item Contracts.

## Global Constraints

- Use the latest `origin/main` as each branch base.
- Every PR must include an archived Contract/Summary pair with `contractVersion: 2`.
- Do not lower coverage floors, delete historical archives, or replace generic template identity/security values.
- Run `make quality`, required AI checks, and `make check-ai-pr` before merging.

### Task 1: Raise coverage to 85 percent

**Files:**
- Modify: `tests/test_*.py` files selected from the coverage report.
- Include: `docs/superpowers/specs/2026-07-15-governance-remediation-design.md`.
- Include: `docs/superpowers/plans/2026-07-15-governance-remediation.md`.

- [ ] Run the coverage report and identify decision-heavy branches below the target.
- [ ] Add focused tests that exercise real failure/decision paths.
- [ ] Run `make quality` and confirm total coverage is at least `85.0%`.
- [ ] Run `make ai-finish`, archive the Work Item, run `make check-ai-pr`, push, open the PR, merge it, and delete the branch.

### Task 2: Control governance complexity and archive growth

**Files:**
- Create or modify: `scripts/` only if a read-only inventory command is required.
- Test: the matching `tests/test_*.py` file.
- Document: `docs/reference/governance-complexity.md`.

- [ ] Define inventory metrics for tracked files, Python/Markdown lines, archive Contract/Summary counts, and archive index consistency.
- [ ] Implement or expose a read-only report with stable non-zero exit behavior for malformed inventory data.
- [ ] Document quarterly review, immutable history, and criteria for future archive compaction proposals.
- [ ] Run targeted tests and `make quality`.
- [ ] Run the full Work Item/PR loop, merge the PR, and delete the branch.

### Task 3: Close adopter configuration ambiguity

**Files:**
- Modify: `docs/getting-started/installation.md`, `docs/getting-started/first-work-item.md`, and `README.md` as needed.
- Test: `tests/test_adoption_ready.py` and documentation metadata tests as needed.

- [ ] Document the exact replacement obligations for `.github/CODEOWNERS` and `SECURITY.md`.
- [ ] Keep template placeholders and verify that readiness remains fail-closed until adopters replace them.
- [ ] Add only focused tests for the documented readiness behavior.
- [ ] Run `make check-ai-adoption-ready`, `make quality`, and the full Work Item/PR loop.
- [ ] Merge the PR and delete the branch.
