---
author: Ray
title: "AI Cockpit Documentation"
description: "Reader-first documentation home for understanding, adopting, and operating AI Cockpit."
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - documentation_architecture
---

# AI Cockpit documentation

[中文](README.zh-CN.md) | [日本語](README.ja.md)

This is the five-minute route through AI Cockpit. You do not need to understand
the implementation first. Start by answering four reader questions: what this
project is, why it exists, what it controls, and where a human must decide.

## Understand the project

Follow the same order as the project’s North Star:

1. **North Star / identity** — AI Cockpit is a Repository Governance Layer that
   turns repository evidence into bounded decisions for calibrated human-agent
   trust. See the [Human-Agent Trust Layer](trust-layer.md).
2. **Purpose** — it makes intent, scope, evidence, unknowns, and human decisions
   visible so an agent cannot silently redefine a change. Read [Why AI Cockpit exists](purpose.md).
3. **Design philosophy** — evidence over self-declaration, proportional controls,
   and fail-closed recovery. Read [Design Philosophy](philosophy/design-philosophy.md).
4. **Architecture** — one governed path from Intent to Contract, implementation,
   verification, Summary, Cockpit, and Human Decision. Read [Architecture](architecture.md).
5. **Capabilities and boundaries** — Cockpit governs evidence; it is not an Agent
   Runtime, Workflow Engine, Security Sandbox, identity provider, or substitute
   for human review. Read [Capabilities and boundaries](capabilities.md).
6. **Human decisions** — [Decision States](concepts/decision-states.md) explains
   when to proceed, investigate, or stop.

## Choose a reader goal

| Goal | Start here | What you should be able to do |
| --- | --- | --- |
| Decide whether to adopt | [Installation](getting-started/installation.md) | Understand the prerequisites, confirmation points, and evidence produced. |
| Start using it | [First Calibration](getting-started/first-calibration.md) → [First Work Item](getting-started/first-work-item.md) | Create the first bounded task from a trusted base. |
| Understand the security boundary | [Injection Boundary](security/injection-boundary.md) | Distinguish Cockpit governance from external security controls. |
| Review a result | [Quality Gates](operations/quality-gates.md) → [Cockpit Status](reference/how-to-read-cockpit-status.md) | Read checks and evidence without treating agent prose as proof. |
| Recover from a stop | [Recovery](operations/recovery.md) | Preserve the Work Item and retry only after the missing evidence is repaired. |
| Maintain or audit the system | [Documentation Architecture](reference/documentation-architecture.md) | Find canonical owners, language policy, and reference depth. |

The home keeps the guided path short: understand the project first, then move to
technical reference. Important topics are intended to have Chinese and Japanese
routes as well as English. A route that is missing or still being migrated is
labelled as such; it must not be read as evidence that multilingual coverage is
complete. Current boundary: the active P1 technical references for commands and
schemas are English-only canonical routes, and the active P2 documentation
authority reference is not translated by default. These are explicit
language-policy boundaries, not evidence that all documentation has complete multilingual
coverage. See the [documentation architecture](reference/documentation-architecture.md)
for the exact P0/P1/P2 policy and the [capability matrix](reference/capability-truth-matrix.md)
for current claims.
