---
author: Ray
title: "Release Code Scanning remediation design"
description: "Trust-boundary remediation for release-workflow CodeQL findings."
status: historical
authority: implementation_record
---

# Release Code Scanning Remediation Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Goal

Remove the untrusted cross-run artifact data flow from release publication while
preserving the requirement that a release has a successful, exact-source
rehearsal before it can publish.

## Selected approach

The publication path will validate the requested rehearsal run only as
repository metadata: successful conclusion, exact source SHA, `release`
workflow identity, and matching run ID. It will not download the rehearsal
receipt or any strict-smoke artifacts from that run.

After this metadata validation, both rehearsal and publication runs dispatch
and wait for their own strict smoke verification. The publication run consumes
only the strict smoke run that it created, instead of taking a run ID, artifact
name, or artifact content from a prior workflow run. The existing rehearsal
receipt is still recorded for audit evidence, but publication no longer relies
on it to reuse evidence.

## Trust boundary

- `rehearsal_run_id` remains an untrusted workflow-dispatch input and must be
  numeric before it is queried.
- The release path verifies that the referenced run is successful and matches
  the current release source before permitting the next step.
- No artifact downloaded from the referenced rehearsal run can influence
  publication or `$GITHUB_ENV`.
- The strict smoke run ID exported to `$GITHUB_ENV` is created by the current
  release workflow and remains numeric-validated before use.

## Error handling

Malformed identifiers, missing runs, a non-successful rehearsal, or a
different source/workflow all fail the job before strict smoke dispatch. A
strict smoke dispatch or wait failure also blocks release publication.

## Verification

`tests/test_release_workflow.py` will assert that the publication path keeps
the exact-source rehearsal metadata check, has no `gh run download` command,
dispatches strict smoke for every run, and retains the public-side-effect
guards. The focused test and the repository quality suite are required before
review.

## Non-goals

This change does not create a tag, publish a GitHub Release, change release
metadata, or dismiss CodeQL alerts. A patch release decision follows only
after the remediation is merged and the hosted scanner result is available.
