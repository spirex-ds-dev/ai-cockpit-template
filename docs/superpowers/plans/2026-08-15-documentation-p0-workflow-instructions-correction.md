---
author: Ray
title: "P0 workflow instruction correction"
description: "Correct canonical before-edit and archive lifecycle commands in the three first Work Item guides."
status: historical
authority: implementation_record
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# P0 Workflow Instruction Correction

## Goal

Make the English, Japanese, and Simplified Chinese first Work Item guides executable against the repository's canonical workflow.

## Scope

- Replace the generic `ai-checkpoint STAGE=before_edit` instruction with `make ai-prepare-implementation CONTRACT=... SUMMARY=...`.
- Show `make ai-finish TASK=... ARCHIVE=true` and distinguish finish/archive from post-merge closure.
- Preserve the required order: archive, commit, push, PR, merge, then `ai-close-work-item`.
- Add regression tests that bind the three pages to the command and ordering contract.

## Verification

Run the focused workflow-instruction test, all declared AI Cockpit checks, and strict documentation quality before opening the PR.
