---
author: Ray
title: "Comprehensive Japanese Assessment Depth Design"
description: Fail-closed design for the mandatory pre-release Japanese repository-governance assessment.
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# Comprehensive Japanese Assessment Depth Design

## Problem

The existing report can say “zero blockers” after checking a small injection
corpus and the presence of selected words in 11 Japanese documents. That does
not satisfy WI-16. In particular, it does not prove executable Wizard/CLI,
Cockpit Status, PR summary, lifecycle, path/encoding, or object-project
behavior, and release preflight does not consume the result.

## Boundary

This assessment proves only repository-governance behavior that can be bound to
current source, tests, commands, and checked-in evidence. It does not prove a
provider model's general Japanese fluency or replace review by a native
Japanese technical writer.

The assessment process and capability remediation are separate:

1. This corrective makes missing evidence visible and release-blocking.
2. Every blocker receives a stable finding ID and an independent corrective
   Work Item.
3. The report is regenerated after each correction.
4. WI-16 closes only when every in-scope row passes and all corrective
   lifecycles are closed.

## Evidence model

One deterministic JSON object is authoritative. Every matrix row contains:

- stable case and finding identities;
- area and required status;
- observation;
- source evidence;
- test evidence;
- command evidence;
- limitation;
- a digest over the row.

The top-level digest covers the complete object except its own digest.
Markdown is generated only from that object. Check mode compares both
checked-in files byte-for-byte with regenerated output.

## Required domains

- polite and plain Japanese, technical vocabulary, and mixed Japanese/English;
- Markdown, hidden HTML, logs, tool output, nested quotation, encoded input,
  Unicode controls, and Japanese paths/filenames;
- prompt injection, Unknown, human confirmation, absurd/high-risk requests,
  and recovery/STOP preservation;
- executable Wizard/CLI;
- Cockpit Status and PR summary parity;
- Task Outcome parity;
- installation, calibration, upgrade, rollback, uninstall, and recovery;
- complete Japanese engineer documentation;
- explicit non-claim for general model fluency and human translation quality.

Document existence or an English-only test cannot satisfy an executable
Japanese row.

## Release integration

`check-release-preflight` depends on `check-japanese-capability`. A blocking,
missing, or stale report stops release before identity/freeze checks. The gate
is not part of normal `quality-full`, because corrective Work Items must remain
able to run and merge while the release gate is intentionally red.

## Current expected findings

Initial source inspection predicts at least these independently correctable
gaps:

- executable Wizard entrypoints do not consume the Japanese resource layer;
- Cockpit Status has no Japanese derived view/parity evidence;
- PR Task Outcome chrome is English-only;
- no executable Japanese adopter lifecycle fixture covers install through
  rollback/uninstall/recovery;
- the Japanese documentation path has no explicit actionable uninstall
  procedure.

The implementation must derive findings from evidence and must not hard-code a
pass merely to match this prediction.
