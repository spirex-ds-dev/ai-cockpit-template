---
author: Ray
title: "Why AI Cockpit exists"
description: "The problem AI Cockpit solves and the human decision it is designed to support."
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, purpose, north-star, human-agent-trust]
---

# Why AI Cockpit exists

## Purpose

This page answers one question: **why should a person use AI Cockpit before an AI agent changes a repository?**

## Audience

Read this first if you are deciding whether the project is appropriate for your team, or if you need to explain it to someone who does not write code.

## Outcome

After reading, you should be able to describe the problem, the North Star, and the boundary between what AI Cockpit governs and what a human or external tool must still control.

## Scenario

An agent proposes a small documentation change. The explanation sounds reasonable, but the request does not say which files may change, the tests are not named, and nobody can tell whether the branch is safe to merge. AI Cockpit makes those questions visible before the change silently becomes the team's responsibility.

## Explanation

AI-assisted development is fast, but speed can hide uncertainty. An agent may misunderstand the request, expand the scope, skip a check, or present a confident explanation without the evidence a reviewer needs.

AI Cockpit is a **Repository Governance Layer**. It turns a human request into a bounded Work Item, connects the intended scope to reviewable evidence, and returns control to a human when the evidence is missing, stale, contradictory, or risky.

Its North Star is **Calibrated Human-Agent Trust**. That does not mean trusting an agent as much as possible. It means relying on the agent when evidence supports reliance, and making investigation, intervention, or stopping clear when evidence does not.

The mechanism is **Evidence Governance**. The project governs evidence; it does not replace the tools that produce tests, coverage, SBOMs, vulnerability scans, provenance, signatures, or provider attestations.

```text
Human intent → bounded Contract → change → evidence → human decision
```

## Action or decision

Use AI Cockpit when a change needs a visible boundary, reproducible checks, and an accountable human decision. If your need is an agent runtime, workflow engine, security sandbox, identity provider, or enterprise compliance system, choose the separate tool responsible for that capability.

## Stop conditions

Do not treat an agent's prose, a green-looking status, or a file that merely exists as proof. Stop and investigate when the request, scope, authority, evidence, or external control is unclear.

## Next steps

1. [Design philosophy](philosophy/design-philosophy.md) — the principles that keep controls proportional and evidence-led.
2. [Architecture](architecture.md) — how intent becomes reviewable evidence.
3. [Capability boundaries](capabilities.md) — what the repository can and cannot claim.

## Technical depth

The governed path is `Intent → Contract → Implementation → Verification → Summary → Cockpit → Human Decision`. Native Governance Evidence is produced by this repository; Delegated Domain Evidence is produced by independent tools or providers. The [Human-Agent Trust Layer](trust-layer.md) gives the complete evidence and recovery boundary.
