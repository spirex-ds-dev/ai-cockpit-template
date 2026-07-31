---
author: Ray
title: Human Benefit Report Implementation Plan
description: Implement WI04 as a compact evidence-derived view over the existing Task Outcome lifecycle.
---

# Human Benefit Report Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Design boundary

Task Outcome remains the sole machine-truth and event authority. Human Benefit Report is a deterministic, validated projection for human decisions. The review phase may describe repository evidence but cannot claim merge or cleanup. The final phase may add only provider-bound closure facts verified by `ai-close-work-item`.

## Implementation

1. Add a projection and validator that derives issue counts, prevented risks, human decisions, remaining risks, and next safe action from a validated Task Outcome.
2. Render stable JSON and concise Markdown review artifacts under `.ai/cockpit/` during `ai-finish`.
3. Make `check-ai-pr` validate the committed report against the archived Outcome selected from the PR diff.
4. Generate a final JSON/Markdown report beside the Closure Receipt after provider verification and before branch deletion; keep synchronized base clean.
5. Register adopter files and Make entrypoints, then document Review/Final semantics and evidence limitations in English, Japanese, and Simplified Chinese.

## Verification

- Focused unit tests for projection, counts, validation, rendering, malformed/stale input, and safe-action selection.
- Focused `ai-finish`, PR-check, closure, installer, and Makefile integration tests.
- Source-bound documentation generation and the Standard quality graph selected by the Contract.
