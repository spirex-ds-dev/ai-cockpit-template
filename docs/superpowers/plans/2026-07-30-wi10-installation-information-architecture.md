---
author: Ray
title: "WI-10 Installation Information Architecture Implementation Plan"
description: "Implementation plan for the beginner-first, Work Item-centered installation documentation route."
---

# WI-10 Installation Information Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development task-by-task.

**Goal:** Replace the overloaded trilingual installation manuals with a beginner-safe, Work Item-centered route map while retaining advanced governance evidence in dedicated documents.

**Architecture:** The three installation home pages become thin, aligned happy paths. Existing Release verification and Calibration Session references are linked from new reader-specific documents; tests make page size, route placement, Work Item handoff, links, and retained safety boundaries deterministic.

**Tech Stack:** Markdown, JSON documentation registry, Python documentation metadata checker, pytest.

## Global Constraints

- Do not remove a safety boundary; move advanced explanation to a linked route.
- First installation creates a calibration/configuration Work Item; an already-installed repository starts the relevant Work Item directly.
- English, Chinese, and Japanese routes have the same meaning and structure.
- Do not claim Runtime installation equals calibration completion.

---

### Task 1: Establish reader-separated route documents and metadata tests

**Files:** installation home pages, security/calibration/troubleshooting/maintenance routes, `scripts/check_docs_metadata.py`, `tests/test_docs_metadata.py`.

- [ ] Add failing tests for missing split routes, missing Work Item handoff, broken links, oversized home pages, and advanced internals leaked into home pages.
- [ ] Implement the smallest checker rules and create the named reader routes with aligned links.
- [ ] Run focused documentation tests and repair all negative mutations.

### Task 2: Rewrite the three installation home pages

**Files:** `docs/getting-started/installation.md`, `.zh-CN.md`, `.ja.md`.

- [ ] Replace lifecycle-heavy content with the shared six-stage map and six action/purpose/result/STOP sections.
- [ ] Make first installation end in a calibration Work Item and already-installed use start the required Work Item directly.
- [ ] Keep explicit Unknown/no-overwrite/no-silent-fallback/separate-approval boundaries and link advanced routes.
- [ ] Run trilingual route and rendering checks.

### Task 3: Align navigation, evidence projections, and lifecycle records

**Files:** READMEs, Documentation Architecture, registry, traceability, Capability Truth and Japanese assessment projections, Contract/Summary.

- [ ] Register the reader map and concise README entries without duplicating guide content.
- [ ] Regenerate source-bound projections after final content edits.
- [ ] Record scenario evidence, alignment, Outcome, archive, PR, Hosted CI, merge, closure, and cleanup.
