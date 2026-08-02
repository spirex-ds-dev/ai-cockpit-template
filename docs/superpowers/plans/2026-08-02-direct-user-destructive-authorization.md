---
author: Ray
title: "Direct-user destructive authorization implementation plan"
description: "Implementation record for bounded direct-user authorization evidence."
audience: maintainers
status: current
authority: supporting
lastVerifiedBy: direct-user-destructive-authorization
---

# Direct-user destructive authorization Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a truthful, exact-scope direct-user authorization record for destructive cleanup when the sole GitHub user cannot self-approve.

**Architecture:** Extend the Approval Evidence schema with a distinct `direct_user_authorized` level and bounded evidence fields. The identity validator accepts that level only with exact scope, a direct instruction reference, timestamp, and digest; all Provider and enterprise paths retain their existing requirements. Contract validation delegates to the same semantic function, while documentation and Capability Truth explain the lower-assurance boundary.

**Tech Stack:** Python 3.14, JSON Schema Draft 2020-12, pytest, repository Make targets.

## Global Constraints

- Never relabel direct user authorization as `provider_verified` or `enterprise_verified`.
- Require an exact match between record scope and `destructiveChangePolicy.allowPatterns`.
- Require `provider: null` and prohibit provider/enterprise identifier fields for direct-user records.
- Preserve fail-closed behavior for `self_declared`, `repository_recorded`, and malformed evidence.
- Do not modify Provider configuration or delete lifecycle artifacts in this Work Item.

---

### Task 1: Define and prove direct-user Approval Evidence

**Files:**
- Modify: `.ai/trust/schema/approval.schema.json`
- Modify: `scripts/ai_external_identity.py`
- Test: `tests/test_external_identity.py`

**Interfaces:**
- Consumes: `approval_issues(record)` and `high_risk_approval_issues(record, required_scope=...)`.
- Produces: `identity_state(record) == "direct_user_authorized"` for a valid direct-user record.

- [ ] **Step 1: Write failing tests**

```python
def test_direct_user_record_requires_exact_scope_and_instruction_binding() -> None:
    record = direct_user_approval()
    assert ai_external_identity.high_risk_approval_issues(
        record, required_scope=[".worktrees/example"]
    ) == []
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `PYTHONPATH=scripts .venv/bin/pytest -q tests/test_external_identity.py -k direct_user`

Expected: failure because `direct_user_authorized` is not accepted by the schema or high-risk validator.

- [ ] **Step 3: Implement the minimal schema and validator rules**

```python
DIRECT_USER_LEVEL = "direct_user_authorized"

if level == DIRECT_USER_LEVEL:
    require_null_provider_and_exact_direct_user_fields(evidence)
```

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `PYTHONPATH=scripts .venv/bin/pytest -q tests/test_external_identity.py`

Expected: all external-identity tests pass, including malformed direct-user cases.

### Task 2: Bind Contract validation to the new truthful level

**Files:**
- Modify: `scripts/ai_check_work_item.py`
- Modify: `tests/test_ai_check_work_item.py`

**Interfaces:**
- Consumes: `high_risk_approval_issues` and `destructiveChangePolicy.allowPatterns`.
- Produces: acceptance only for a valid exact-scope `direct_user_authorized` record.

- [ ] **Step 1: Write a failing Contract test**

```python
def test_destructive_contract_accepts_exact_direct_user_authorization() -> None:
    contract = valid_contract()
    contract["destructiveChangePolicy"] = direct_user_destructive_policy()
    assert ai_check_work_item.validate_contract(contract) == []
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `PYTHONPATH=scripts .venv/bin/pytest -q tests/test_ai_check_work_item.py -k direct_user`

Expected: failure because high-risk Contract validation still accepts only Provider or enterprise levels.

- [ ] **Step 3: Implement the minimal Contract integration**

```python
identity_issues = high_risk_approval_issues(identity_evidence, required_scope=patterns)
```

Update the high-risk validator’s eligible level set without changing its exact-scope call site.

- [ ] **Step 4: Run focused Contract tests**

Run: `PYTHONPATH=scripts .venv/bin/pytest -q tests/test_ai_check_work_item.py tests/test_external_identity.py`

Expected: valid bounded evidence passes; missing or mismatched records fail.

### Task 3: Publish the assurance boundary and regenerate derived truth

**Files:**
- Modify: `docs/reference/external-identity-boundary.md`
- Modify: `docs/contract-fields.md`
- Modify: `docs/reference/capability-truth-matrix.json`
- Modify: `docs/reference/capability-truth-matrix.md`
- Test: `tests/test_trust_schema.py`

**Interfaces:**
- Consumes: documented Approval Evidence schema and validator behavior.
- Produces: a current Capability Truth claim that explicitly describes direct-user authorization as lower assurance.

- [ ] **Step 1: Write/extend the schema regression test first**

```python
assert "direct_user_authorized" in schema["properties"]["identityLevel"]["enum"]
```

- [ ] **Step 2: Run it to confirm the red failure**

Run: `PYTHONPATH=scripts .venv/bin/pytest -q tests/test_trust_schema.py -k direct_user`

Expected: failure until the schema enum is changed.

- [ ] **Step 3: Document the accepted fields and non-capabilities**

State that instruction references and digests are repository records, not independent identity authentication; regenerate truth bytes with `python3 scripts/ai_capability_truth.py --write`.

- [ ] **Step 4: Run focused verification**

Run: `make check-trust-schemas && PYTHONPATH=scripts .venv/bin/pytest -q tests/test_external_identity.py tests/test_ai_check_work_item.py tests/test_trust_schema.py && python3 scripts/ai_capability_truth.py`

Expected: all commands pass and the derived matrix is fresh.

### Task 4: Finish the governed Work Item

**Files:**
- Modify: `.ai/work-items/active/direct-user-destructive-authorization.summary.json`
- Generated: `.ai/cockpit/current_status.md`, active Outcome, archive bundle

**Interfaces:**
- Consumes: focused test results and full required quality evidence.
- Produces: an archived Outcome and merge-ready Work Item.

- [ ] **Step 1: Record guideline, scenario, documentation, and exact verification evidence in the Summary**
- [ ] **Step 2: Run `make ai-checkpoint ... STAGE=before_finish` and `make ai-finish TASK=direct-user-destructive-authorization`**
- [ ] **Step 3: Report the evidence-derived traffic-light Outcome to the user before archive**
- [ ] **Step 4: Archive, commit, run `make check-ai-pr AI_BASE_COMMIT=9a177e4cdf4afb7d7b75de1e3b6c6db01b7376ff`, push, create/merge the PR, and run `make ai-close-work-item`**

## Self-review

- Spec coverage: Tasks 1–2 cover A1–A3, Task 3 covers A4, and Tasks 1–3 cover A5.
- Placeholder scan: no unresolved task or interface placeholders remain.
- Type consistency: `direct_user_authorized` is the sole new identity-level string throughout the plan.
