---
author: Ray
title: Task Outcome Report
description: Evidence-backed reporting of what AI Cockpit changed, found, prevented, and left for human review.
---

# Task Outcome Report

Task Outcome answers “what value and evidence did AI Cockpit provide for this Work Item?” It is separate from Cockpit Status, which answers “can execution continue?”, and from the PR Summary, which is an optional sanitized reviewer presentation.

## Sources and structure

Machine truth is `.ai/work-items/active/<task>.outcome.json`. Its Markdown view is derived at `.ai/work-items/active/<task>.outcome.md`; archived Work Items retain the corresponding `outcome.json` and `outcome.md`. The report is rebuilt from the Contract, Summary, verification, guards, risks, checkpoints, human confirmations, stops/resumes, changed files, tests, reviews, commit/PR binding, and archive manifest.

The report contains these sections: Outcome Summary, Task Overview, Delivered Changes, Findings, Risks, Warnings, Interventions, Forced Stops, Resolutions, Recurrence Prevention, Avoided Impact, Residual Risks, Human Decisions, and Evidence. Empty sections say `None`. Findings are evidence-backed and categorized; risks distinguish observed problems, potential risks, and prevented events. A Resolution links Problem → Action → Verification → Result.

## Safety and privacy

Task Outcome does not manufacture scores, productivity, time, money, percentages, or trust claims. Avoided Impact is conditional and requires Finding/Risk/Intervention/Stop/Resolution/Test evidence. Residual and accepted risks remain visible. Secrets, credentials, private keys, and unnecessary evidence details do not belong in the PR presentation.

The full report is not copied into Cockpit Status or a pull request. The PR fragment is opt-in through Project Profile reporting policy and uses an allowlist. Provider PR state and release evidence remain platform or release evidence; Markdown presentation is not proof of merge, publication, or security assurance.

## Language

Project Profile `reporting.defaultLanguage` selects the default locale. `reporting.taskOutcome.languages` may explicitly select `ja`, `en`, and/or `zh-CN` (supported aliases are normalized and unsupported values fail closed). The renderer writes only the configured `outcome.<locale>.md` files. JSON keys and the fact source remain English and are not duplicated per language; user-provided evidence prose is not silently translated or replaced by a fallback language.

## Lifecycle

`ai-finish` performs final verification, Summary validation, optional Outcome generation/validation, Markdown rendering, Status generation, and presentation before archive. Archive moves Outcome artifacts transactionally with the Work Item. Event corrections are append-only. A completed report does not itself close a Work Item: the PR must merge before `make ai-close-work-item TASK=<task>` can verify ownership, branch cleanup, and base synchronization.

See [Task Outcome Report Self-Check](task-outcome-report-self-check.md) for the current implementation boundary and known gaps.
