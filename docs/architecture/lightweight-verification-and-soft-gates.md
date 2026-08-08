---
author: AI Cockpit maintainers
title: "Lightweight Verification and Soft Gates"
description: "Task, PR, and Release verification stages with shared evidence context."
keywords:
  - verification
  - soft-gates
  - task
  - release
---

# Lightweight Verification and Soft Gates

Verification has three views over one immutable `VerificationContext`:

- **Task** checks changed files and affected tests.
- **PR** checks project health and critical trust boundaries.
- **Release** checks the complete strict proof, including identity, supply chain, installer lifecycle, compatibility, and distribution.

Each checker emits a structured result with a `hard`, `soft`, or `informational` gate. A hard failure remains fail-closed. Complexity growth, archive count, checker count, documentation drift, and duration are trend signals; insufficient history is a warning and may require human confirmation. A check that does not apply to a stage is still emitted as `skipped` with a reason code such as `stage_not_applicable`.

The context reads Git changes, Contract, Summary, Project Profile, impact policy, and complexity policy once per run. Checker registration is deduplicated by ID. Historical archive evidence and repayment records are never rewritten. `current_status.md` remains a generated decision view; structured verification evidence is the machine source.

Use `make ai-verify CONTRACT=... SUMMARY=... STAGE=task|pr|release` for a direct structured run. During `ai-finish`, the registered `quality` check derives the task policy from the actual changed paths after excluding only that Work Item's generated Contract, Summary, Start Receipt, Outcome, and Cockpit status projections. A docs-only task can therefore select the focused `quality-fast` route; workflow, installer, dependency, trust, unknown, and mixed paths remain strict. The selected policy and exact quality command are preserved in the quality verification evidence. PR and Release retain their full stage floors and are never downgraded by a focused local Finish result.
