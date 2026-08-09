---
author: Ray
title: "Calibration Session Model"
description: "Reference model for stored calibration facts, proposals, confirmation, and activation."
---

# Calibration Session Model

This is a maintainer and auditor reference, not an installation tutorial.

The calibration Runtime records a resumable Session, answers and evidence,
checklist evidence, phase records, and a reviewable proposal. It preserves
Unknown facts rather than inventing them. A proposal is not active policy:
activation remains bound to separate human confirmation and current evidence.

The detailed runtime fields, stale-evidence rules, confirmation boundaries, and
current implementation status are maintained in
[Calibration Session](calibration-session.md) and the
[Capability Truth Matrix](capability-truth-matrix.md). A Work Item records
rationale, acceptance, ownership decisions, and external verification links;
it does not replace the stored calibration facts or prove a person's identity.

While a Session is `in_progress` or `paused`, ordinary Work Item startup is
blocked. The only exception is a Contract- and Start-Receipt-bound corrective
route for repairing a defect discovered in that active Session. It binds the
Session ID, state, and exact bytes digest; limits repairs to Contract-owned
paths; cannot change Session/activation state; and remains yellow in Cockpit
Status until the corrective Work Item completes. See
[Work Item Lifecycle](ai-cockpit-work-item-lifecycle.md#controlled-corrective-route-during-live-calibration)
for the executable declaration and limits.
