---
author: Ray
title: Human Benefit Report
description: A concise evidence-derived explanation of the value, remaining risks, and next human decision for one governed task.
audience:
  - adopter
  - reviewer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - human_benefit_report
  - implementation_approach_report
---

# Human Benefit Report

## What this helps you do

Use this report when you need a short answer for a person: **what was done,
what problems were found, what was resolved, what remains risky, and what
should happen next?** It is the human-facing projection of a validated Task
Outcome.

## Tell your Agent what you want

> “Give me the human handoff for this Work Item. Include completed work,
> blocking problems, resolved problems with evidence, remaining risks,
> unknowns, human decisions, and the next safe action.”

The Agent can present the persisted `humanHandoff`. It must not rewrite an
evidence-free benefit into a fact.

## What the result looks like

The default order is intentionally decision-oriented:

```text
Task Result
Status: Success / Partial / Blocked / Failed

What was completed
Problems found
Stops triggered
Problems resolved
Risks avoided
Remaining risks
Unknowns
Human decisions
Verification
Impact
Next action
```

Counts are evidence-record counts for findings, risks, warnings, and forced
stops. They are not productivity, time, money, security, or trust scores.

## Example

If a documentation link was missing and the Work Item added it, the handoff
should say:

```text
Completed: the missing capability-overview link was added.
Resolved problem: the docs entry now reaches the capability overview.
Evidence: Contract, changed file, and passing documentation-link check.
Remaining risk: Hosted provider review has not yet been confirmed.
Next action: review the PR and wait for the provider result before merge.
```

If the evidence is missing, the wording must remain “reported” or “inference,”
or the result must remain yellow/red. A concise report is not permission to
skip review.

## If the report is missing or stale

Stop and validate the Task Outcome first. The report is invalid when it is
missing, malformed, stale, cross-task, or inconsistent with the archived
Outcome. Repair the source record and regenerate the projection; do not hand
edit the projection to make it look complete.

## Advanced route and lifecycle

`humanHandoff` is derived from `.ai/work-items/active/<task>.outcome.json`.
`ai-finish` writes the Review Report to `.ai/cockpit/task_report.json` and
`.ai/cockpit/task_report.md`. After a provider-confirmed merge,
`ai-close-work-item` writes the Final Report beside the Closure Receipt before
branch cleanup.

```sh
make generate-human-benefit-report \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
make check-human-benefit-report \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

The Review Report cannot prove PR creation, Hosted CI, merge, cleanup, human
receipt, or provider identity. The Final Report can repeat only facts verified
by the closure adapter. Neither report proves platform isolation, enterprise
compliance, or production safety.

See [Task Outcome Report](task-outcome-report.md), [Decision States](../concepts/decision-states.md),
and [Work Item Lifecycle](../operations/work-item-lifecycle.md).
