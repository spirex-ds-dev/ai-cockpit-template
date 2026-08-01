---
author: Ray
title: "WI06 Capability Claim Binding Implementation Plan"
description: "TDD plan for source-bound multilingual public capability claims."
audience: maintainers
status: current
authority: supporting
lastVerifiedBy: wi-06-capability-claim-binding
---

# WI06 Capability Claim Binding Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Require current public capability claims to identify fresh,
state-compatible rows in the existing Capability Truth matrix.

**Architecture:** `ai_check_capability_claims.py` selects README and canonical
current Markdown, parses YAML and inline bindings, delegates matrix validity and
freshness to `ai_capability_truth`, applies lexical state qualifiers, and checks
multilingual binding parity. `check-docs-metadata` composes the checker.

**Tech Stack:** Python 3.11+, standard library, pytest, Markdown/YAML-like front
matter, JSON Capability Truth matrix.

### Task 1: Executable binding policy

**Files:**
- Create: `tests/test_capability_claims.py`
- Create: `scripts/ai_check_capability_claims.py`

- [ ] Write failing tests for YAML and inline bindings, unbound claim terms,
  unknown IDs, exact evidence freshness, state qualifiers, exclusions, and
  multilingual sibling parity.
- [ ] Run `.venv/bin/pytest -q tests/test_capability_claims.py` and confirm the
  absent checker fails.
- [ ] Implement the smallest parser and validator that reuses
  `validate_matrix`, `build_evidence_source`, and `capability_state`.
- [ ] Run the focused test file until green.

### Task 2: Current documentation migration

**Files:**
- Create: `docs/reference/capability-claim-authoring.md`
- Modify: current README, concept, getting-started, operations, reference, and
  security documents declared by the Contract
- Modify: `docs/reference/capability-truth-matrix.json`
- Modify: `docs/reference/capability-truth-matrix.md`

- [ ] Add exact capability bindings to every current document with configured
  claim terms, keeping multilingual sibling sets equal.
- [ ] Add an implemented `capability_claim_binding` matrix row backed by the
  checker, tests, and authoring guide, then regenerate exact evidence digests.
- [ ] Document both syntaxes, state rules, exclusions, qualifiers, freshness,
  multilingual parity, and remediation.
- [ ] Run the checker against the repository and repair only real violations.

### Task 3: Existing-check integration and finish

**Files:**
- Modify: `Makefile`
- Modify: `tests/test_makefile.py`
- Modify: generated documentation assessment evidence declared by the Contract

- [ ] Add a `check-capability-claims` helper target and invoke it from
  `check-docs-metadata` without adding a check registry entry.
- [ ] Prove Make composition with a focused structural test.
- [ ] Refresh derived documentation assessments through their generators.
- [ ] Run focused tests, `make check-docs-metadata`, and the Contract-selected
  Standard finish route; record all results in the Summary.
