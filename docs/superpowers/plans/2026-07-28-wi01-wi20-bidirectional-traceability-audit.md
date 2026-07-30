---
author: Ray
title: "WI-01 through WI-20 Bidirectional Traceability Audit Implementation Plan"
description: Test-driven execution plan for the complete instruction, plan, implementation, and acceptance audit.
keywords:
  - implementation-plan
  - traceability
  - work-items
  - audit
---

# WI-01 through WI-20 Bidirectional Traceability Audit Implementation Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove, for every WI-01 through WI-20, that the original instruction, approved plan, archived implementation, and executable acceptance evidence form a complete mapping in both directions.

**Architecture:** A machine-readable twenty-row audit is the authoritative result. The existing instruction-traceability gate validates row identity, evidence domains, archive bindings, named paths, reverse coverage, finding state, and top-level completion; a Markdown report presents the same facts for human review. Confirmed omissions leave the audit open and are fixed only through separate corrective Work Items before the affected row is reverified.

**Tech Stack:** JSON evidence, Markdown reports, Python standard library validation, pytest mutation regressions, AI Cockpit Contract/Summary/archive lifecycle.

## Global Constraints

- Preserve every archived Contract, Summary, Manifest, and index entry byte-for-byte.
- Audit exactly WI-01 through WI-20; historical completion labels are not acceptance evidence.
- A user-named path requires exact implementation evidence or a specific evidence-backed no-change rationale.
- Both directions are mandatory: instruction → plan → implementation → acceptance and acceptance → implementation → plan → instruction.
- Confirmed omissions are release-blocking and require an independent corrective Work Item, PR, merge, closure, and branch cleanup.
- Do not enter process issues, Japanese assessment, documentation alignment, release, or cleanup while this audit is open.

---

### Task 1: Define the canonical twenty-row audit

**Files:**

- Create: `docs/reference/wi01-wi20-bidirectional-traceability-audit.json`
- Modify: `docs/reference/instruction-traceability.md`
- Test: `tests/test_instruction_traceability.py`

**Interfaces:**

- Consumes: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`, `docs/reference/remediation-instruction-traceability.json`, `.ai/work-items/archive/index.json`
- Produces: `auditVersion: 1`, `status`, `workItems`, and `findings`; each work-item row owns `workItemId`, `instructionEvidence`, `planEvidence`, `contractEvidence`, `implementationEvidence`, `noChangeRationales`, `acceptanceEvidence`, `verificationEvidence`, `namedPaths`, `findings`, and `status`

- [x] **Step 1: Write the failing shape tests**

  Require exactly the set `WI-01` through `WI-20`, reject duplicate/unknown IDs, and require every evidence domain to be an array with at least one usable entry unless a schema-authorized no-change rationale satisfies an exact named path.

- [x] **Step 2: Run the focused tests and confirm the old repository has no canonical twenty-row audit**

  Run: `.venv/bin/python -m pytest -q tests/test_instruction_traceability.py`

  Expected: FAIL because `docs/reference/wi01-wi20-bidirectional-traceability-audit.json` and its validation do not exist.

- [x] **Step 3: Add the audit schema instance and documentation**

  Use this row boundary:

  ```json
  {
    "workItemId": "WI-01",
    "instructionEvidence": [{"path": "...", "locator": "..."}],
    "planEvidence": [{"path": "...", "locator": "..."}],
    "contractEvidence": [{"contractPath": "...", "summaryPath": "...", "manifestPath": "..."}],
    "implementationEvidence": [{"path": "...", "reason": "..."}],
    "noChangeRationales": [],
    "acceptanceEvidence": [{"path": "...", "reason": "..."}],
    "verificationEvidence": [{"command": "...", "result": "passed", "sourcePath": "..."}],
    "namedPaths": [],
    "findings": [],
    "status": "verified"
  }
  ```

- [x] **Step 4: Run the focused shape tests**

  Run: `.venv/bin/python -m pytest -q tests/test_instruction_traceability.py`

  Expected: Shape tests pass; evidence-content tests introduced in Task 2 may still fail.

### Task 2: Validate evidence existence, archive identity, and named paths

**Files:**

- Modify: `scripts/check_instruction_traceability.py`
- Modify: `tests/test_instruction_traceability.py`
- Modify: `docs/reference/wi01-wi20-bidirectional-traceability-audit.json`

**Interfaces:**

- Consumes: canonical audit rows and `.ai/work-items/archive/index.json`
- Produces: deterministic errors containing the WI ID, evidence domain, and exact missing or mismatched path

- [x] **Step 1: Add negative tests**

  Cover a missing implementation path, missing acceptance path, Contract/Summary pair mismatch, Manifest path mismatch, digest mismatch, broad-glob named-path substitution, empty no-change reason, and a no-change reason without source evidence.

- [x] **Step 2: Confirm every new negative test fails against the current checker**

  Run: `.venv/bin/python -m pytest -q tests/test_instruction_traceability.py`

  Expected: FAIL for each unsupported audit mutation.

- [x] **Step 3: Implement deterministic audit validation**

  Resolve repository paths without following evidence outside the repository, bind archive triples through index paths and SHA-256 values, and require each `namedPaths[].path` to appear exactly in `implementationEvidence` or in one `noChangeRationales` entry with non-empty `reason` and `evidence`.

- [x] **Step 4: Populate exact evidence for all twenty rows**

  Read each cited archived Contract and Summary; record concrete implementation and acceptance paths from those artifacts. Do not copy broad `scope` globs into implementation evidence. Record any unsupported claim as an open finding instead of setting the row to verified.

- [x] **Step 5: Run the checker and focused tests**

  Run: `make check-instruction-traceability`

  Expected: PASS only when all current row evidence is structurally and cryptographically valid.

### Task 3: Enforce reverse coverage and finding closure

**Files:**

- Modify: `scripts/check_instruction_traceability.py`
- Modify: `tests/test_instruction_traceability.py`
- Modify: `docs/reference/wi01-wi20-bidirectional-traceability-audit.json`

**Interfaces:**

- Consumes: validated twenty-row evidence
- Produces: reverse-ownership map for implementation and acceptance paths plus fail-closed audit/finding status

- [x] **Step 1: Add reverse-coverage and false-completion tests**

  Add mutations for orphan implementation evidence, orphan acceptance evidence, duplicate ownership without an explicit shared-evidence reason, an open finding under `status: complete`, and a verified row containing an open finding.

- [x] **Step 2: Confirm the mutations fail**

  Run: `.venv/bin/python -m pytest -q tests/test_instruction_traceability.py`

  Expected: FAIL before reverse-coverage and finding-state validation is implemented.

- [x] **Step 3: Implement reverse coverage**

  Build exact path ownership from the twenty rows. Every implementation and acceptance path must resolve to at least one instruction locator and one plan locator in its owning row. Shared paths require `sharedEvidenceReason`; duplicate ownership without it is an error.

- [x] **Step 4: Implement closure-state rules**

  Permit top-level `complete` only when all twenty rows are `verified`, all findings are `resolved` or `not_applicable`, and every corrective-required finding cites a closed archived corrective Contract/Summary/Manifest triple.

- [x] **Step 5: Run focused validation**

  Run: `.venv/bin/python -m pytest -q tests/test_instruction_traceability.py && make check-instruction-traceability`

  Expected: All focused tests and the repository audit pass, or the audit remains explicitly open with exact corrective-required findings.

### Task 4: Produce the human report and route omissions

**Files:**

- Create: `docs/reference/wi01-wi20-bidirectional-traceability-audit.md`
- Modify: `docs/reference/wi01-wi20-bidirectional-traceability-audit.json`
- Modify: `docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md`
- Modify: `docs/reference/remediation-instruction-traceability.json`

**Interfaces:**

- Consumes: machine-readable audit rows and findings
- Produces: one human table with WI, status, exact evidence, finding IDs, corrective IDs, residual limits, and next action

- [x] **Step 1: Summarize all twenty rows without adding facts**

  The Markdown report must state that archived implementation evidence proves repository history, not current adopter, provider, enterprise, or release readiness.

- [x] **Step 2: Record every finding**

  Each finding contains `findingId`, `workItemId`, `severity`, `missingDomain`, `fact`, `evidence`, `status`, `releaseBlocking`, `correctiveWorkItemId`, and `reverification`.

- [x] **Step 3: Route confirmed omissions**

  If no findings are open, continue to Task 5. If any finding is open, leave this audit Work Item active, start exactly one dedicated corrective at a time from current `origin/main`, complete its entire lifecycle, resume this audit through `make ai-resume-work-item`, and reverify the affected rows.

- [x] **Step 4: Align the authoritative plan and directive registry**

  Record the audit result and corrective state without changing the eight-stage order or claiming later stages complete.

### Task 5: Verify, archive, review, and close

**Files:**

- Modify: `.ai/work-items/active/wi01-wi20-bidirectional-traceability-audit-20260728.summary.json`
- Generate: `.ai/cockpit/current_status.md`
- Generate: `.ai/work-items/archive/2026/wi01-wi20-bidirectional-traceability-audit-20260728.*`

**Interfaces:**

- Consumes: complete audit, zero open findings, focused evidence, and all closed corrective lineages
- Produces: archived audit evidence, independent PR, Hosted CI, merged PR, closed lifecycle, deleted branches, synchronized `main`

- [x] **Step 1: Run focused checks**

  Run: `.venv/bin/python -m pytest -q tests/test_instruction_traceability.py`

  Run: `make check-instruction-traceability`

- [ ] **Step 2: Run AI Cockpit verification and full quality**

  Run: `make ai-finish TASK=wi01-wi20-bidirectional-traceability-audit-20260728`

  Expected: all required gates pass and the audit archives only with zero open findings.

- [ ] **Step 3: Run post-archive PR validation**

  Commit the complete archive bundle, then run `make check-ai-pr AI_BASE_COMMIT=<recorded-base-commit>`.

- [ ] **Step 4: Complete provider and lifecycle closure**

  Push the dedicated branch, open one PR, wait for all Hosted checks including terminal CI evidence, merge without provider branch deletion, run `make ai-close-work-item TASK=wi01-wi20-bidirectional-traceability-audit-20260728`, and verify local/remote branch deletion plus `main == origin/main`.

- [ ] **Step 5: Advance only to the process-issues stage**

  The next stage is other recorded process issues plus `RFE-ISSUE-082`; Japanese assessment, documentation alignment, release, and plan cleanup remain blocked.
