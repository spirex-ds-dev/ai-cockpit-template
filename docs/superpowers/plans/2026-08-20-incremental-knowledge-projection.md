---
author: Ray
title: "Incremental Knowledge Projection Implementation Plan"
description: "Implementation plan for dependency-aware Knowledge Projection refreshes."
audience:
  - maintainer
  - reviewer
authority: supporting
keywords:
  - ai-cockpit
  - implementation-knowledge
  - incremental-projection
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# Incremental Knowledge Projection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ordinary all-record Knowledge Projection refreshes with dependency-aware incremental refreshes while preserving Evidence binding and fail-closed recovery.

**Architecture:** Add a generated reverse dependency projection beside the query index. New or affected Records update only their own serialized entries; a missing or invalid dependency projection takes an explicit full rebuild or fails closed. Finish and Archive pass known changed paths into the canonical generator.

**Tech Stack:** Python standard library, JSON schemas, pytest, Make-based AI Cockpit lifecycle.

**Spec:** `docs/superpowers/specs/2026-08-20-incremental-knowledge-projection-design.md`

## Global Constraints

- Contract, Summary, Outcome, repository Evidence, and explicit lifecycle facts remain authoritative.
- The normal path adds no database, cache server, daemon, vector store, embedding, semantic ranking, or LLM dependency.
- Missing or unverifiable dependency state must trigger explicit full validation/rebuild or fail closed; never silently reuse a projection.
- Archived Contract, Summary, Outcome, archive manifest, and archive index evidence is immutable.
- Query filters, supersession semantics, unknown preservation, and fresh-adopter parity remain unchanged.

---

### Task 1: Add the selective-refresh regression test

**Files:**
- Modify: `tests/test_implementation_knowledge.py`
- Test: `tests/test_implementation_knowledge.py`

**Interfaces:**
- Consumes: current `build_record()` and `rebuild_existing_projections()` fixture helpers.
- Produces: a failing test that requires `changed_paths` routing and proves an unrelated Record is not rebuilt.

- [x] **Step 1: Write the failing test**

Add a fixture with two archived Records, one depending on `tests/shared.py` and
one depending on `tests/unrelated.py`. Call
`rebuild_existing_projections(repo_root=tmp_path, changed_paths=["tests/shared.py"])`,
wrap the canonical Record builder only to count calls, and assert that the
affected Work Item is rebuilt while the unrelated Work Item is not visited.

- [x] **Step 2: Run the test to verify it fails**

Run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_implementation_knowledge.py -k selective_refresh
```

Expected: FAIL because the current refresher has no changed-path dependency
routing and still rebuilds every existing Record.

- [x] **Step 3: Commit the test-only red state**

Do not commit a red branch; retain the failing test in the working tree while
implementing the minimum production behavior in Task 2.

### Task 2: Implement dependency and query-index incremental updates

**Files:**
- Create: `.ai/schemas/implementation-knowledge-dependency-index.schema.json`
- Modify: `scripts/ai_generate_knowledge_record.py`
- Modify: `scripts/ai_check_knowledge_index.py`
- Test: `tests/test_implementation_knowledge.py`

**Interfaces:**
- Consumes: the red selective-refresh test and existing Record `generatedFrom`/`evidence` fields.
- Produces: `dependency_paths()`, incremental index updates, dependency-index validation, and explicit full fallback.

- [x] **Step 1: Add the schema and pure dependency extraction test**

Define schema version 1 with `records` and `byPath` objects. Test sorted,
de-duplicated dependencies from Contract/Summary/Outcome and Evidence paths.

- [x] **Step 2: Implement the minimal dependency index**

Add normalized dependency extraction, atomic load/write helpers, reverse lookup,
and update operations. Keep full deterministic rebuild available for recovery.

- [x] **Step 3: Implement selective `rebuild_existing_projections()`**

Add keyword-only `changed_paths` and `include_work_item_ids`. Use the valid
reverse mapping to select affected IDs; rebuild only those archived sources;
update only changed Record/index/dependency bytes. If the dependency projection
is unavailable or invalid, perform the explicit full rebuild path.

- [x] **Step 4: Run the focused test to verify it passes**

Run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_implementation_knowledge.py -k 'selective_refresh or dependency'
```

Expected: PASS, including the original stale-evidence and legacy partial tests.

### Task 3: Integrate Finish and Archive lifecycle callers

**Files:**
- Modify: `scripts/ai_finish.py`
- Modify: `scripts/ai_archive_work_item.py`
- Test: `tests/test_task_outcome_ai_finish_integration.py`
- Test: `tests/test_ai_archive_work_item.py`

**Interfaces:**
- Consumes: incremental generator APIs from Task 2.
- Produces: lifecycle calls that pass changed generated paths and explicitly include the current archived Record.

- [x] **Step 1: Add failing integration assertions**

Assert that Finish passes the source-bound output paths to the refresher and
that Archive includes only the current Record when no shared path changed.

- [x] **Step 2: Run the integration tests to verify the red state**

Run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_task_outcome_ai_finish_integration.py tests/test_ai_archive_work_item.py -k knowledge
```

Expected: FAIL because callers currently invoke the all-record refresher with
no changed-path or current-Record boundary.

- [x] **Step 3: Pass changed paths and current IDs**

Accumulate the generated source-bound output paths in Finish and call the
incremental refresher with them. In Archive call the generator with an empty
changed-path set and the just-created Work Item ID. Preserve the existing
fail-closed checker calls.

- [x] **Step 4: Run lifecycle tests to verify green**

Run the same focused command and confirm all selected tests pass.

### Task 4: Add benchmark and installer/parity coverage

**Files:**
- Create: `scripts/ai_knowledge_projection_benchmark.py`
- Create: `tests/test_knowledge_projection_benchmark.py`
- Modify: `tests/test_knowledge_installer_parity.py`

**Interfaces:**
- Consumes: dependency routing APIs from Task 2.
- Produces: reproducible local JSON benchmark for 1,000 and 10,000 synthetic Records and fresh-adopter schema parity.

- [x] **Step 1: Add the benchmark test**

Test that synthetic dependency maps of 1,000 and 10,000 Records route an
unrelated changed path to zero affected IDs without iterating Record payloads.

- [x] **Step 2: Run the benchmark test to verify it fails**

Run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_knowledge_projection_benchmark.py
```

Expected: FAIL until the benchmark module and dependency routing helper exist.

- [x] **Step 3: Implement the benchmark command**

Generate only temporary synthetic JSON mappings, measure each requested size,
record affected count and operation counters, and write the requested JSON
artifact under `target/` without touching repository Knowledge data.

- [x] **Step 4: Verify fresh-adopter parity**

Extend the existing parity fixture to assert the dependency-index schema and
benchmark entrypoint are delivered/usable without pre-populated Records.

- [x] **Step 5: Run both tests and the benchmark command**

Run the focused benchmark/parity tests and:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/ai_knowledge_projection_benchmark.py --records 1000 10000 --output target/knowledge-projection-benchmark.json
```

### Task 5: Document the design and behavior boundary

**Files:**
- Create: `docs/superpowers/specs/2026-08-20-incremental-knowledge-projection-design.md`
- Modify: `docs/reference/implementation-knowledge.md`
- Test: existing documentation metadata and link checks.

**Interfaces:**
- Consumes: verified generator/lifecycle behavior from Tasks 2–4.
- Produces: maintainer-facing dependency-index contract, fallback semantics,
  and unchanged query/no-RAG boundary.

- [x] **Step 1: Add the design document and update reference documentation**

Document the JSON projection, changed-path flow, full-validation fallback,
failure semantics, and command boundaries without claiming a performance SLO.

- [x] **Step 2: Run documentation checks**

Run:

```sh
make check-docs-metadata
```

Record any pre-existing Capability Truth freshness issue separately from this
Work Item; do not weaken the checker.

### Task 6: Execute final verification and governed handoff

**Files:**
- Modify: `.ai/work-items/active/incremental-knowledge-projection-20260820.summary.json`
- Generated: `.ai/cockpit/current_status.md`, task reports, archive bundle, Knowledge projections, and verification artifacts.

**Interfaces:**
- Consumes: all implementation and test evidence from Tasks 1–5.
- Produces: complete Summary, Outcome, archive bundle, PR-ready diff, and
  independent review evidence.

- [ ] **Step 1: Run focused tests and project tests**

Run the changed tests first, then the full `pytest -q` suite and benchmark.

- [ ] **Step 2: Run required AI Cockpit checks**

Run the Contract-declared checks, `make ai-checkpoint ... STAGE=before_finish`,
`make ai-finish TASK=incremental-knowledge-projection-20260820`, and verify
the generated Summary/Outcome contain exact command results.

- [ ] **Step 3: Run independent code review**

Review the committed diff against base `8030234f` and fix all Critical or
Important findings before PR creation.

- [ ] **Step 4: Archive, push, open one PR, and merge**

Commit only scoped paths, run `make check-ai-pr AI_BASE_COMMIT=8030234f`, push
the dedicated branch, wait for required hosted checks, and merge without
provider-side branch deletion.

- [ ] **Step 5: Close the Work Item**

Run `make ai-close-work-item TASK=incremental-knowledge-projection-20260820`
and require archived evidence, exact merged-head ownership, synchronized base,
remote branch absence, and a clean closure result before release work begins.
