---
author: Ray
title: "RFE-105 Quality Session Child-Process Cleanup"
description: "Make quality phases own, terminate, and reap their child process groups when a failure or interruption occurs."
---

# RFE-105: quality-session process cleanup

## Problem

A failed quality-fast policy gate returned while a `project-test` descendant
from the same quality invocation remained alive. The next attempt overlapped
with it and both wrote shared coverage output. This invalidated retry evidence.

## Plan

1. Run each quality phase in a dedicated process group.
2. On a non-zero result or interruption, terminate and reap only that group.
3. Preserve phase order, exit status, gate membership, session directories,
   timing logs, JUnit paths, and all diagnostics.
4. Prove failure, interruption, success ordering, Makefile integration, and a
   full clean quality session.

## Boundary

This helper never searches for or kills arbitrary test processes. It acts only
on the process-group leader it created with `start_new_session=True`.
