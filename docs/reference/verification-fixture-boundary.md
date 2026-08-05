---
author: Ray
title: Verification Fixture Boundary
description: Source and runtime-state boundary for isolated repository verification fixtures.
---

# Verification Fixture Boundary

Tests that create an isolated copy of the AI Cockpit repository use
`tests/repository_fixture.py`. The fixture contains repository source inputs,
not local runtime state. In particular, it excludes `.git`, `.worktrees`,
virtual environments, build outputs, and Python/tool caches.

Retained `.worktrees` may contain active or historical governed Work Items.
They remain in the source checkout and are never deleted or copied merely to
reduce local runtime. A fixture result is local repository-test evidence;
it is not provider, hosted-CI, adopter, or production evidence.
