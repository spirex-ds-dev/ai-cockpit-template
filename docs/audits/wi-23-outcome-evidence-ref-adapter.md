---
title: "WI-23 Outcome Evidence Reference Adapter Audit"
author: "AI Cockpit"
description: "Evidence-bound audit of the Summary evidenceRefs adapter correction."
workItemId: wi-23-outcome-evidence-ref-adapter
status: in_progress
---

# WI-23 Outcome Evidence Reference Adapter Audit

## Finding

The WI-22 Summary stores observed-issue evidence in `evidenceRefs`, while the pre-merge adapter read only `evidence`. The resulting archived WI-22 Outcome showed top-level `Resolutions: None` despite the source record carrying evidence-bound resolution claims.

## Correction boundary

- `evidenceRefs` is the canonical observed-issue source.
- Legacy `evidence` remains accepted for compatibility.
- Missing or malformed references remain inference and cannot become verified resolutions.
- WI-01 through WI-22 archives are not rewritten.

## Verification plan

The focused integration suite covers `evidenceRefs`, legacy `evidence`, malformed input, and the Outcome validator. Full governed verification and archive-diff evidence must be recorded before finish.
