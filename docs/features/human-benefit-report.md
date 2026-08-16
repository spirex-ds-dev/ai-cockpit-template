---
author: Ray
title: Human Benefit Report
description: A concise evidence-derived explanation of the value and remaining decisions for one governed task.
---

# Human Benefit Report

Human Benefit Report answers what changed, how many evidence-backed issues were detected, which stops occurred, what was resolved, what risk was prevented, which decisions came from a person, what remains unresolved, and the next safe action.

## Default human summary format

The default Markdown projection uses this exact decision order:

```text
Task Result
Status: Success / Partial / Blocked / Failed

What was completed
- ...

Problems found
- Total:
- Blocking:
- Warning:

Stops triggered
- Reason:
- Stage:
- Resolution:

Problems resolved
- Problem:
- Solution:
- Evidence:

Risks avoided
- ...

Remaining risks
- ...

Unknowns
- ...

Human decisions
- ...

Verification
- ...

Impact
- Rework avoided:
- Repeat correction prevented:
- Major risk prevented:

Next action
- ...
```

The JSON projection behind this format is `humanHandoff`. It is derived from the validated Outcome, not authored freehand. Each claim has `evidenceRefs`; evidence-free benefit language is represented as `inference` and cannot be phrased as a fact. This prevents a path-only receipt from being mistaken for a human explanation.

## One fact source, two lifecycle views

The report is a deterministic projection of the validated Task Outcome. It does not introduce another event log or allow free-form agent claims to become evidence.

`ai-finish` writes the Review Report to `.ai/cockpit/task_report.json` and `.ai/cockpit/task_report.md`. `check-ai-pr` compares those files with the archived Task Outcome and fails closed when they are missing, malformed, stale, or inconsistent.

When archive rewrites that Outcome's active paths, the archive transaction regenerates the exact report pair and records both paths in the same archived Summary. Only a complete current archive transaction can own that pair; a missing, stale, malformed, or cross-task report remains unowned.

After provider verification, `ai-close-work-item` writes the Final Report beside the Closure Receipt under `target/task-closure-receipts/` before branch deletion. The Final Report adds the PR URL, merge commit, synchronized base, cleanup intent, and continuation worktree. Writing it outside source history keeps synchronized `main` clean.

## Count semantics

Detected issues count findings, risks, warnings, and forced stops as distinct evidence records. Hard stops and warnings are explicit subsets. Resolved counts use the structured state/result fields; unresolved is the remaining detected count. These are record counts, not unique-root-cause, productivity, security, time, money, or trust scores.

## Evidence boundary

A Review Report cannot prove PR creation, Hosted CI, merge, cleanup, human receipt, or provider identity. A Final Report can repeat only facts already verified by the closure adapter. Neither report proves platform isolation, security, enterprise compliance, or production safety. Missing or contradictory source evidence remains visible and blocks validation rather than being inferred as passed.
