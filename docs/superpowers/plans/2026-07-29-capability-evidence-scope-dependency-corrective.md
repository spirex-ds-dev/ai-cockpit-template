---
author: Ray
title: "Capability Evidence Scope Dependency Corrective Implementation Plan"
description: Fail-fast Contract ownership and regeneration checks for Capability Truth evidence dependencies.
---

# Capability Evidence Scope Dependency Corrective Implementation Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent a Work Item from reaching implementation or expensive full-quality verification when it changes byte-bound Capability Truth evidence without owning and regenerating the machine matrix.

**Architecture:** Add one focused dependency module that derives evidence-path-to-capability-row edges from `docs/reference/capability-truth-matrix.json`. Preflight consumes the graph against declared Contract scope; Scope Guard consumes the same graph against actual changed paths. The matrix remains the only inventory, and its existing validator remains the authority for evidence bytes, row digests, and capability status.

**Tech Stack:** Python 3 standard library, pytest, AI Cockpit Contract/Preflight/Scope Guard, JSON Capability Truth Matrix, Markdown documentation.

## Global Constraints

- Correct the reusable process before resuming the interrupted Japanese Work Item.
- Derive every dependency from the authoritative matrix; do not hardcode `installation.md`.
- Preserve current capability status and all existing byte-level validation.
- A repository without the Capability Truth document set receives a not-applicable dependency result rather than a template-specific false failure.
- A configured matrix with missing, malformed, escaping, symbolic-link, duplicate, or non-string evidence paths fails closed.
- One Work Item, one branch, one PR, exact-Head Hosted checks, merge, closure, and branch cleanup must complete before resume.

---

## Root-cause evidence

The paused `japanese-calibration-session-evidence-doc-corrective-20260729`
Work Item changed `docs/getting-started/installation.md`. Four Capability Truth
rows bind that file:

- `project_calibration_profile_proposal`
- `ten_stage_calibration_session`
- `interactive_installation_wizard`
- `bootstrap_wizard_lifecycle`

Its Contract did not own `docs/reference/capability-truth-matrix.json`.
Preflight, focused documentation tests, metadata checks, and `quality-fast`
passed. Full `project-test` then reported three failing tests and four stale
`evidenceSource` records after 1,486 tests passed. The existing byte gate is
correct; the missing edge is Contract- and diff-level dependency discovery.

### Task 1: Author the dependency graph and prove fail-closed parsing

**Files:**

- Create: `scripts/ai_evidence_dependencies.py`
- Create: `tests/test_evidence_dependencies.py`

**Interfaces:**

- Consumes: a repository root and `docs/reference/capability-truth-matrix.json`
- Produces: `load_capability_evidence_dependencies(root: Path) -> EvidenceDependencies | None`
- Produces: `contract_scope_dependency_issues(scope: list[str], dependencies: EvidenceDependencies) -> list[str]`
- Produces: `changed_path_dependency_issues(paths: list[str], dependencies: EvidenceDependencies) -> list[str]`

- [ ] **Step 1: Write failing parser tests**

  Create a temporary matrix with two rows sharing one evidence path. Assert the
  loader returns one sorted path mapped to both capability IDs and separately
  preserves unique source/test paths.

- [ ] **Step 2: Write failing invalid-manifest tests**

  Parameterize missing configured JSON, non-object root, non-list
  `capabilities`, missing/duplicate capability IDs, non-list evidence fields,
  non-string paths, absolute/escaping paths, duplicate aliases inside one row,
  missing files, directories, and symbolic links. Each failure must name the
  matrix location or evidence path.

- [ ] **Step 3: Verify RED**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_evidence_dependencies.py
  ```

  Expected: collection fails because `ai_evidence_dependencies` does not
  exist.

- [ ] **Step 4: Implement the minimum loader**

  Use `PurePosixPath`, resolved-root containment, `lstat`, deterministic sorting,
  and immutable dataclasses. Return `None` only when neither the matrix nor its
  companion Capability Truth Markdown is present; if the document set is
  configured, malformed or missing JSON is an error.

- [ ] **Step 5: Verify GREEN**

  Re-run the focused test file and require all parser cases to pass.

### Task 2: Block incomplete Contract scope in Preflight

**Files:**

- Modify: `scripts/ai_preflight_review.py`
- Modify: `tests/test_preflight_review.py`

**Interfaces:**

- Consumes: `EvidenceDependencies` from Task 1 and `contract.scope`
- Produces: deterministic `Evidence Dependency` Preflight signal

- [ ] **Step 1: Write the interrupted-Work-Item regression**

  Use a matrix where four rows bind
  `docs/getting-started/installation.md`. Assert a Contract that scopes only
  that document returns an `Inconsistent` signal naming the document, matrix,
  and all four IDs.

- [ ] **Step 2: Write negative controls**

  Assert these states:

  - evidence plus matrix in scope → `Ready`;
  - unrelated path only → `Not Applicable`;
  - matrix-only scope → `Ready`;
  - a `docs/**` scope already covering both paths → `Ready`;
  - configured malformed matrix → `Inconsistent`.

- [ ] **Step 3: Verify RED**

  Run the new Preflight test selection. Expected: the signal helper or signal
  entry is absent.

- [ ] **Step 4: Implement the signal**

  Add the dependency signal to `derive_report()` before overall status is
  calculated. Missing ownership must yield `not_ready`; it is not eligible for
  chat-only human override.

- [ ] **Step 5: Verify GREEN**

  Run all `tests/test_preflight_review.py` tests.

### Task 3: Require actual matrix regeneration in Scope Guard

**Files:**

- Modify: `scripts/ai_check_scope.py`
- Modify: `tests/test_contract_and_policy.py`

**Interfaces:**

- Consumes: actual `changed_paths(contract)` and the same dependency graph
- Produces: fail-closed Scope Guard issue when bound evidence changes without the matrix

- [ ] **Step 1: Write the evidence-only RED case**

  Pass `["docs/getting-started/installation.md"]` as the actual diff while both
  evidence and matrix are already declared in Contract scope. Assert Scope
  Guard still fails because ownership does not prove regeneration.

- [ ] **Step 2: Write valid and unrelated controls**

  Assert evidence plus matrix changes pass, matrix-only changes pass, unrelated
  changes pass, and a malformed configured dependency matrix fails.

- [ ] **Step 3: Verify RED**

  Run the focused Scope Guard tests. Expected: evidence-only diff currently
  passes.

- [ ] **Step 4: Implement changed-path enforcement**

  Invoke the Task 1 helper after ordinary scope ownership. Keep existing YAML
  `dependencyScopeRules` behavior unchanged.

- [ ] **Step 5: Verify GREEN**

  Run the full Contract/Scope Guard focused suites.

### Task 4: Document, trace, and protect distribution coverage

**Files:**

- Modify: `docs/reference/capability-truth-matrix.md`
- Modify: `.ai/guards/coverage_policy.yaml`
- Modify: `docs/reference/remediation-instruction-traceability.json`
- Modify: `docs/reference/documentation-context-registry.json`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`
- Modify: `scripts/ai_installer_catalog.json`
- Modify: `tests/test_installed_runtime_parity.py`
- Regenerate: `docs/reference/capability-truth-matrix.json`
- Modify: `.ai/work-items/active/capability-evidence-scope-dependency-corrective-20260729.summary.json`

**Interfaces:**

- Consumes: implemented Preflight and Scope behavior
- Produces: instruction → plan → implementation → acceptance mapping and reviewer handoff evidence

- [ ] **Step 1: Document the two distinct requirements**

  State that Contract scope must own the matrix before editing and that the
  actual diff must contain a regenerated matrix whenever a bound source/test
  file changes. Do not imply matrix regeneration proves the underlying
  capability.

- [ ] **Step 2: Register executable coverage**

  Associate `scripts/ai_evidence_dependencies.py` with
  `tests/test_evidence_dependencies.py`; do not raise a complexity threshold
  unless measured policy evidence requires a scoped repayment record.

- [ ] **Step 3: Update bidirectional traceability**

  Add one directive mapping the user instruction and observed failure to the
  Contract, this plan, all implementation paths, focused commands, and A1–A10.
  Register the plan in the documentation context registry.

- [ ] **Step 4: Record the issue and scenario evidence**

  The Summary must distinguish the correct stale-evidence gate from the missing
  early dependency gate and record RED/GREEN output for every scenario.

- [ ] **Step 5: Preserve the future absurd/injection baseline without overclaim**

  Record the user's supplied current-adopter assessment in the comprehensive
  plan as reference input for the later real absurd/injection Work Item. Keep
  its three-layer distinction: request-time semantic classification is
  currently medium, post-write repository evidence governance is comparatively
  strong, and physical shell/network/secret/push prevention is weak or outside
  the Repository Governance Layer. Preserve all 12 conditional conclusions,
  and state that near-complete fixed-corpus results do not prove generalized
  semantic attack recognition. Do not implement that future Work Item here.

- [ ] **Step 6: Close the installed-runtime dependency**

  Record the full-quality failure caused by the missing installed module. Add a
  RED installed-runtime assertion for `ai_evidence_dependencies.py`, include
  it in the authoritative installer catalog, regenerate the Capability Truth
  matrix, and prove fresh installed imports do not rely on host scripts.

- [ ] **Step 7: Run focused and fast verification**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q \
    tests/test_installed_runtime_parity.py \
    tests/test_evidence_dependencies.py \
    tests/test_preflight_review.py \
    tests/test_contract_and_policy.py \
    tests/test_capability_truth_matrix.py \
    tests/test_absurd_capability_truth.py
  make check-instruction-traceability
  make quality-fast
  ```

### Task 5: Complete the governed lifecycle

**Files:**

- Update/archive: Contract, Summary, Status, start receipt, archive manifest, and archive index

**Interfaces:**

- Consumes: all verified implementation and traceability evidence
- Produces: merged and closed corrective on synchronized `main`

- [ ] **Step 1: Refresh final Contract checkpoints**

  Run `before_edit` and `before_finish` against the final Contract and Summary.

- [ ] **Step 2: Run full finish**

  Run:

  ```bash
  make ai-finish TASK=capability-evidence-scope-dependency-corrective-20260729
  ```

  If a late Summary-only failure follows a passed heavy quality gate, record
  the missing evidence-reuse/order behavior as a process issue. Do not bypass
  canonical Finish; route the optimization to the later process corrective.

- [ ] **Step 3: Validate and publish one PR**

  Commit the archive bundle, run `make check-ai-pr` against base
  `4a78169e7c82b575d93f830b8acbddaee70b6288`, push, open one PR, and require all
  exact-Head Hosted checks.

- [ ] **Step 4: Merge and close**

  Merge without provider-side branch deletion, then run:

  ```bash
  make ai-close-work-item TASK=capability-evidence-scope-dependency-corrective-20260729
  ```

- [ ] **Step 5: Prove cleanup and resume**

  Verify synchronized clean `main`, absent local/remote corrective branch, and
  removed corrective worktree. Then rebase/resume the paused Japanese Session
  documentation corrective, add/regenerate the capability matrix under its
  expanded Contract, and rerun its full `ai-finish`.

## Plan self-review

- Spec coverage: A1–A10 map respectively to Tasks 2, 3, 1, 1–3, 1–3, 4, 4,
  5, Task 4 Step 5, and Task 4 Step 6.
- Placeholder scan: no implementation step contains TBD/TODO or deferred error
  handling.
- Type consistency: all consumers use the same `EvidenceDependencies`,
  `contract_scope_dependency_issues`, and `changed_path_dependency_issues`
  interfaces defined in Task 1.
