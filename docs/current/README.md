---
author: Ray
title: "Current Agent Documentation"
description: Canonical default documentation route for AI Cockpit agents.
authority: canonical
instructional: true
status: current
supersededBy:
---

# Current Agent Documentation

This directory is the default documentation read set for an AI Cockpit agent.
Read these canonical, current, instructional documents before treating
documentation as an instruction source. The route does not replace the
repository's governing `AGENTS.md` rules.

Use `make ai-documentation-read-set` to retrieve the machine-readable default
set. Reference material requires an explicit opt-in with
`INCLUDE_REFERENCE=1`; historical material under `docs/archive/` is excluded
and cannot be used as current instruction.

For the authority model and compatibility boundary, see
[Documentation Authority Boundary](../reference/documentation-authority-boundary.md).
