---
author: Ray
title: "Design Philosophy"
description: "The principles that shape AI Cockpit without adding control for its own sake."
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, design-philosophy, evidence, calibrated-trust]
---

# Design Philosophy

## Purpose

This page answers: **what principles should guide a governance control when an agent and a human share a repository?**

## Audience

Read it when you need to judge whether a proposed process, check, or document belongs in AI Cockpit.

## Outcome

You will understand why the project values calibrated trust, evidence over self-declaration, proportional control, and human responsibility.

## Scenario

A team proposes adding a new approval form because it feels safer. The philosophy asks a prior question: what collaboration failure does the form address, what evidence will it produce, and will it reduce uncertainty without creating ceremony that nobody can maintain?

## Explanation

### Discover, do not invent

Each component must answer a real collaboration need. Do not add process merely because a larger checklist looks more complete. Trace a control to the risk and evidence it addresses.

### Follow the North Star

The North Star is **Calibrated Human-Agent Trust**. Trust is calibrated when people can rely on an agent where evidence supports reliance, and can intervene when evidence is missing, stale, contradictory, or insufficient.

### Converge before creating

Architecture should remove unnecessary complexity until the essential structure is visible. Values choose the direction; constraints, evidence, and practice reveal the smallest structure that can support it.

### Respect different responsibilities

People provide intent, authorization, value judgments, and final accountability. Agents are useful for execution, analysis, consistency checks, and organizing evidence. AI Cockpit supports that collaboration; it does not replace human judgment.

### Evidence over self-declaration

An agent's explanation can help a person understand a change, but it is not independent proof. Tests, diffs, approvals, signatures, and external attestations remain evidence only when the responsible tool or provider produces them.

```text
Values → principles → bounded mechanism → evidence → human decision
```

## Action or decision

Keep a control when it makes a known risk and its evidence easier to review. Move it to a specialist tool when it requires runtime isolation, identity, provider policy, or domain-specific proof that this repository does not produce.

## Stop conditions

Stop when a proposed control has no named risk, no evidence-producing path, or a claim broader than its evidence. Never increase trust by hiding uncertainty behind process language.

## Next steps

1. [Architecture](../architecture.md) — the structure that these principles produce.
2. [Capability boundaries](../capabilities.md) — the claims and responsibilities that remain outside.
3. [Human-Agent Trust Layer](../trust-layer.md) — the complete evidence boundary.

## Technical depth

The principles map to layers: North Star/Mission is Calibrated Human-Agent Trust; epistemic principle is Evidence over Self-Declaration; mechanism is Evidence Governance; product boundary is Repository Governance Layer; implementation is Intent, Contract, Verification, Summary, Status, and Archive.
