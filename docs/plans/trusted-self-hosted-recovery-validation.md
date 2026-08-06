---
author: Codex
title: "Trusted Self-hosted Recovery Validation"
description: Design boundary for temporary maintainer-dispatched self-hosted diagnostics.
keywords:
  - ai-cockpit
  - self-hosted-runner
  - ci
  - recovery
---

# Trusted self-hosted recovery validation

## Decision

Add a default-off `recovery_diagnostic` job to the existing
`compatibility.yml` manual-dispatch surface for maintainer-initiated diagnostic
validation while GitHub-hosted Actions capacity is unavailable. GitHub does
not discover a new manually dispatched workflow until it exists on the default
branch, so a separate recovery workflow cannot unblock the current outage. The
existing push/pull-request compatibility matrix, `smoke.yml`, `release.yml`,
required checks, branch protection, and release evidence rules remain unchanged.

The selected approach is deliberately narrower than rerouting compatibility:

| Option | Decision | Reason |
| --- | --- | --- |
| Wait for GitHub-hosted runners | Rejected | It leaves development feedback unavailable during a provider outage. |
| Add hosted-runner labels to the Mac runner | Rejected | A macOS host must not impersonate an Ubuntu matrix lane; that would invalidate cross-platform evidence. |
| Default-off compatibility dispatch diagnostic job | Selected | Uses an already registered manual-dispatch workflow while preserving the authoritative hosted gate. |

## Workflow contract

`compatibility.yml` will expose a default-off boolean `recovery_diagnostic`
input under `workflow_dispatch`. The isolated job will run only when that input
is true, check out and verify the immutable dispatched `github.sha`, and use
`contents: read` permissions. Its condition excludes `push` and
`pull_request`, so untrusted public PR code cannot cause execution on the
personal machine.

Its sole job will require all of these labels:

```yaml
runs-on: [self-hosted, macOS, X64, ai-cockpit-recovery]
```

The job will check out the dispatched commit, confirm that `HEAD` equals that
commit, run the repository's macOS-supported `make quality` command under the
job timeout, and publish a red/green diagnostic summary. The summary must say
that the result is **diagnostic, non-release, and cannot satisfy compatibility,
merge, or release gates**. A failure remains a workflow failure; it is not
converted to a warning or a successful outcome.

The runner is repository runner 21 (`ai-cockpit-template`). Its verified labels
are `self-hosted`, `macOS`, `X64`, and the dedicated custom label
`ai-cockpit-recovery`. The workflow does not register, delete, or manage the
runner service.

## Evidence and recovery sequence

1. A maintainer dispatches `compatibility.yml` at the maintenance branch with
   `recovery_diagnostic=true`.
2. The run URL, dispatched SHA, checked-out SHA, command result, and diagnostic
   classification are recorded in the relevant active Work Item Summary.
3. A green diagnostic run permits continued development feedback only. It does
   not permit merge, archive mutation, release, or Work Item closure.
4. After GitHub-hosted Actions recovers, the exact candidate SHA must again pass
   the normal hosted smoke and compatibility requirements before merge or
   release proceeds.

## Regression protection

`tests/test_workflows.py` will assert the default-off dispatch condition, exact
label array, fixed-source checkout verification, diagnostic wording, and
preservation of existing compatibility triggers. The operational quality-gate
document will repeat the security boundary and dispatch procedure.

## Failure handling

If the recovery run cannot start, cannot find the dedicated runner, cannot
check out the requested SHA, or fails quality, it produces a red diagnostic
result. The associated Work Item records the failed gate and recovery
condition. No result may be copied into hosted evidence or used to override a
blocked PR.
