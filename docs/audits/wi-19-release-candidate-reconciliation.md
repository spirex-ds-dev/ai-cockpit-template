---
author: Ray
title: "WI-19 Release Candidate Reconciliation Audit"
description: Evidence-bound audit for the reserved v0.5.61 candidate and the v0.5.62 successor.
keywords:
  - ai-cockpit
  - audit
  - release
  - evidence
---

# WI-19 Release Candidate Reconciliation Audit

## Purpose

WI-18 attempted the candidate `v0.5.61`. The provider already exposes that version as an immutable release, so the release workflow failed closed before mutation. Historical Work Item archives are referenced, not rewritten.

## Evidence and resolution

- Provider v0.5.61 targets `a3ed6e5fe052e4100151b788c5541c87cbc84cb2` and is immutable. It is recorded as reserved evidence; the tag is not moved or deleted.
- The provider `release.json` and `release-digests.json` were downloaded and synchronized through `scripts/sync_published_release_projection.py`.
- The repository now records `v0.5.61` as the published projection and advances the next candidate to `v0.5.62`. Installer and version projections use the same candidate value.
- Local publication is not claimed for `v0.5.62`. Exact-source rehearsal, provider assets, and Quick Install receipt remain required evidence.

Evidence refs: `https://github.com/spirex-ds-dev/ai-cockpit-template/releases/tag/v0.5.61`, `command://release-rehearsal-31957662456`, `command://sync-published-release-projection-v0.5.61`, `release.json`, `release-state.json`, `next-release.json`, `.ai/cockpit/version.json`, `.ai/cockpit/release-digests.json`, `install.sh`.

## Boundary

The corrective Work Item does not create, move, or delete an existing immutable tag; rewrite WI-01–WI-18 archives; or change unrelated runtime behavior. Any statement about future v0.5.62 publication is a pending dependency, not a completed fact.
