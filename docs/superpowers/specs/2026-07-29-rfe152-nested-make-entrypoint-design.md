---
author: Ray
title: "RFE-152 Nested Make Entrypoint Propagation Design"
description: Repository-local Makefile authority for direct and composite AI Cockpit lifecycle targets.
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# RFE-152 Nested Make Entrypoint Propagation Design

## Problem

`make -f Makefile.ai <target>` previously worked only for a direct target.
Python lifecycle runners and Make recipes started child operations with a new
plain `make`, so an adopter that intentionally left its root Makefile unchanged
lost every AI Cockpit target at the first nested step. Existing end-to-end tests
always installed `include Makefile.ai` and concealed the defect.

## Authority boundary

The selected Make invocation exports `AI_COCKPIT_MAKE_ENTRYPOINT` from the
first parsed `MAKEFILE_LIST` item. `override` prevents an ambient or
command-line value from replacing that fact. The value must resolve to an
existing repository-local standard `GNUmakefile`, `makefile`, `Makefile`, or
`Makefile.ai`; absolute paths, traversal, external symlinks, missing files,
unsupported names, and a conflicting nested `-f`/`--file` selection fail
closed.

The value remains repository-relative. Registered verification commands and
archived Summary evidence remain canonical (`make <target>`) and therefore do
not persist machine paths.

## Propagation

One shared argv constructor inserts `-f <selected-entrypoint>` into nested Make
commands. It is consumed by start, finish, onboarding, and hosted-verification
preparation. Make recipes use one `AI_NESTED_MAKE` command for recursive
preflight, quality, PR, and aggregate checks. No shell command string is
accepted as authority.

When AI Cockpit is included by a root Makefile, the selected entrypoint is the
root `Makefile`. When invoked explicitly, it is `Makefile.ai`. Root integration
is optional in both direct and composite cases.

## Failure behavior

Entrypoint validation happens before child execution. A bad authority produces
an explicit failure; it never silently falls back to plain Make. A nested gate
failure remains a gate failure, preserves the active Work Item, and can be
retried through the same selected entrypoint.

## Verification

Red-first tests use an installed adopter whose root Makefile does not include
AI Cockpit. They cover direct start, composite finish, required-check
failure/retry, archive completion, caller parity, included-root compatibility,
and the full malformed/conflicting entrypoint matrix.
