---
author: Ray
title: "Direct-user destructive authorization design"
description: "Design record for bounded direct-user authorization evidence."
audience: maintainers
status: current
authority: supporting
lastVerifiedBy: direct-user-destructive-authorization
---

# Direct-user destructive authorization design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Purpose

Permit a sole authenticated user to delegate an exact destructive repository
cleanup when GitHub rejects self-approval. The resulting evidence must remain
truthfully lower assurance than an independent provider review.

## Decision

Add `direct_user_authorized` as an Approval Evidence identity level. It is
eligible for a destructive Contract only when all of the following are true:

- `approvalType` is `destructive_change`;
- the evidence scope exactly equals `destructiveChangePolicy.allowPatterns`;
- the record has a non-empty actor, direct-user instruction reference,
  ISO-8601 authorization time, and `sha256:` authorization digest;
- `provider` is `null`, and the evidence has neither review IDs nor other
  Provider or enterprise fields.

The validator reports this state as `direct_user_authorized`. It never reports
it as `provider_verified` or `enterprise_verified`.

## Boundaries

Existing `self_declared` and `repository_recorded` records remain ineligible
for destructive work. `provider_verified` and `enterprise_verified` retain
their current requirements. The change does not modify GitHub settings,
reviews, branches, releases, or tags.

## Verification

Focused tests prove the accepted exact record, rejection of each missing or
mismatched binding, and rejection of Provider-like fields. Contract validation
is tested end to end. The Capability Truth matrix and public documentation
state the assurance distinction and limitations.
