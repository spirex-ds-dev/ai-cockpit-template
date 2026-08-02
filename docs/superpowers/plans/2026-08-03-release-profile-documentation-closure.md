---
author: Codex
title: "Release Profile Documentation Closure Plan"
description: "Minimal plan for removing the residual fourth-profile wording from current documentation."
---

# Release Profile Documentation Closure Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** Execute this small documentation-only plan in the
> dedicated `release-profile-documentation-closure` Work Item. Each completed
> step must be verified before lifecycle closure.

**Goal:** Ensure current documentation defines exactly `light`, `standard`, and
`strict` Governance Profiles and describes `release` only as a Strict operation
escalation.

**Architecture:** Correct the two active historical implementation records so
they preserve useful context without contradicting today's canonical reference.
Correct the Japanese and Simplified Chinese reference metadata to state the
same model. No runtime policy, provider configuration, or archived Work Item is
changed.

**Tech Stack:** Markdown, repository documentation metadata validation, system
invariants, and ripgrep-based terminology verification.

## Global Constraints

- The canonical model is `light < standard < strict`.
- `release` is an operation class and may add release-preflight and distribution
  verification only to a release-related Strict Work Item.
- Historical archived Work Item evidence is immutable.
- Do not change Provider configuration, branch protection, or release state.

---

### Task 1: Correct active terminology records

**Files:**

- Modify: `docs/superpowers/specs/2026-08-01-risk-based-quality-routing-design.md`
- Modify: `docs/superpowers/plans/2026-08-01-risk-based-quality-routing.md`
- Modify: `docs/reference/governance-profiles.ja.md`
- Modify: `docs/reference/governance-profiles.zh-CN.md`

**Consumes:** `.ai/glossary.md` and `docs/reference/governance-profiles.md`.

**Produces:** Current documentation that never presents release as a fourth
Governance Profile.

- [ ] Replace the former four-profile decision in the design record with the
      current three-profile model and explicit release escalation.
- [ ] Update the implementation record's goal and verification tasks to test
      three profiles plus a release operation, not four profiles.
- [ ] Change localized reference descriptions to name only the three profiles;
      retain their existing release-operation explanation.
- [ ] Run the focused non-archive terminology scan and confirm no fourth-profile
      claim remains.

### Task 2: Validate documentation and governed closure

**Files:**

- Verify: `docs/superpowers/plans/2026-08-03-release-profile-documentation-closure.md`
- Verify: repository documentation and governance checks

**Consumes:** The corrected Task 1 documents.

**Produces:** Evidence that metadata, invariants, scope, and scenario coverage
remain aligned before Work Item finish.

- [ ] Run `make check-docs-metadata`, `make check-ai-system-invariants`, and
      the focused terminology scan.
- [ ] Record scenario evidence, documentation alignment, and no residual risk
      in the Change Summary.
- [ ] Run the Contract-required finish, archive, PR, merge, and
      `ai-close-work-item` lifecycle without provider configuration changes.

## Plan Self-Review

- Scope is limited to current Markdown records and generated governed evidence.
- The canonical three-profile model is explicit in every task.
- No placeholder action, unbounded cleanup, or implementation change is needed.
