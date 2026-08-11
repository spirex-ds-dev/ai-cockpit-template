---
author: Ray
title: "Superseded Advanced-Base Archive Binding Design"
description: Bind an aged superseded archive transaction to the exact remote-default tip.
status: historical
authority: implementation_record
---

# Superseded Advanced-Base Archive Binding Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Problem

An immutable superseded Contract may name a base older than later corrections
already merged to the default branch. Measuring the current archive candidate
from that historical base includes unrelated mainline changes and correctly
fails Contract ownership. Using an arbitrary newer base would hide committed
Work Item changes.

## Decision

Keep the Contract base rule for normal Work Items. For a canonically validated
superseded predecessor only, permit an alternate report base when it equals both
the candidate Head and the uniquely discovered remote-default tracking tip.
This proves every committed byte is already on the trusted base. Measure the
remaining dirty lifecycle transaction normally, treat the successor receipt as
lifecycle-owned, and include its bytes in both content digests.

## Fail-closed boundaries

- Reject a missing, malformed, or mismatched superseded receipt.
- Reject a base different from candidate Head or remote-default tip.
- Reject missing or ambiguous remote-default identity.
- Reject every foreign dirty or untracked path.
- Preserve normal Outcome binding and archive-manifest requirements.
