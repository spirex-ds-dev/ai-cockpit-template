---
author: Ray
title: Task Outcome Events
description: Maintainer reference for append-only Task Outcome event evidence and reconstruction.
---

# Task Outcome Events

Events are append-only evidence at `.ai/work-items/active/<task>.events.jsonl`. Each line is an independent JSON event. Archive moves the file byte-for-byte with the Work Item when it exists.

## Event policy

Supported event families include finding, risk, warning, confirmation, stop, resume, resolution, risk-accepted, check-pass-after-fix, prevention, completed, and cancelled. A correction uses `event_corrected` or `event_superseded`; it never silently edits an earlier event. A post-fix recurrence is a new finding rather than a mutation of the original.

Finding deduplication uses `findingFingerprint`, derived from Checker ID, reason code, affected resource, and Evidence subject. The same fingerprint is deduplicated unless the event explicitly records post-fix recurrence. Event IDs and timestamps provide deterministic ordering; relationships must reference existing event IDs.

## Generation and validation

`scripts/ai_generate_task_outcome.py` reads structured evidence and events, derives findings, resolutions, prevention, conditional Avoided Impact, and residual risk, then emits machine truth and Markdown. `scripts/ai_check_task_outcome.py` validates schema, bindings, provenance, event relationships, JSON/Markdown parity, privacy, conditional language, no-score rules, and residual-risk visibility. `scripts/ai_render_task_outcome.py` and the multilingual renderer are derived views and must not change the JSON source.

When generation or validation fails, raw Evidence remains available and the process cannot claim success. Do not repair an event log by deleting lines or rewriting historical archive evidence. Add a correction or a new Work Item with explicit evidence.

## Review and privacy checklist

Before accepting an Outcome change, verify the Work Item binding, Contract/Summary/Verification digests, base/head commits, PR binding, and archive manifest. Check that each finding and risk has evidence, every stop has a reason and resume decision, accepted residual risk is visible, and avoided impact is conditional. Keep secrets and personal paths out of events. Do not treat event counts as performance targets.

Publication evidence is a separate provider-bound input to the deterministic outcome generator. When available, bind the release URL, tag target SHA, workflow run ID, asset digest, and Quick Install result; do not infer publication from a local candidate state or user authorization. Risk level and authority approval are likewise separate evidence fields.

The Project Profile controls default language and generated locale views. It does not change JSON keys or authorize an unreviewed fallback. Cockpit Status receives only a short status/link/count projection; a PR receives only the approved sanitized summary.

Generator 1.2 additionally derives `humanHandoff` for direct agent-to-human delivery. The projection contains the completed, passed, retained, risk, red-reason, and fixed human-question claims. Each claim carries `evidenceRefs`; evidence-free statements are marked `inference`. The archive boundary requires the localized handoff to be emitted in the conversation before archive, and closure must independently verify clean local worktrees/branches and absence of the remote Work Item branch.
