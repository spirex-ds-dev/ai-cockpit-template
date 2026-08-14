---
author: Ray
title: "AI Cockpit"
description: Evidence-based repository governance for calibrated human-agent trust.
audience:
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
---

# AI Cockpit

[中文](README.zh-CN.md) | [日本語](README.ja.md)

Start with the [documentation home](docs/README.md) for the reader-first path.

<!-- readme-section: identity -->
## What it is

AI Cockpit is a **Repository Governance Layer** for AI-assisted software
development. It turns repository evidence into bounded decisions a human can
review.

Read the extended [Human-Agent Trust Layer](docs/trust-layer.md) explanation.

<!-- readme-section: problem -->
## The problem it solves

Agents can exceed scope, weaken tests, skip verification, or leave reviewers
without evidence. AI Cockpit makes the intended change, actual diff, required
checks, unknowns, and human decisions explicit.

<!-- readme-section: how-it-works -->
## How it works

```text
Evidence → Governance Decision → Human Control
```

Each change uses one Contract, one branch, one Summary/Outcome, one PR, and a
verified closure. Agent prose alone is not proof.

<!-- readme-section: decision-states -->
## Three decision states

- **Green:** required evidence supports the bounded next action.
- **Yellow:** investigate missing, stale, contradictory, or risky evidence.
- **Red:** stop; a required control failed or authority is absent.

See the [documentation home](docs/README.md) for the decision and recovery path.

<!-- readme-section: quick-start -->
## Start in 30 seconds

Open the target Git project with your coding agent, then follow the
[30-Second Start](docs/getting-started/30-second-start.md). It begins read-only,
resolves a fixed published release, shows the write plan, and asks before the
installation step. For the full path, use [Installation](docs/getting-started/installation.md).

<!-- readme-section: boundary -->
## Product boundary

AI Cockpit is not an Agent Runtime, Workflow Engine, Security Sandbox, general
prompt-injection detector, identity provider, compliance certificate, or
replacement for human review. External identities, branch protection,
production isolation, and release attestations remain external evidence.

Current claims are bounded by the
[Capability Truth Matrix](docs/reference/capability-truth-matrix.md).

<!-- readme-section: documentation -->
## Documentation

Use the [documentation home](docs/README.md) to choose a goal: understand the
project, decide whether to adopt it, start the first governed task, review a
result, recover from a stop, or maintain the system. It then links to the
canonical English, Japanese, or Chinese route where that route is available.
