---
author: Ray
title: "Quality Critical Path HCI Performance V2 Implementation Plan"
description: "Test-first implementation plan for source-bound measurements and fail-closed quality shards."
keywords:
  - quality
  - performance
  - implementation-plan
---

# Quality Critical Path HCI Performance V2 Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver source-bound performance evidence, safe parallel project-test execution, and 30-second quality feedback without weakening verification.

**Architecture:** A manifest owns the complete test set; per-shard receipts are validated by an aggregate; a measurement module validates sample comparability and percentiles. The existing quality runner remains the single streaming evidence producer and gains structured progress/context metadata.

**Tech Stack:** Python standard library, pytest, GNU Make, GitHub Actions, coverage.py, JUnit XML.

## Global Constraints

- Preserve every existing test and coverage >=85.10%.
- Never use SKIP_QUALITY, cache-only validation, or a green outcome for incomplete samples.
- Keep `project-test` serial and equivalent to the aggregate manifest.
- Baseline and candidate require five sequential same-SHA/tree runner-class Hosted samples each.
- Do not edit v0.5.50 release/version artifacts.

---

### Task 1: Measurement model

**Files:** Create `scripts/quality_measurements.py`, `tests/test_quality_measurements.py`.

**Interfaces:** `validate_samples(samples, expected_kind)` returns normalized samples or raises `MeasurementError`; `percentiles(values)` returns nearest-rank p50/p95.

- [ ] Write failing tests for five comparable samples, a wrong SHA, a cancelled sample, and nearest-rank values.
- [ ] Run `pytest tests/test_quality_measurements.py -q` and observe missing-module failure.
- [ ] Implement parsing, identity equality, successful-result validation, and percentile calculation.
- [ ] Re-run `pytest tests/test_quality_measurements.py -q`.

### Task 2: Complete test manifest

**Files:** Create `scripts/quality_test_manifest.py`, `tests/test_quality_test_manifest.py`; modify `Makefile`.

**Interfaces:** `build_manifest(root)` returns immutable pytest and command entries; `assign_shards(manifest, durations)` returns exactly-one shard ownership; `validate_aggregate(receipts, manifest, source)` raises on mutations.

- [ ] Write failing manifest/ownership/missing-artifact/wrong-SHA tests.
- [ ] Run the focused test and observe missing-module failure.
- [ ] Implement deterministic manifest, historical-duration assignment and fail-closed aggregate validation.
- [ ] Add serial and shard Make entrypoints using isolated output roots; re-run focused tests.

### Task 3: Evidence and HCI output

**Files:** Modify `scripts/run_quality_gate.py`, `scripts/summarize_quality_gates.py`, `scripts/run_quality_session.py`; create `scripts/quality_progress.py`; modify `tests/test_quality_telemetry.py`, create `tests/test_quality_progress.py`.

- [ ] Write failing tests for 30-second progress rendering and required identity/test/coverage fields.
- [ ] Run focused tests and observe the intended failures.
- [ ] Add progress coordinator and source/environment metadata while preserving failure, timeout and cancellation result semantics.
- [ ] Re-run focused telemetry tests.

### Task 4: Hosted shard workflow and fixture isolation

**Files:** Modify `.github/workflows/smoke.yml`, `Makefile`, `tests/test_workflows.py`, `tests/test_makefile.py`.

- [ ] Write failing assertions for independent shard jobs, per-shard artifacts, aggregate `always()` execution, 30-second heartbeat, and receipt consumption.
- [ ] Run focused tests and observe failures.
- [ ] Implement shard jobs/aggregate validation and immutable fixture cache keys without changing release semantics.
- [ ] Re-run focused workflow and Makefile tests.

### Task 5: Documentation, full verification and Hosted evidence

**Files:** Modify three quality-gate operation documents, documentation registry and capability matrix; active Summary.

- [ ] Describe commands, receipt authority boundary, HCI messages and diagnosis.
- [ ] Run documentation/traceability checks.
- [ ] Run required local quality commands and snapshot preparation.
- [ ] Dispatch and retain five sequential baseline samples and five candidate samples; record all results and statistical decision in Summary.
- [ ] Finish, archive, open/merge PR, close Work Item, and verify branch cleanup.

## Self-Review

Every Contract acceptance item maps to Tasks 1–5. The plan has no placeholder implementation steps; task interfaces are defined before consumers. Tests precede production changes in Tasks 1–4.
