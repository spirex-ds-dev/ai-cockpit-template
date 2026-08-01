---
title: Governance Performance Budgets
author: Ray
description: Source-bound quality performance reporting that preserves required verification.
---

# Governance performance budgets

Quality performance is measured from the receipts emitted by existing quality gates. It is not permission to omit a required gate, and local measurements are not hosted-provider evidence.

Each quality summary includes a `performanceReport` with the selected governance profile when a routing receipt exists, verification escalations and their recorded reasons, category durations, cache accounting, repeated checks, and the slowest step. The report distinguishes `not_configured` from `within_budget`; a no-Contract CI run records `profile: unknown` rather than inferring one.

`scripts/ai_performance_budget.py` derives a profile P95 only after three or more local quality summaries for that profile. Before then the profile state is `collecting`; it must not be presented as an established budget. The report's `measurementSource` remains `local_quality_summaries`.

An over-budget report identifies its measured slowest step. It does not skip, downgrade, or otherwise alter the required quality, security, release, or provider verification graph.
