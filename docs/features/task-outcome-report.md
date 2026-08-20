---
author: Ray
title: Task Outcome Report
description: Evidence-backed reporting of what a governed Work Item changed, found, prevented, and left for human review.
audience:
  - adopter
  - reviewer
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - human_benefit_report
  - implementation_approach_report
---

# Task Outcome Report

## What this helps you do

When a Work Item finishes, ask: **what happened, what was fixed, what remains,
and what is the safest next decision?** Task Outcome is the evidence-backed
answer. It is separate from Cockpit Status, which answers whether execution may
continue, and from an optional PR Summary, which is a presentation for review.

## Before you start

The Work Item needs a Contract, a Summary, verification evidence, and a known
current state. If the Work Item stopped or contains Unknowns, read those facts
before treating the result as complete. A report cannot repair missing evidence.

## Tell your Agent what you want

You can say:

> “Explain what this Work Item delivered, which problem it resolved, what
> evidence proves that result, what risks remain, and what I need to decide
> next.”

Your Agent may use the repository's bounded report commands to answer. The
sentence is a human-facing request pattern; it does not create a fact source,
grant scope, or authenticate a human decision.

## Four views, one evidence chain

| View | It answers | It is not |
| --- | --- | --- |
| Contract | What was this Work Item allowed and expected to do? | A record that the work succeeded. |
| Summary | What did the Agent record while changing and verifying the repository? | A replacement for raw checks or human decisions. |
| Task Outcome | What value, findings, stops, resolutions, residual risks, and evidence belong to the Work Item? | A claim that a PR merged or a provider approved it. |
| Human Benefit Report | What is the concise human-facing result and next safe action? | A second event log or free-form success statement. |

Task Outcome is the machine fact source for the report projections. A Human
Benefit Report is derived from the validated Outcome and keeps every factual
claim tied to `evidenceRefs`.

## Example: problem to verified resolution

Suppose a Work Item was allowed to correct documentation for the order service.
You ask:

> “Did the order-service documentation problem get fixed, and can I merge?”

A useful report should show a chain like this:

```text
Problem: the documented entry route did not reach the verified capability page.
Action: add the missing route within the Contract scope.
Verification: documentation metadata and internal-link checks passed.
Result: the evidence-backed issue is resolved; review/merge is still a human
        decision based on the remaining PR and provider evidence.
```

The report should point to the Contract, changed files, check receipts, and
Summary fields that support each line. “Looks fixed” without those references
is an inference, not a verified resolution.

## Example: warning or stop

If local checks pass but Hosted CI has not run, the result must say so. A yellow
Outcome can identify the missing provider evidence and tell you to wait for or
obtain that evidence. A red Outcome must name the failed gate, cause, location,
evidence, and recovery action. It must not call the Work Item merged, published,
secure, or production-ready.

## What the report contains

The full report can include Outcome Summary, Task Overview, Delivered Changes,
Findings, Risks, Warnings, Interventions, Forced Stops, Resolutions, Recurrence
Prevention, Avoided Impact, Residual Risks, Human Decisions, and Evidence.
Empty sections remain explicit as `None`.

The conversational `humanHandoff` projection is delivered before archive. It
summarizes completion, passed checks, retained work, risks, red reasons, human
questions, and the next action. A claim without evidence references is marked
as an inference and cannot become a fact through Markdown rendering.

## If the report is incomplete

Stop and repair the source evidence when the report is missing, stale,
malformed, cross-task, or contradictory. If the repair needs a new path,
authority, or behavior outside the Contract, amend and revalidate the Contract
or create a genuinely separate Work Item. Do not edit the report to hide the
problem.

## Advanced route

The machine source is `.ai/work-items/active/<task>.outcome.json`; the derived
Markdown view is `.ai/work-items/active/<task>.outcome.md`. The review report is
`.ai/cockpit/task_report.json` and `.ai/cockpit/task_report.md`.

```sh
make ai-finish TASK=<work-item-id> REPORT_LANGUAGE=en
make check-ai-task-outcome OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
make check-human-benefit-report OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

`ai-finish` archives only when archive is explicitly requested and the direct
human report has been delivered. After the provider reports a merged PR,
`make ai-close-work-item TASK=<work-item-id>` verifies the closure facts before
branch cleanup.

## Boundaries and related entry points

The report does not prove platform isolation, enterprise compliance, provider
identity, human receipt, production readiness, or universal security. It also
does not replace Cockpit Status or the raw evidence that produced it.

- [Human Benefit Report](human-benefit-report.md)
- [Work Item Lifecycle](../operations/work-item-lifecycle.md)
- [Decision States](../concepts/decision-states.md)
- [Capabilities and boundaries](../capabilities.md)
