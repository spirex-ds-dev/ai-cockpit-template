---
author: Codex
title: "Risk-Based Quality Routing Implementation Plan"
description: "Executable plan for WI-03 governance-profile selection and quality routing."
---

# Risk-Based Quality Routing Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For Codex:** Use test-driven development for each behavior group and run the
> smallest focused verification after every green step. The repository Work Item
> lifecycle remains the final integration and archival authority.

**Goal:** Make Lite, Standard, Strict, and Release selection deterministic,
Contract-bound, conservative, and executable through the existing quality graph.

**Architecture:** A new Python router reads a versioned YAML policy and emits one
receipt. Contract validation, the legacy scope adapter, verification policy, and
Make consume the same ordered profile semantics. Make routing selects existing
owners and does not duplicate their commands.

**Tech stack:** Python 3 standard library plus repository YAML support, GNU Make,
pytest, JSON/YAML governance artifacts, Markdown documentation.

---

## Task 1: Bootstrap Contract profile validation

**Files:** `tests/test_contract_and_policy.py`, `scripts/ai_check_work_item.py`,
active WI-03 Contract.

1. Add failing tests for a valid automatic profile and malformed selected,
   source, reasons, and override combinations.
2. Run the focused test and confirm the new cases fail for the missing field.
3. Add the closed Contract field and minimal structural validator.
4. Run the focused test to green.
5. Add the actual Strict automatic profile to the active Contract and rerun
   `make ai-prepare-implementation` so the `before_edit` hash binds the schema.

## Task 2: Build the policy-backed selector

**Files:** `.ai/quality/governance-routing.yaml`,
`scripts/determine_governance_profile.py`, `tests/test_governance_profile.py`.

1. Add failing classification tests for Lite, Standard, every Strict protected
   class, Release, unknown, empty, mixed, and input-order independence.
2. Implement strict policy loading, normalized path matching, profile ordering,
   and deterministic receipts.
3. Add failing CLI/security tests for invalid bases, malformed YAML, absolute and
   traversing paths, and symlink repository escape; implement fail-closed checks.
4. Add failing override tests for complete current evidence, missing fields,
   mismatch, expiry, explicit upward escalation, and forbidden downgrade.
5. Implement bounded override evaluation and rerun the focused suite to green.

## Task 3: Align compatibility and verification consumers

**Files:** `scripts/determine_quality_scope.py`,
`scripts/ai_verification_policy.py`, `tests/test_verification_policy.py`, router
tests.

1. Add red tests proving the legacy output schema and explicit modes remain
   compatible while classification delegates to the router.
2. Replace independent legacy classification with profile projection.
3. Add red tests for the four-level verification vocabulary and conservative
   ordering; update the policy module without creating a second classifier.
4. Run both focused suites to green.

## Task 4: Route existing Make ownership graphs

**Files:** `Makefile`, `templates/make/Makefile.ai`, `tests/test_makefile.py`,
`tests/test_quality_gate_architecture.py`.

1. Add red dry-run and architecture assertions for Lite, Standard, Strict, and
   Release routing, sole gate ownership, explicit escalation, and rejected
   downgrade.
2. Add a Standard composition target using existing Fast, project-test,
   reference-impact, and full test-weakening owners.
3. Make `ai-cockpit-quality` discover the active Contract, create the routing
   receipt, and dispatch exactly one selected graph.
4. Mirror the interface in the adopter Make template and run focused tests.

## Task 5: Preserve installation parity

**Files:** `scripts/ai_installer_catalog.json`, `tests/test_adoption_e2e.py`.

1. Add red assertions that the router and policy are installed and executable.
2. Register the script in the installer catalog and rely on the governed `.ai`
   tree copy for the policy.
3. Run the focused adoption scenario to green.

## Task 6: Document the public governance contract

**Files:** the three governance-profile references, documentation registry,
capability truth and alignment artifacts.

1. Document profiles, precedence, receipt fields, override evidence, CLI/Make
   usage, compatibility, and non-claims in English, Japanese, and Chinese.
2. Register the design and plan as implementation records.
3. Update capability and documentation-alignment evidence through their
   repository-supported generators or validators; do not hand-edit generated
   status files.
4. Run docs metadata, alignment, and traceability checks.

## Task 7: Verify and close the Work Item

1. Run all focused WI-03 tests, then the Contract-declared Strict project and AI
   checks. Fix only demonstrated defects and rerun the affected minimum set.
2. Complete scenario evidence, guidelines compliance, verification results, and
   change summary.
3. Run `make ai-checkpoint` at `before_finish`, generate status, and execute
   `ai-finish` until the Work Item archives cleanly.
4. Commit the archived Work Item and implementation, push the dedicated branch,
   create and merge one PR, wait for required hosted checks, and run
   `make ai-close-work-item TASK=wi-03-risk-based-quality-routing`.
5. Confirm remote/local branch absence, clean synchronized base, and
   `ready_on_base` before starting WI-05.
