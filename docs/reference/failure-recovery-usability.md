---
author: Ray
title: "Failure recovery usability"
description: "A complete, user-readable recovery record for governed operation failures."
status: "active"
---

# Failure recovery usability

Recovery guidance is a report for the person running the operation, not a
pointer to implementation source. For each supported failure scenario it must
state the current state, writes performed, what rolled back, what remains, one
safe next command, and whether a human must intervene.

`scripts/ai_recovery_usability.py` validates this minimum record for nine
ordinary failure modes: interrupted installation, failed upgrade, a leftover
lock, branch recovery failure, conflict, incomplete closure, stale evidence,
unknown source, and an unavailable provider. Missing or malformed information
fails closed rather than presenting an ambiguous retry path.

The component intentionally does not operate a provider or claim that local
fixtures prove provider recovery. A provider-unavailable record should keep
the external state explicit and set `humanInterventionRequired` when the
operator cannot continue safely.

## Required report fields

| Field | User-facing meaning |
| --- | --- |
| `currentState` | What is known at the stop point. |
| `writesPerformed` | Local or remote state that was written. |
| `rolledBack` | State safely restored by the operation. |
| `notRolledBack` | State that still needs attention. |
| `nextCommand` | The single safe command to run next. |
| `humanInterventionRequired` | Whether the user must stop and involve an owner. |

Use `render_recovery_report` to present these facts in a stable, readable
form. It never converts uncertainty into a success claim.
