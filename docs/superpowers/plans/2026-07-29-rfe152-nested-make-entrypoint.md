---
author: Ray
title: "RFE-152 Nested Make Entrypoint Implementation Plan"
description: TDD and governed lifecycle plan for explicit Makefile.ai propagation.
---

# RFE-152 Nested Make Entrypoint Implementation Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Goal

Make the prompt-first, no-root-edit installation path executable for both
direct and composite lifecycle targets while retaining fail-closed Makefile
authority and machine-independent evidence.

## Instruction → plan → implementation → acceptance

| Instruction | Plan | Implementation | Acceptance |
| --- | --- | --- | --- |
| Do not require beginners to edit a root Makefile | Export the actually selected entrypoint | `Makefile`, distributed `Makefile.ai` | No-include adopter completes start and finish |
| Fix the process permanently | Use one validated argv boundary in every caller | `ai_common`, lifecycle callers, recursive recipes | No plain-Make fallback remains |
| Do not create a new bypass | Reject untrusted or conflicting entrypoints | Repository/path/name/file/conflict checks | Negative matrix fails before subprocess execution |
| Prevent omissions | Bind docs and tests to the same boundary marker | Three installation guides and metadata checker | Three-language metadata and mutation checks pass |
| Complete the Work Item lifecycle | Archive, PR, Hosted CI, merge, closure, branch cleanup | Contract, Summary, manifest, PR evidence | Clean synchronized main before RFE-082 |

## Tasks

1. Reproduce the no-include `ai-start` and `ai-finish` failures before changing
   runtime code.
2. Add repository-local entrypoint validation and command construction.
3. Route start, finish, onboarding, hosted snapshot, and recursive Make recipes
   through that constructor/entrypoint.
4. Prove required nested failures remain visible and retryable.
5. Replace the temporary WI-10 composite-integration warning in English,
   Chinese, and Japanese with the implemented propagation boundary.
6. Update metadata checks, traceability, parent issue history, Contract,
   Summary, and documentation registry.
7. Run focused regressions, full quality, `ai-finish`, archive, aggregate PR
   validation, Hosted CI, merge, `ai-close-work-item`, and branch cleanup.

## Non-claims

- This does not execute arbitrary Makefiles.
- This does not modify adopter root Makefiles.
- This does not prove project-specific quality commands are correct.
- RFE-ISSUE-082 and release remain blocked until this lifecycle closes.
