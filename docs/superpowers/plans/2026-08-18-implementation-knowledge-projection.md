---
author: Ray
title: "Implementation Knowledge Projection Implementation Plan"
description: "Test-first plan for evidence-bound implementation knowledge records, deterministic indexing, lifecycle validation, and adopter parity."
keywords:
  - implementation-knowledge
  - work-item-lifecycle
  - evidence-binding
  - adopter-parity
---

# Implementation Knowledge Projection Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic, evidence-bound projection from archived Work Item Contract/Summary/Outcome into rebuildable Implementation Knowledge Records and a lightweight index, with stale detection and fresh-adopter parity.

**Architecture:** `ai_generate_knowledge_record.py` reads the authoritative Contract, Summary, Outcome, and repository evidence and writes one record plus a deterministic index. `ai_check_knowledge_index.py` validates schemas, source digests, evidence paths, identity bindings, and Summary/Outcome agreement without rewriting authoritative archives. The installer catalog, adopter capability manifest, Make targets, and fresh-adopter tests expose exactly the same runtime surface.

**Tech Stack:** Python 3.11+, JSON Schema, existing Make-based AI Cockpit runtime, pytest, installer catalog/manifest parity checks.

**Spec:** `user-request:implementation-knowledge-projection-20260818#Implementation Knowledge Projection` (the user-provided requirements pasted in this task)

## Global Constraints

- Contract, Summary, Evidence, Outcome, and Git merge identity remain the authoritative fact sources; Knowledge Records are rebuildable projections only.
- Missing historical Implementation Approach, Design Reason, current validity, or supersession relation remains `unknown`/`partial`; no AI backfill or semantic code validation is allowed.
- Verified claims require existing repository-relative evidence paths; declared evidence digests must match current bytes; stale or contradictory inputs cannot remain `verified`.
- The first version is deterministic and machine-readable; semantic search, embeddings, LLM ranking, and customer-answer generation are out of scope.
- Installed adopter capability must be proven by a fresh-adopter fixture, not inferred from template files or catalog declarations.

---

### Task 1: Define the record/index schemas and failing projection tests

**Files:**
- Create: `.ai/schemas/implementation-knowledge-record.schema.json`
- Create: `.ai/schemas/implementation-knowledge-index.schema.json`
- Create: `tests/test_implementation_knowledge.py`

**Interfaces:**
- The record schema accepts `schemaVersion`, `workItemId`, `title`, `topics`, `components`, `implementation`, optional `configuration`, `changes`, `designDecisions`, `effects`, `evidence`, `mergedCommit`, `currentValidity`, `supersedes`, `generatedFrom`, and `knowledgeState`.
- `knowledgeState` is exactly `verified`, `partial`, `unknown`, or `superseded`; implementation/design statuses are `verified`, `unknown`, or `incomplete`.
- The index schema accepts only `schemaVersion` and sorted lightweight `workItems` entries containing `workItemId`, `title`, `topics`, `components`, `state`, and `knowledgePath`.

- [ ] **Step 1: Write failing fixtures for a verified code Work Item, a legacy partial Work Item, and a stale/mismatched source.**

  Build temporary repository-relative Contract/Summary/Outcome/evidence files. Assert the public generator API will return a verified record for matching sources, partial/unknown for missing approach, and non-verified for missing evidence, identity mismatch, Summary/Outcome mismatch, or changed source digest.

- [ ] **Step 2: Run the focused tests and verify they fail for missing production entrypoints.**

  Run: `pytest -q tests/test_implementation_knowledge.py`

  Expected: collection or assertion failure because `scripts.ai_generate_knowledge_record` and the schema files do not exist yet.

- [ ] **Step 3: Add the two JSON Schemas with closed field sets and enum states.**

  Reject additional top-level fields, require repository-relative evidence paths, require `generatedFrom.summaryDigest` and `generatedFrom.outcomeDigest`, and exclude any query/semantic-ranking fields from the index.

- [ ] **Step 4: Run schema-focused tests and keep the behavioral tests red.**

  Run: `pytest -q tests/test_implementation_knowledge.py -k schema`

  Expected: schema tests pass while generator behavior tests remain red until Task 2.

- [ ] **Step 5: Commit the schemas and red tests.**

  Run:

  ```bash
  git add .ai/schemas/implementation-knowledge-record.schema.json .ai/schemas/implementation-knowledge-index.schema.json tests/test_implementation_knowledge.py
  git commit -m "test: define implementation knowledge projection contract"
  ```

### Task 2: Implement evidence-bound record generation and deterministic index rebuild

**Files:**
- Create: `scripts/ai_generate_knowledge_record.py`
- Modify: `tests/test_implementation_knowledge.py`
- Create: `.ai/knowledge/work-items/.gitkeep` only if the repository requires an empty generated-artifact directory

**Interfaces:**
- `build_record(contract_path: Path, summary_path: Path, outcome_path: Path, repo_root: Path) -> dict[str, Any]` returns one record without writing files.
- `rebuild_index(records_dir: Path, output_path: Path) -> dict[str, Any]` reads only record JSON files, sorts by `workItemId`, and writes the lightweight index atomically.
- CLI: `python scripts/ai_generate_knowledge_record.py --contract <path> --summary <path> --outcome <path> --output <record> --index <index>`.
- A legacy input without approach returns `knowledgeState: partial`, `implementation.status: unknown`, and no invented design decisions.
- A verified state is possible only after identity, evidence path, declared evidence digest, and Summary/Outcome consistency checks pass.

- [ ] **Step 1: Implement file hashing, normalized JSON loading, and repository-relative path validation.**

  Compute SHA-256 digests for Summary and Outcome bytes for `generatedFrom`; reject absolute paths, traversal, missing files, and non-repository evidence for verified claims.

- [ ] **Step 2: Implement Summary/Outcome projection with explicit unknowns.**

  Copy existing `implementationApproach`/`configurationApproach`, `designDecisions`, `actualChanges`/`changedFiles`, and evidence paths. Compare the Summary approach with Outcome `sections.implementationApproach`; any disagreement becomes a structured consistency issue and prevents `verified`.

- [ ] **Step 3: Implement state calculation and optional explicit supersession.**

  Set `verified` only when all required evidence checks pass; use `partial` when facts are present but incomplete or stale; use `unknown` when no usable approach/evidence exists; use `superseded` only when the source explicitly declares `supersedes`.

- [ ] **Step 4: Implement atomic record/index writes and deterministic ordering.**

  Never edit Contract/Summary/Outcome. Write the record to `.ai/knowledge/work-items/<id>.json` (or the explicit `--output`) and rebuild `.ai/knowledge/index.json` from records only.

- [ ] **Step 5: Run the focused tests and verify green.**

  Run: `pytest -q tests/test_implementation_knowledge.py`

  Expected: verified, legacy partial, negative evidence, stale digest, identity mismatch, Summary/Outcome mismatch, supersession, and deterministic index tests pass.

- [ ] **Step 6: Commit the generator.**

  Run: `git add scripts/ai_generate_knowledge_record.py tests/test_implementation_knowledge.py && git commit -m "feat: project evidence-bound implementation knowledge"`

### Task 3: Implement stale/index checker and Make targets

**Files:**
- Create: `scripts/ai_check_knowledge_index.py`
- Modify: `Makefile`
- Modify: `templates/make/Makefile.ai`
- Modify: `tests/test_implementation_knowledge.py`

**Interfaces:**
- `check_record(record_path: Path, repo_root: Path) -> list[str]` returns fail-closed issues for schema, source digest, evidence, identity, consistency, or invalid state.
- `check_index(index_path: Path, records_dir: Path, repo_root: Path) -> list[str]` validates every indexed record and deterministic index projection.
- CLI: `python scripts/ai_check_knowledge_index.py --index .ai/knowledge/index.json --records .ai/knowledge/work-items` exits nonzero on stale or invalid data.
- Make targets: `ai-generate-knowledge-record` delegates to the generator; `ai-check-knowledge-index` delegates to the checker; neither target performs semantic search or repository mutation beyond declared generated outputs.

- [ ] **Step 1: Write failing checker and Make target tests.**

  Mutate a Summary after record generation, remove an evidence file, alter a record identity, and add an index-only record. Assert the checker exits nonzero and identifies the exact stale/mismatch reason.

- [ ] **Step 2: Implement schema validation and source-digest checks.**

  Validate the record and index JSON against their schemas, recompute `generatedFrom` digests, and verify every evidence path/digest before allowing `verified`.

- [ ] **Step 3: Implement index completeness and deterministic rebuild comparison.**

  Rebuild an in-memory expected index and compare canonical JSON bytes/objects. Reject missing, extra, duplicate, or semantically enriched index entries.

- [ ] **Step 4: Add Make targets in both template and root Makefile surfaces.**

  Keep target names and defaults identical so the installed adopter can invoke the same commands. Do not add a query target in this WI.

- [ ] **Step 5: Run focused checker tests and commit.**

  Run: `pytest -q tests/test_implementation_knowledge.py`

  Commit: `git add scripts/ai_check_knowledge_index.py Makefile templates/make/Makefile.ai tests/test_implementation_knowledge.py && git commit -m "feat: add knowledge projection stale checks"`

### Task 4: Deliver the adopter-facing installer surface and fresh-adopter parity

**Files:**
- Modify: `scripts/ai_installer_catalog.json`
- Modify: `.ai/project/adopter-capability-manifest.json`
- Create: `tests/test_knowledge_installer_parity.py`
- Modify: `tests/test_installed_runtime_parity.py` if the existing parity registry is the canonical test surface

**Interfaces:**
- Installer scripts: `ai_generate_knowledge_record.py`, `ai_check_knowledge_index.py`.
- Installer schemas: `implementation-knowledge-record.schema.json`, `implementation-knowledge-index.schema.json`.
- Capability id: `implementation_knowledge_projection`, marked adopter-facing and requiring installed-surface verification.
- The parity fixture installs a fresh empty adopter, asserts files and Make targets exist, and runs both entrypoints against temporary fixture evidence.

- [ ] **Step 1: Add a failing fresh-adopter parity test.**

  Create an empty adopter fixture through the existing installer helper and assert the two scripts, two schemas, Make targets, and capability manifest entry exist; run the installed checker.

- [ ] **Step 2: Add the scripts/schemas/Make targets to the installer catalog.**

  Use the existing catalog path/ownership conventions and ensure the installed copies are the same bytes as the template sources.

- [ ] **Step 3: Add the capability manifest entry and parity binding.**

  Bind the capability to both scripts, both schemas, both Make targets, and the fresh-adopter parity test. Do not mark it adopter-installed without the test evidence.

- [ ] **Step 4: Run parity and installer tests, then commit.**

  Run: `pytest -q tests/test_knowledge_installer_parity.py tests/test_installed_runtime_parity.py`

  Commit: `git add scripts/ai_installer_catalog.json .ai/project/adopter-capability-manifest.json tests/test_knowledge_installer_parity.py tests/test_installed_runtime_parity.py && git commit -m "feat: install implementation knowledge projection"`

### Task 5: Document the authority boundary and run the complete WI verification

**Files:**
- Create: `docs/reference/implementation-knowledge.md`
- Modify: `.ai/work-items/active/implementation-knowledge-projection-20260818.summary.json`
- Generated: `.ai/knowledge/**` only through the generator command and evidence-bound fixture inputs

**Interfaces:**
- Documentation must state record/index paths, CLI/Make usage, fields, status model, digest/stale behavior, legacy partial behavior, and explicit exclusions.
- Summary must record the implementation approach, design decisions, evidence-bound paths, and verification results before `ai-finish`.

- [ ] **Step 1: Write the documentation and document the external-Agent boundary.**

  Explain that Core returns structured records only; an external Agent may turn the same evidence into customer or engineering prose.

- [ ] **Step 2: Generate only the declared Knowledge artifacts and verify the checker.**

  Run the generator against the focused archived fixtures, rebuild the index, and run `make ai-check-knowledge-index`. Do not mass-backfill legacy archives by inference.

- [ ] **Step 3: Run all focused and repository governance checks.**

  Run:

  ```bash
  pytest -q tests/test_implementation_knowledge.py tests/test_knowledge_installer_parity.py tests/test_installed_runtime_parity.py
  make check-ai-contract CONTRACT=.ai/work-items/active/implementation-knowledge-projection-20260818.contract.json
  make check-ai-scope CONTRACT=.ai/work-items/active/implementation-knowledge-projection-20260818.contract.json
  make ai-checkpoint CONTRACT=.ai/work-items/active/implementation-knowledge-projection-20260818.contract.json SUMMARY=.ai/work-items/active/implementation-knowledge-projection-20260818.summary.json STAGE=before_finish
  ```

- [ ] **Step 4: Record the Summary's Implementation Approach and verification evidence.**

  Bind every verified claim to repository-relative generator/schema/test/installer paths and keep any residual risk or unsupported legacy current-validity claim explicit.

- [ ] **Step 5: Run `ai-finish`, archive, publish, merge, close, and re-audit.**

  `make ai-finish TASK=implementation-knowledge-projection-20260818 ARCHIVE=true REPORT_LANGUAGE=zh-CN`, then run `make check-ai-pr`, push, open/merge the PR without provider-side branch deletion, and finish with `make ai-close-work-item TASK=implementation-knowledge-projection-20260818`.

---

## Self-review

- Spec coverage: record generation, lightweight index, deterministic filters excluded from this WI, legacy partial, evidence/digest fail-closed, supersession preservation, immutable authority boundary, lifecycle timing, and adopter parity each have a task and test path.
- No semantic search, natural-language answer generation, current-code semantic validation, or historical AI backfill is included.
- All later tasks consume the exact CLI, schema, Make target, and capability names defined above.
