---
author: Codex
title: "WI-16 Outcome Human Handoff"
description: "Design for evidence-complete, locale-bound Outcome delivery to every agent conversation."
status: historical
authority: implementation_record
lastVerifiedBy: wi-16-outcome-human-handoff
---

# WI-16 Outcome Human Handoff

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Problem

The current Task Outcome pipeline persists a valid JSON/Markdown artifact and
prints a localized direct report, but the report often contains only file paths
and a generic warning. Verification results, completed work, retained limits,
residual risks, and red-gate causes are not projected into a compact human
handoff. The locale is a CLI rendering choice rather than a bound Outcome fact.

## Design

Keep the existing Outcome sections as the canonical fact source and add a
versioned `humanHandoff` projection to the generated Outcome. It contains the
requested locale plus explicit `completed`, `passed`, `retained`, `risks`, and
`redReasons` arrays. Each item has human-readable detail and evidence
references; red reasons additionally identify the failed gate, cause,
location, and recovery condition. The projection is derived only from the
Contract, Summary, verification records, and persisted failure evidence.

`ai-finish` will construct the projection before rendering both the active
Outcome and the direct conversation report. A missing or unsupported locale
fails closed; no silent language fallback is allowed. The Make entrypoint and
agent rules will require the conversation language to be passed explicitly,
so Codex, Gemini, Claude, and other agents use the same governed path.

## Data flow and boundaries

1. Contract declares the Outcome handoff requirement, locale boundary, and
   generated paths.
2. Summary records changed-file reasons, verification results, known gaps,
   residual risks, and any failed gate.
3. `ai-finish` derives `humanHandoff`, validates it with the Outcome validator,
   renders the requested locale, and emits the direct report before archive.
4. Human Benefit Report and localized derived views consume the same Outcome;
   they do not invent or translate evidence prose.

Historical archive bundles remain immutable and are not backfilled. New
generator output is versioned so old archived Outcomes remain readable.

## Failure behavior

- Missing/unsupported locale: fail closed before archive and preserve a red
  blocked Outcome with the recovery command.
- Completed verification with known gaps: yellow Outcome; retained items and
  risks are shown explicitly, with no completion overclaim.
- Failed verification or stop: red Outcome; `redReasons` is non-empty and
  names the gate, cause, evidence location, and recovery.
- Empty completed/passed evidence: fail closed unless the source explicitly
  records that the item is not applicable with a reason.

## Verification

Focused tests cover green/yellow/red projections, verification and risk
binding, locale rejection, direct-report language parity, schema/Markdown
parity, and all-agent Make/skill forwarding. Full repository quality and the
normal archive/PR/hosted/closure lifecycle remain mandatory.
