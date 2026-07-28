---
author: Ray
title: "WI-10 Prompt-First Multiplatform Installation Implementation Plan"
description: Test-driven execution plan for the beginner-safe trilingual WI-10 corrective.
keywords:
  - implementation-plan
  - installation
  - prompt-first
  - multilingual
---

# WI-10 Prompt-First Multiplatform Installation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver and enforce a complete prompt-first installation hand
sequence that a person with no programming experience can follow in English,
Simplified Chinese, or Japanese, including iOS, Android, and Java.

**Architecture:** Existing documentation metadata checks become the executable
schema for novice stages, prompt authority boundaries, calibration completeness,
platform examples, and language links. Three complete installation guides are
the source routes; short READMEs and layered pages link into them.

**Tech Stack:** Markdown, Python standard library, pytest, Make, AI Cockpit
Contract/Summary evidence.

## Global Constraints

- Do not change installer, calibration, runtime, security, or capability behavior.
- Do not infer toolchain, device, signing, hosted-CI, or production evidence.
- Keep English, Chinese, and Japanese structure and safety meaning aligned.
- Prefer copy-ready prompts; retain only necessary human bootstrap/evidence commands.
- Every phase states action, expected result, stop condition, and recovery.
- One Work Item, one branch, one PR, merge, archive, closure, and branch cleanup.

---

### Task 1: Lock the executable beginner-document schema

**Files:**
- Modify: `tests/test_docs_metadata.py`
- Modify: `scripts/check_docs_metadata.py`

**Interfaces:**
- Consumes: existing `check_repository(root: Path) -> list[str]`.
- Produces: `beginner_installation_errors(root: Path) -> list[str]`, included
  by `check_repository`.

- [ ] **Step 1: Write failing mutation tests**

Add tests that copy repository documentation, then independently remove:
`installation.zh-CN.md`, one `novice-stage`, one `calibration-stage`, one
required prompt-safety marker, one platform-language file, one
`platform-stage`, one platform non-claim marker, and one same-language link.
Assert each error names the exact path and missing identifier.

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:
`PYTHONPATH=scripts python3 -m pytest -q tests/test_docs_metadata.py -k beginner`

Expected: import or assertion failures because
`beginner_installation_errors` and the required documents do not exist.

- [ ] **Step 3: Implement the checker constants and deterministic errors**

Define exact language suffixes, novice stages, calibration stages, platforms,
platform stages, prompt safety markers, command explanation markers, and
same-language targets. Read only repository files; return one stable error per
missing file, identifier, or link.

- [ ] **Step 4: Run the focused tests**

Expected at this intermediate point: checker mutation assertions pass while
the positive repository check reports missing content.

### Task 2: Write the three complete installation routes

**Files:**
- Modify: `docs/getting-started/installation.md`
- Create: `docs/getting-started/installation.zh-CN.md`
- Modify: `docs/getting-started/installation.ja.md`

**Interfaces:**
- Consumes: exact identifiers from Task 1 and executable calibration stages
  in `scripts/ai_calibrate.py`.
- Produces: complete same-order trilingual guides.

- [ ] **Step 1: Replace the English route**

Write all 15 novice stages, prompt contract markers, retained-command
explanations, scaffold inventory, ten calibration stages and answer forms,
first governed lifecycle, stop/recovery table, and final success checklist.

- [ ] **Step 2: Write complete Chinese and Japanese routes**

Translate every section semantically. Preserve identifiers, file paths,
command evidence, authority boundaries, and non-claims exactly; do not replace
sections with summaries.

- [ ] **Step 3: Run the focused checker**

Run:
`PYTHONPATH=scripts python3 -m pytest -q tests/test_docs_metadata.py -k 'beginner or authoritative_command'`

Expected: installation-route tests pass; platform-file tests remain red.

### Task 3: Add complete iOS, Android, and Java examples

**Files:**
- Create: `docs/getting-started/examples/ios.md`
- Create: `docs/getting-started/examples/ios.zh-CN.md`
- Create: `docs/getting-started/examples/ios.ja.md`
- Create: `docs/getting-started/examples/android.md`
- Create: `docs/getting-started/examples/android.zh-CN.md`
- Create: `docs/getting-started/examples/android.ja.md`
- Create: `docs/getting-started/examples/java.md`
- Create: `docs/getting-started/examples/java.zh-CN.md`
- Create: `docs/getting-started/examples/java.ja.md`

**Interfaces:**
- Consumes: platform identifiers and safety markers from Task 1.
- Produces: nine same-structure platform walkthroughs.

- [ ] **Step 1: Write the English examples**

For each platform, include the copy-ready read-only prompt, evidence inventory,
stack/boundary choices, quality-command discovery, generated/critical paths,
stop/recovery rules, and platform success checklist. State all platform
non-claims explicitly.

- [ ] **Step 2: Write the Chinese and Japanese examples**

Translate every section and preserve all machine markers and safety boundaries.

- [ ] **Step 3: Run platform mutation tests**

Expected: all missing-file, missing-stage, and missing-boundary tests pass.

### Task 4: Align navigation and concise entrypoints

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `README.ja.md`
- Modify: `docs/getting-started/30-second-start.md`
- Modify: `docs/getting-started/30-second-start.zh-CN.md`
- Modify: `docs/getting-started/30-second-start.ja.md`
- Modify: `docs/getting-started/standard-adoption-guide.md`
- Modify: `docs/getting-started/standard-adoption-guide.zh-CN.md`
- Modify: `docs/getting-started/standard-adoption-guide.ja.md`
- Modify: `docs/reference/documentation-architecture.md`
- Modify: `docs/reference/documentation-context-registry.json`

**Interfaces:**
- Consumes: the complete routes and examples from Tasks 2–3.
- Produces: same-language, non-duplicated navigation.

- [ ] **Step 1: Replace first-use commands with the discovery prompt**

Keep existing fact markers and lifecycle facts, but make the first action a
same-language prompt and link to the complete guide for every next step.

- [ ] **Step 2: Add same-language platform links**

READMEs and installation pages link to the matching iOS, Android, and Java
documents; no language silently falls back to English.

- [ ] **Step 3: Register the new current documentation**

Update documentation architecture/context records without reclassifying
immutable history.

- [ ] **Step 4: Run all documentation metadata tests**

Run:
`PYTHONPATH=scripts python3 -m pytest -q tests/test_docs_metadata.py`

Expected: PASS.

### Task 5: Close traceability, evidence, and lifecycle

**Files:**
- Modify: `docs/reference/remediation-instruction-traceability.json`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`
- Modify: `.ai/work-items/active/wi10-prompt-first-multiplatform-installation-20260728.summary.json`
- Generate: `.ai/cockpit/current_status.md`
- Generate/archive: `.ai/work-items/archive/**`, `.ai/cockpit/sbom.json`,
  `.ai/cockpit/provenance.json`, `.ai/cockpit/release-digests.json`,
  `release.json`

**Interfaces:**
- Consumes: all implementation and test evidence.
- Produces: bidirectional evidence for WI10-AUDIT-001 through
  WI10-AUDIT-004 and a closed Work Item lifecycle.

- [ ] **Step 1: Record exact implementation and acceptance evidence**

Map each of the four audit findings to exact files, tests, and verification.
Record the two preflight formatting pauses as resolved process observations;
do not reinterpret them as product defects.

- [ ] **Step 2: Run focused and fast governance checks**

Run documentation tests, `make check-docs-metadata`,
`make check-instruction-traceability`, and `make quality-fast`.
Expected: PASS.

The first supplement `quality-fast` stopped at `project-lint` because the two
new reader-visible checks raised `beginner_installation_errors` complexity from
49 to 51 while the enforced maximum is 50 (`WI-10-ISSUE-028`). The corrective
keeps the budget and acceptance intact: extract those checks into a focused
helper, prove the mutation test and `make project-lint`, then rerun
`quality-fast` from its beginning.

That rerun then stopped earlier at `project-format-check`: Ruff required a
deterministic line wrap in the extracted helper (`WI-10-ISSUE-029`). Only the
affected script is formatted, and the full fast gate must restart again; the
parallel lint success from the failed run is not treated as a complete gate.

Post-Finish review then found that archive processing rewrote the Contract
path but left the Summary path stale while traceability fallback hid the
error (`WI-10-ISSUE-030`). WI-10 stayed frozen until process corrective PR
#448 passed Hosted checks, merged as `221e214d`, closed, and cleaned both
branches. After rebasing on that corrected main, regenerate the no-active
status and complete archive index, migrate this already-archived Summary to
its exact durable path, and rerun traceability plus PR/Hosted verification.

- [ ] **Step 3: Run complete finish verification**

Run the Contract checks, `before_finish` checkpoint, full `make quality`, and
`make ai-finish`. Record actual results and residual evidence limits.

- [ ] **Step 4: Complete GitHub lifecycle**

Commit, push, create the dedicated PR, wait for hosted checks, merge, run
`make ai-close-work-item`, delete local/remote branch through closure, and
synchronize local main to origin/main.

- [ ] **Step 5: Resume the WI-01 through WI-20 audit**

Rebase the preserved audit branch on the new main, mark WI-10 corrective
evidence without claiming the remaining audit is complete, and continue the
approved sequence.

### Supplement: version-neutral installation and proofreading gate

This user-confirmed supplement is part of WI-10 acceptance. The installation
guides must remain reusable across future releases: they must not prescribe a
concrete AI Cockpit release number or use moving `main` metadata as release
evidence. The read-only discovery prompt dynamically selects the highest
verifiable stable release for each installation, and only that transaction's
resolved tag is bound to the installation.

**Instruction → plan → implementation → acceptance mapping:**

| Instruction | Plan | Implementation evidence | Acceptance evidence |
| --- | --- | --- | --- |
| Installation must not be fixed to one version. | Add a reader-visible version-neutral release rule to all three guides and retain tag-pinned verification. | `docs/getting-started/installation.md`, `docs/getting-started/installation.zh-CN.md`, `docs/getting-started/installation.ja.md`; `INSTALLATION_VERSION_NEUTRAL_TEXT`; existing release metadata boundary and hardcoded-version checker. | `test_wi10_beginner_check_rejects_hidden_version_neutral_or_proofreading_copy`; `test_wi10_beginner_check_rejects_moving_or_hardcoded_release_metadata`. |
| The proofreading checklist must be visible and prevent omissions. | Add one same-structure eight-row checklist and language-specific visible heading to each guide and make both executable. | `installation-proofreading-checklist` marker/table; `INSTALLATION_PROOFREADING_HEADING`; `scripts/check_docs_metadata.py`. | Positive trilingual route check; missing-marker and missing-visible-heading mutation tests. |
| Table layout must remain renderable in all languages. | Require uninterrupted five-column Markdown decision rows through the documentation gate. | `_step_table_errors` applied to the new checklist; existing scaffold/calibration/platform table checks remain active. | `test_wi10_beginner_check_rejects_interrupted_or_malformed_proofreading_table`; full `tests/test_docs_metadata.py`. |

- [x] Add version-neutral wording to English, Chinese, and Japanese installation routes.
- [x] Add the visible proofreading checklist to all three routes.
- [x] Add regression gates for missing marker, hidden reader-visible wording, interrupted table, and malformed columns.
- [x] Verify the five focused WI-10 route, visibility, rendering, and release-boundary tests.
- [ ] Record the final result in `wi10-installation-version-neutral` Summary and complete full quality, archive, PR, Hosted CI, merge, closure, and branch cleanup.

The first start attempt correctly rejected the six pre-Contract patch paths as
unowned. The patch was preserved in Git stash, the Work Item was created from a
clean latest `origin/main`, its skeleton `not_ready` report was replaced with
the exact nine-item acceptance and six-scenario Contract, and the patch was
restored only after Preflight became `ready` and the `before_edit` checkpoint
was recorded. The linked worktree has no private `.venv`; focused tests use the
main workspace's ignored, lockfile-backed virtual environment without changing
repository dependencies.
