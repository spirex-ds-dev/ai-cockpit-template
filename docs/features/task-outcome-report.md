---
author: Ray
title: Task Outcome Report
description: Evidence-backed reporting of what AI Cockpit changed, found, prevented, and left for human review.
---

# Task Outcome Report

Task Outcome answers “what value and evidence did AI Cockpit provide for this Work Item?” It is separate from Cockpit Status, which answers “can execution continue?”, and from the PR Summary, which is an optional sanitized reviewer presentation.

## Sources and structure

Machine truth is `.ai/work-items/active/<task>.outcome.json`. Its Markdown view is derived at `.ai/work-items/active/<task>.outcome.md`; archived Work Items retain the corresponding `outcome.json` and `outcome.md`. The pre-merge Outcome is rebuilt from Contract, Summary, verification, guards, risks, checkpoints, human confirmations, stops/resumes, changed files, tests, and archive evidence. It binds the exact base and Work Item head, and explicitly records that provider PR facts do not yet exist.

The report contains these sections: Outcome Summary, Task Overview, Delivered Changes, Findings, Risks, Warnings, Interventions, Forced Stops, Resolutions, Recurrence Prevention, Avoided Impact, Residual Risks, Human Decisions, and Evidence. Empty sections say `None`. Findings are evidence-backed and categorized; risks distinguish observed problems, potential risks, and prevented events. A Resolution links Problem → Action → Verification → Result.

## Warning color semantics

`knownGaps` means an intentionally unaddressed requirement. Each genuine known gap becomes a Warning with a limitation binding and makes an otherwise completed Outcome `completed_with_warnings` (yellow). It must not be used as free-form completion commentary.

For an evidence-backed fact that is not an unresolved requirement—for example, that hosted verification is not required by the active Contract—use the optional Summary `nonRiskExplanations` field. Finish carries that structured explanation into the Non-Risk Explanations section without adding a Warning, limitation, or yellow status. The field requires a statement, reason, and source/subject evidence reference; malformed entries fail Summary validation. Failed verification, blocked states, residual risks, and genuine gaps retain their existing warning or red behavior.

## Safety and privacy

Task Outcome does not manufacture scores, productivity, time, money, percentages, or trust claims. Avoided Impact is conditional and requires Finding/Risk/Intervention/Stop/Resolution/Test evidence. Residual and accepted risks remain visible. Secrets, credentials, private keys, and unnecessary evidence details do not belong in the PR presentation.

The full report is not copied into Cockpit Status or a pull request. The PR fragment is opt-in through Project Profile reporting policy and uses an allowlist. Provider PR state and release evidence remain platform or release evidence; Markdown presentation is not proof of merge, publication, or security assurance.

## Language

Project Profile `reporting.defaultLanguage` selects the default locale. `reporting.taskOutcome.languages` may explicitly select `ja`, `en`, and/or `zh-CN` (supported aliases are normalized and unsupported values fail closed). The renderer writes only the configured `outcome.<locale>.md` files. JSON keys and the fact source remain English and are not duplicated per language; user-provided evidence prose is not silently translated or replaced by a fallback language.

## Lifecycle

`ai-finish` first validates deterministic active-evidence readiness, including Summary documentation alignment and ownership, before it starts an expensive required quality route. If that readiness check fails, it immediately persists the canonical blocked/red Outcome with the failed gate and recovery condition; it does not run quality merely to rediscover an archive-blocking evidence defect. After quality and Outcome/report generation, Finish validates the same documentation alignment again so later self-referential mutations cannot make a completed state stale. Archive moves Outcome artifacts transactionally with the Work Item. Event corrections are append-only.

After the PR has merged, `make ai-close-work-item TASK=<task>` verifies provider ownership, base synchronization, and cleanup facts, then generates and validates a separate Closure Receipt before either Work Item branch is deleted. The receipt names the archived Outcome, merged PR, merge commit, final base commit, cleanup intent, and the worktree from which the next Work Item may continue. A missing or invalid Outcome/Receipt fails closed. The assistant must surface that receipt in its Work Item completion report; it is not a replacement for provider evidence.

This rule applies prospectively. Historical archive bundles are not rewritten merely to add a newer report format.

See [Task Outcome Report Self-Check](task-outcome-report-self-check.md) for the current implementation boundary and known gaps.
