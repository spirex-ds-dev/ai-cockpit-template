---
author: Ray
title: "Capabilities and boundaries"
description: "A plain-language boundary map for what AI Cockpit can claim and what remains external."
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
keywords: [ai-cockpit, capabilities, boundaries, evidence]
---

# Capabilities and boundaries

AI Cockpit's product boundary is the **Repository Governance Layer**.

## Purpose

This page answers: **what does AI Cockpit control, and what must another person, tool, or provider control?**

## Audience

Read it before adoption, security review, or any claim that a repository check proves a wider property.

## Outcome

You will know which statements are supported by repository evidence, which are template or adopter responsibilities, and which are explicitly out of scope.

## Scenario

An adopter sees a passing local quality check and asks whether that proves production isolation and the agent's identity. It does not. The check supports a bounded repository decision; the external claims need their own evidence from the responsible systems.

## Explanation

### AI Cockpit can govern

- Work Item scope, exclusions, acceptance, and evidence sources.
- Registered checks, change summaries, status signals, human decisions, and archive traceability.
- Known repository-local cases where a gate can deterministically stop or request investigation.

### AI Cockpit cannot prove by itself

- Agent Runtime behavior, general prompt-injection protection, or semantic safety in every language.
- Security Sandbox isolation, identity authentication, branch protection, or immutable external audit.
- Vulnerability absence, enterprise compliance, provider publication, or production readiness.
- An adopter's installation or calibration merely because the template contains the relevant material.

The [Capability Truth Matrix](reference/capability-truth-matrix.md) is the current source for row-level implementation status. Its statuses distinguish `implemented`, `template_only`, `adopter_installed`, and `planned`; prose must not broaden those statuses.

```text
Local governance evidence → bounded repository decision
External/domain evidence → external responsibility and claim
```

## Action or decision

For each important claim, ask: who produces the evidence, which scope does it cover, and what is the safe next action when it is missing? Keep the claim local when this repository can verify it; link to the external owner when it cannot.

## Stop conditions

Stop a merge or adoption decision when a claim has no current evidence, when a `planned` or `template_only` row is described as implemented, or when external responsibility is presented as a local guarantee.

## Next steps

1. [Architecture](architecture.md) — where evidence flows and who owns it.
2. [Decision States](concepts/decision-states.md) — how people act on green, yellow, and red evidence.
3. [Capability Truth Matrix](reference/capability-truth-matrix.md) — row-level evidence and limitations.

## Technical depth

Capability claims are bound to exact matrix IDs and regenerated evidence. A passing check is evidence for its declared scope, not a universal security or compliance statement. Native and Delegated Domain Evidence remain separate so that provenance and responsibility are reconstructable.
