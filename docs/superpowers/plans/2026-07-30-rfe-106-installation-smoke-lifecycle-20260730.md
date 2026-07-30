---
author: Ray
title: "RFE-106 Installation Smoke Lifecycle Repair"
description: "Repair the installed-adopter smoke fixture so an active Outcome is explicitly archived before the installation commit and strict post-install guards."
---

# RFE-106: Installation smoke lifecycle repair
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Root cause

RFE-104 hosted installation smoke ran `ai-finish`, which correctly retained an
active Outcome. The fixture then evaluated strict coverage against its
pre-install baseline before committing the installed Runtime. The guard
correctly rejected the Runtime scripts because an adopter installation does not
ship the template repository's test suite.

## Corrective plan

1. After `ai-finish`, archive the active installer Work Item explicitly when
   it remains active; in either compatibility state, prove an archive exists
   before the installation commit.
2. Add a source-order regression that rejects archive-after-commit or
   archive-after-coverage-guard ordering.
3. Keep coverage enforcement blocking and do not expand the installer payload
   with template tests.
4. Verify locally, then use hosted installation smoke as the environment proof.

## Boundary

The fixture verifies lifecycle command ordering. It does not claim that a human
received a conversation report; real Work Items still require the agent to
relay their active Outcome directly before archive.
