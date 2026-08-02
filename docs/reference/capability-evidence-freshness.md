---
author: Ray
title: "Capability Evidence Freshness"
description: "How local Capability Truth evidence expires and binds to its observed environment."
audience: adopter
status: current
authority: reference
lastVerifiedBy: capability-expiration-environment-binding
---

# Capability Evidence Freshness

Capability Truth rows are not permanent evidence. Each generated row records
`verifiedAt`, `validUntil`, its bounded local `environment`, the evidence
`scope`, and `evidenceFreshness`. A record is stale when its expiry passes or
its environment does not match the current local runtime. Missing or malformed
freshness data is stale.

The existing byte-bound evidence inventory remains required: a changed source
or test file invalidates the row even before its time window expires. A fresh
re-verification regenerates the record and may restore a repository-local
claim only after its source and tests are again current.

This mechanism does not inspect a provider and cannot prove identity, branch
protection, independent review, authorization, or any external enterprise
control. Those remain `not_verified` unless separately observed with
provider-bound evidence.
