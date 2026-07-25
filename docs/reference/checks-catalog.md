---
author: Ray
title: "Checks Catalog"
description: "Repository quality and governance checks with explicit evidence boundaries."
keywords:
  - ai-cockpit
  - checks
  - governance
  - verification
---

# Checks Catalog

The quality architecture check is one local governance check among the full
Work Item gates. It verifies repository-observable safety patterns and makes
test-layer applicability explicit.

| Command | Purpose | Boundary |
| --- | --- | --- |
| `make check-quality-architecture` | Generate and validate the local quality/test-layer report | Does not verify external controls |
| `make project-format-check` | Ruff formatting and whitespace | Source formatting only |
| `make project-lint` | Ruff, mypy, Bandit, complexity, supply-chain, compile checks | Local static and repository checks |
| `make project-test` | Full pytest, coverage, installer and CI release evidence | Repository test evidence |

All checks remain subject to the Work Item Contract, Summary, required
scenario evidence, human decisions, and PR review. Green local checks do not
mean production readiness, compliance, or release authorization.
