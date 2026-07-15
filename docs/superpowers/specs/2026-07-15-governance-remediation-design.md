---
author: Ray
title: Governance Remediation Design
description: Approved design for coverage, governance complexity, and adopter configuration remediation.
keywords:
  - governance
  - coverage
  - adoption
---

# Governance Remediation Design

## Goal

Close the three findings from the engineering review through three independent, auditable PRs: raise measured governance coverage to at least 85%, control governance/archive complexity without rewriting history, and make adopter-owned CODEOWNERS and SECURITY configuration explicit and fail-closed.

## Approved approach

1. Coverage: add focused tests for decision-heavy failure branches. Do not lower floors, change production behavior, or inflate coverage with meaningless tests.
2. Complexity: add read-only inventory and lifecycle guidance. Historical Contract/Summary JSON remains immutable; no bulk migration or deletion is performed.
3. Adoption placeholders: retain generic placeholders because this is a reusable template. Strengthen the adopter checklist and readiness evidence so an adopting repository cannot mistake placeholders for production configuration.

## PR boundaries

- `coverage_85_target`: tests plus this design and execution plan.
- `governance_complexity_control`: inventory/reporting and archive lifecycle documentation.
- `adoption_configuration_closure`: adopter configuration guidance and focused readiness checks.

Each PR must contain a version-2 archived Work Item Contract/Summary, pass `make check-ai-pr`, and be merged before its work branch is deleted.

## Verification

- Coverage PR: `make quality`, with measured total coverage `>= 85.0%` and critical floors passing.
- Complexity PR: inventory output, archive index consistency, documentation metadata, and full quality checks.
- Adoption PR: readiness tests for placeholder detection, documentation checks, and full quality checks.

## Non-goals

The template will not invent an owner team, security contact, SLA, or external trust identity. It will not delete historical audit records merely to reduce file counts.
