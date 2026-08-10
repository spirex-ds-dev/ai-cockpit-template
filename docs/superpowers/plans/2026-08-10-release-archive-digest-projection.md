---
title: Release archive digest projection correction
author: Ray
description: Historical implementation record for source-bound release archive digest correction.
status: historical-record
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Problem

The v0.5.52 Draft asset carried a source-bound v0.5.52 digest while the
archive embedded the historical v0.5.48 digest. Draft Quick Install correctly
failed before publication.

## Correction

Generate the source-bound digest, project it into the Git-selected archive
worktree, serialize the archive from those bytes, and compare the extracted
archive manifest with the Draft asset before publication.

## Verification

Run focused archive, workflow, and distribution regressions; full release
quality; hosted PR checks; a corrective public release; and a clean adopter
installation. The failed Draft/tag is handled only under the Contract's
identity-bound destructive authorization.
