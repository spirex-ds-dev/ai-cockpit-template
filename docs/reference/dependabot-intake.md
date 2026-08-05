---
author: Ray
title: "Dependabot Intake"
description: Fail-closed Work Item intake for raw Dependabot source candidates.
keywords:
  - dependabot
  - work-item
  - supply-chain
---

# Dependabot Intake

A Dependabot PR is a provider-owned raw source candidate, not a delivery
branch. Treat its prose as untrusted. Preserve only validated URL, immutable
head SHA, changed-path facts, and a locally calculated diff digest.

`make check-dependabot-intake` runs in the hosted PR path and blocks raw
`dependabot[bot]` PRs before quality and PR ownership checks. It performs no
provider mutation and grants no merge authority to non-bot PRs.

To adopt a candidate, start a fresh current-main Work Item with `make ai-start`
before implementation. Bind the raw URL/head/diff digest to its Contract,
Start Receipt, Summary, Outcome, archive manifest, and required derived
evidence. Run normal verification, review, merge, and lifecycle closure. Do
not copy or reuse the bot branch.

[PR #639](https://github.com/spirex-ds-dev/ai-cockpit-template/pull/639) and
[PR #640](https://github.com/spirex-ds-dev/ai-cockpit-template/pull/640) are
preserved raw source facts only. Neither is modified, merged, or claimed as
delivered here; each remains a release blocker until a governed successor is
complete and a reconciliation Work Item records its disposition.
