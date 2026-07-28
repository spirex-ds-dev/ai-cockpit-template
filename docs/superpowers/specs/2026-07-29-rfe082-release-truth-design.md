---
author: Ray
title: "RFE-082 Release Truth Reconciliation Design"
description: Separate immutable tag reservation, provider publication, repository projections, and final source binding.
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# RFE-082 Release Truth Reconciliation Design

## Problem

The release model currently uses “highest public tag” for two different facts.
A Git tag reserves a semantic version even when no stable GitHub Release
exists, while a stable provider Release is a publication record. The
repository additionally keeps `release.json` as its published projection and
`next-release.json` as an unpublished candidate. Treating these four states as
one identity left v0.5.44 both reserved and reusable, left a stale candidate
source SHA in canonical state, and produced misleading public-release
diagnostics.

Provider evidence at implementation start shows:

- v0.5.43 is the latest stable GitHub Release;
- v0.5.44 exists as an immutable Git tag but has no GitHub Release;
- `release.json` remains the last repository projection at v0.5.42;
- the existing v0.5.43/v0.5.44 paths are not claimed as verified installable
  distributions;
- obsolete PR #401 still exposes an archived, unmerged recovery branch.

## Fact model

Remote semantic tags are the version-reservation set. Stable provider Releases
are discovered separately and exclude drafts, prereleases, malformed payloads,
and non-semantic names. Diagnostics name both facts; no tag is described as a
published Release merely because `git ls-remote` returned it.

`release-state.json` records unavailable versions between the repository
published projection and candidate. Each quarantine entry has a tag, reason,
and evidence reference. The candidate must be exactly one patch after the
highest of the published projection and unavailable versions, and it may not
reuse any reserved tag.

## Source binding

At `candidate_prepared`, the final release source does not exist yet because
later Work Items will change main. Canonical state therefore records
`sourceBinding: deferred_to_release_finalization` and a null `sourceCommit`.
Only verified/published states may claim an exact source SHA. The later release
workflow remains responsible for binding source commit, tag target, metadata
commit, archive, freeze, digests, SBOM, provenance, and provider evidence.

## Obsolete path retirement

PR #401 is closed with a replacement explanation. Its exact local and remote
work branch are deleted, while the closed PR and archived evidence remain
available for audit. No commit from #401 is cherry-picked or merged into the
replacement Work Item.

## Failure behavior

- malformed provider Release payloads fail closed;
- a candidate equal to a reserved tag fails closed;
- duplicate, unsorted, malformed, or unexplained quarantine facts fail closed;
- ordinary distribution diagnostics distinguish stale projection, latest
  stable Release, and highest reserved tag;
- final preflight remains blocked until the later release Work Item generates
  exact-source evidence.

## Non-claims

- This Work Item does not publish v0.5.45.
- It does not validate v0.5.43 or v0.5.44 as installable.
- It does not modify or delete any semantic-version tag, Release, or asset.
- It does not generate final release freeze or digest evidence.
