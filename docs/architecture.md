---
author: Ray
title: "Architecture"
description: "How AI Cockpit turns intent into bounded evidence and a human decision."
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, architecture, evidence-flow, boundaries]
---

# Architecture

## Purpose

This page answers: **how does a human intention become a reviewable repository decision?**

## Audience

Read it when you need the project map, not a directory tour: adopters, maintainers, and reviewers deciding where evidence or responsibility belongs.

## Outcome

You will understand the main flow, the ownership of evidence, and why some controls remain outside AI Cockpit.

## Scenario

Someone asks an agent to “clean up the docs.” Before any edit, the request becomes a Contract with a scope and acceptance conditions. The agent changes only that boundary; checks produce evidence; a Summary compresses the result; a human decides whether the next action is safe.

## Explanation

```text
Intent → Contract → Implementation → Verification → Summary → Cockpit → Human Decision
```

1. **Intent** explains why the Work Item exists and what constraints matter.
2. **Contract** declares scope, exclusions, acceptance, evidence sources, and required checks before editing.
3. **Implementation** changes only the declared repository surface.
4. **Verification** runs registered checks and records their results.
5. **Summary** preserves changed files, evidence, risks, and limitations.
6. **Cockpit** compresses Repository Truth into a Human Decision State.
7. **Human Decision** chooses proceed, investigate, approve, block, or recover.

Native Governance Evidence—Intent, Contract, verification records, Summary, Status, and Archive—is owned by this repository. Delegated Domain Evidence—tests, coverage, SBOMs, vulnerability scans, provenance, signatures, and provider attestations—is produced by specialist tools or external systems. AI Cockpit can bind and govern delegated evidence; it cannot make that evidence true by repeating it.

The architecture therefore has a deliberate boundary:

```text
Repository Governance Layer | external runtime, identity, sandbox, provider, and enterprise controls
```

The left side makes repository changes reviewable. The right side remains the responsibility of adopters, providers, auditors, or other domain systems.

## Action or decision

Use the flow to decide where a new fact belongs. Put request, scope, verification, and human decisions in the governed Work Item. Put domain-specific proof in the tool that can produce it. Link the two without duplicating ownership.

## Stop conditions

Stop when the requested effect has no declared boundary, when evidence ownership is ambiguous, or when a local record is being used as proof of an external control. Missing links are reasons to investigate, not reasons to guess.

## Next steps

1. [Capability boundaries](capabilities.md) — which claims are local and which remain external.
2. [Human-Agent Trust Layer](trust-layer.md) — evidence, fail-closed control, and recovery.
3. [Installation](getting-started/installation.md) — the adopter path when the boundary is understood.

## Technical depth

The canonical repository boundaries are the Work Item Contract, Scope/Backtrack/Coverage/Review Guards, Verification Registry, AI Change Summary, Cockpit Status, and Archive Manifest. They support human decisions; they do not provide general semantic-risk detection, identity authentication, runtime isolation, immutable audit, or enterprise compliance.
