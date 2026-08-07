---
author: Ray
title: "Dependabot Intake"
description: Fail-closed Work Item intake for raw Dependabot source candidates.
---

# Dependabot Intake

A Dependabot PR is a provider-owned source candidate, not a delivery branch.
`make check-dependabot-intake` rejects a raw `dependabot[bot]` PR before quality
and ownership checks, without mutating the provider or authorizing any merge.

To adopt a candidate, start a fresh current-main Work Item and bind the source
URL, immutable head SHA, and diff digest to its Contract, Start Receipt,
Summary, Outcome, archive manifest, and derived evidence. Do not reuse the bot
branch. #639 and #640 remain raw facts until a governed successor closes and
#662 records their terminal disposition.
