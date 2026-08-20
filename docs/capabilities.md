---
author: Ray
title: "Capabilities and boundaries"
description: "A scannable capability overview with direct links to natural-language user guides and explicit responsibility boundaries."
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
  - adopter_capability_manifest
  - adopter_work_item_status_interface
  - adopter_governance_cost_metrics
  - adopter_performance_diagnosis
  - human_benefit_report
  - implementation_approach_report
  - implementation_knowledge_query
  - implementation_knowledge_projection
  - work_item_intelligence_interface
keywords: [ai-cockpit, capabilities, boundaries, evidence]
---

# Capabilities and boundaries

This page is the capability overview. Use it as an index: scan the goal,
status, and responsibility boundary, then select **Details**. The linked page
contains the actual user journey, examples, stop conditions, and advanced
commands.

## Purpose

This page answers what AI Cockpit can help a person understand, where each
capability stops, and which detailed page to open next.

## Audience

Read this as an adopter, reviewer, or maintainer who needs a quick capability
map before deciding whether to follow a detailed user journey.

## Outcome

After reading, you should be able to choose a capability by goal, read its
status and responsibility boundary, and know when a human or external system
must take over.

## Scenario

You know the outcome you want—such as understanding a previous implementation,
processing independent Work Items, or recovering from a stop—but do not know
which page or command applies. Start with the index and follow one Details link.

AI Cockpit's product boundary is the **Repository Governance Layer**. It turns
repository evidence into bounded decisions for a Work Item. It is not an Agent Runtime, Workflow Engine, Security Sandbox, identity provider, or replacement for human review.

## Explanation

The status in this table is the adopter capability manifest vocabulary. It is a
truth label for the declared surface, not a universal security, production,
or provider guarantee. The [Capability Truth Matrix](reference/capability-truth-matrix.md)
provides row-level evidence and limitations.

| Capability / user goal | Manifest status | What it helps you do | Boundary or owner | Details |
| --- | --- | --- | --- | --- |
| Capability manifest | `implemented` | See which adopter-facing surfaces are declared and checked together. | The template and installer declare the surface; an adopter still needs its own installation evidence. | [Advanced manifest reference](reference/capability-truth-matrix.md) |
| Work Item Status Interface | `adopter_installed` | Read evidence-derived Work Item status and index data. | It reports a local projection; it does not execute, schedule, or retry tasks. | [Status Interface](reference/work-item-status-interface.md) |
| Governance cost metrics | `adopter_installed` | Understand advisory governance cost signals for a Work Item. | It reports local observability evidence; it is not a productivity, time, money, or trust score. | [Advanced metrics reference](reference/governance-cost-metrics.md) |
| Performance diagnosis | `adopter_installed` | See evidence-backed timing and possible bottlenecks. | It diagnoses recorded timing; it does not promise optimization or a faster run. | [Advanced diagnosis reference](reference/performance-diagnosis.md) |
| Task Outcome and Human Benefit Report | `adopter_installed` | Understand what happened, what was resolved, what remains, and the next safe action. | The Outcome is evidence-derived; the Human Benefit Report is a projection, not a second fact source. | [Outcome and reports](features/task-outcome-report.md) |
| Implementation Knowledge query | `adopter_installed` | Find prior Work Items by exact topic, component, date, commit, or state filters. | The query is read-only, deterministic, and archive-derived; it is not semantic search or RAG. | [Knowledge guide](reference/implementation-knowledge.md) |
| Implementation Knowledge projection | `adopter_installed` | Keep validated implementation records and indexes derived from completed evidence. | Finish and archive evidence own the source; stale or conflicting records fail closed or remain partial/unknown. | [Knowledge guide](reference/implementation-knowledge.md) |
| Work Item problem-resolution boundary | `adopter_installed` | Decide whether a discovered problem belongs in the current Work Item. | Keep the repair in scope when Contract, authority, and base still cover it; otherwise open a separate Work Item. | [Lifecycle and recovery](operations/work-item-lifecycle.md) |
| Template Capability Truth material | `template_only` | Read the evidence model and claim limitations used by the template. | Template material alone does not prove an adopter's installation, calibration, or external assurance. | [Capability Truth Matrix](reference/capability-truth-matrix.md) |
| Implementation Approach report | `adopter_installed` | Read the evidence-bound explanation of how a change was approached. | This is a reserved report surface carried by Summary, Outcome, and Human Benefit Report; it is not agent self-description. | [Outcome and reports](features/task-outcome-report.md) |

## Action or decision

| If you want to… | Start here |
| --- | --- |
| Understand a result and decide what to do next | [Outcome, Summary, and Human Benefit Report](features/task-outcome-report.md) |
| Find a previous verified implementation | [Implementation Knowledge](reference/implementation-knowledge.md) |
| Process independent Work Items at the same time | [Work Item parallel processing](features/work-item-parallelism.md) |
| Read status, recover from a stop, or close a Work Item | [Work Item Lifecycle](operations/work-item-lifecycle.md) |
| Install or update an existing installation | [Upgrade](upgrade.md) |

## How to use this index

Start with a goal, not a command. For example: “I need to know whether the
previous Work Item really fixed the order-service problem.” Follow the matching
Details link, read its stop conditions, and only then use an advanced command if
you need a repeatable local check.

The natural-language request is a human-agent interaction pattern. Your Agent
may translate it into Contract-aware commands; AI Cockpit still evaluates the
declared scope and repository evidence. A sentence does not grant authority,
expand scope, schedule other Work Items, or create external proof.

## Stop conditions

Pause an adoption, merge, or continuation decision when:

- a current status or evidence source is missing, stale, contradictory, or
  outside the declared scope;
- `planned` or `template_only` material is presented as a current adopter
  guarantee;
- an external responsibility is described as a local proof;
  - a capability guide would require a scheduler, retry controller, identity
  provider, security sandbox, or release claim that AI Cockpit does not own.

## Next steps

1. [Task Outcome and Human Benefit Report](features/task-outcome-report.md) — understand a result and its next safe action.
2. [Implementation Knowledge](reference/implementation-knowledge.md) — find a previous evidence-bound implementation.
3. [Work Item parallel processing](features/work-item-parallelism.md) — process independent Work Items safely.
4. [Work Item Lifecycle](operations/work-item-lifecycle.md) — recover, review, and close a Work Item.

## Technical depth

The Chinese and Japanese overview pages preserve the same rows, statuses,
boundaries, and Details routes. Some technical references remain English-only;
they are labelled as advanced fallbacks rather than silently presented as
translated user guidance.

For the evidence contract, read the [Capability Truth Matrix](reference/capability-truth-matrix.md).
For the implementation path, read the [Work Item Lifecycle](operations/work-item-lifecycle.md).
