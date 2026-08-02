---
author: Ray
title: "Provider Evidence Boundary"
description: Provider governance controls remain external evidence and are not locally collected or claimed.
audience:
  - maintainer
  - auditor
status: reference
authority: explanatory
lastVerifiedBy: remove-cancelled-provider-validation
keywords:
  - ai-cockpit
  - provider-evidence
  - evidence-boundary
---

# Provider Evidence Boundary

`provider-backed-governance-validation` was removed from the active plan.
AI Cockpit does not include a local collector for Provider configuration,
branch protection, reviewer identity, or other hosted-provider controls.

Those controls are external dependencies. A local Work Item must record them
as `not_run`, `not_claimed`, or `external_dependency` unless an independently
authorized external evidence source is available. This repository must not claim
that Provider governance has been verified merely because local quality checks pass.
