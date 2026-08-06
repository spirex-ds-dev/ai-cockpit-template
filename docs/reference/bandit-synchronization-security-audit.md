---
author: Ray
title: "Synchronization Bandit Security Audit"
description: "Reviewed Bandit boundary for governed Work Item synchronization."
lastVerifiedBy: "make check-bandit-baseline"
keywords:
  - bandit
  - synchronization
  - security
  - work-item
---

# Synchronization Bandit Security Audit

Issue #694 reported a historical scanner drift from 117 to 123 findings while
the first controlled synchronization delivery was being prepared. The original
123-finding artifact is not part of the current source history and must not be
treated as baseline evidence.

The current, merged synchronization implementation is audited from canonical
`make check-bandit-evidence` output. After replacing the one raw partial
`git` executable invocation in `scripts/ai_resume_work_item.py::_git`, the
reviewed result is **115 LOW findings** with digest
`80327d22bfd0d3d907c7e2611f7cae159915289ed090afbc227cc2f1d3ac067d`.

## Finding inventory

| File | Rule | Code path | Exploitability | Lifecycle impact | Disposition |
| --- | --- | --- | --- | --- | --- |
| `scripts/ai_resume_work_item.py` | B404 | `import subprocess` | The module can start a process, but all synchronization calls use list-form argv. | This module implements local, fail-closed synchronization. | Retained LOW finding. The import is necessary; call sites resolve an absolute executable and have focused regression coverage. |
| `scripts/ai_resume_work_item.py` | B603 | `_git`, `_governed_git`, `_rebase_onto`, `_live_remote_head` and related fixed Git calls | No shell is used. The executable is validated absolute and callers validate the relevant operands before mutation. | A false allow could mutate a local Work Item or suppress its error; each failure still raises `ResumeError`. | Retained only where a narrow `nosec B603` marks the fixed, reviewed list-form boundary. |
| `scripts/ai_resume_work_item.py` | B607 | historical raw `_git` call | A partial executable could be resolved through `PATH`. | Could weaken the process-execution boundary before synchronization state is checked. | Remediated: `_git` now shares `governed_git_executable()` and no B607 result remains for this file. |

There are no unreviewed synchronization-specific additions to the current
baseline. The historical six-finding report is recorded as an incident signal,
not an approval to add findings without reproducible scanner evidence.

## Refresh procedure

Run `make refresh-bandit-baseline` only after the findings have been reviewed.
It first creates canonical `target/quality/bandit.json`, then writes the exact
count and digest from that JSON. `make check-bandit-baseline` rejects any
different scanner result. A baseline refresh is therefore an explicit reviewed
change, never a way to make an unexpected finding disappear.
