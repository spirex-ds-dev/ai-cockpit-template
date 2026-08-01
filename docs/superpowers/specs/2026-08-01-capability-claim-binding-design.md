---
author: Ray
title: "WI06 Capability Claim Binding Design"
description: "Design for binding current public capability language to source-bound matrix evidence."
audience: maintainers
status: current
authority: supporting
lastVerifiedBy: wi-06-capability-claim-binding
---

# WI06 Capability Claim Binding Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Decision

Add one deterministic documentation checker that consumes
`ai_capability_truth.py` and `capability-truth-matrix.json`. The checker does
not own capability state, evidence digests, or a second vocabulary. It is
invoked by the existing `check-docs-metadata` target, so capability binding is
part of the established documentation boundary rather than a new Gate.

## Documents in scope

The checker scans README siblings and current canonical Markdown selected by
front matter. Historical Work Items, implementation records, supporting
evidence, and the generated `capability-truth-matrix.md` projection are not
public claims and are excluded. The projection is exempt because it is a
direct rendering of the machine-readable truth source rather than prose that
independently asserts capability.

## Bindings and wording

Authors bind exact matrix IDs with either YAML `capabilityClaims` list entries
or inline `<!-- capability-claim: id -->` markers. A current public document
that contains a configured English, Japanese, or Simplified Chinese claim term
must have at least one binding. Every binding must exist in a valid matrix and
retain current source/test evidence bytes, a canonical row digest, and a
non-empty limitation.

Rows with `implemented` or `adopter_installed` effective state may support
present-tense language. A `template_only` row also requires explicit prose
that says the template is provided without proving adopter installation. A
`planned` row requires planned or future wording. An `evidence_stale` effective
state supports no public claim.

## Multilingual boundary

Sibling paths are grouped by removing `.ja` or `.zh-CN` before `.md`. When two
or more siblings exist, their complete binding sets must match. This provides
a deterministic scope boundary: translations may differ stylistically, but no
language can silently acquire a broader capability set.

## Failure model

Errors name the document and the missing binding, unknown ID, stale evidence,
state qualifier, or sibling mismatch. Detection is deliberately lexical and
auditable; it does not attempt semantic entailment or machine translation.

## Verification

Focused tests exercise both binding syntaxes, all state rules, invalid and
stale evidence, canonical-document selection, and multilingual parity. A
Makefile test proves composition under the existing documentation check.
