---
title: Governance Profile Cost Separation
author: Ray
description: Canonical profile intensity and operation-specific verification escalation.
---

# Governance Profile Cost Separation

AI Cockpit has three canonical governance profiles: `light`, `standard`, and
`strict`. The profile describes the intensity appropriate for the change; it
does not encode every operation-specific verification requirement.

Release is an operation class. A Strict Work Item gains `release_preflight` and
`distribution` escalation when its requested operation, resource scope, or
capability claim is release-related. This preserves release evidence while
letting security, CI, migration, and other non-release Strict work avoid the
release graph. `release` is not accepted as a governance profile; declare the
release operation class instead.
