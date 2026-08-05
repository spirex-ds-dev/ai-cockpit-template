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
| `make project-format-check` | Locked Ruff formatting and whitespace | Stops before Ruff unless the selected interpreter matches the direct `ruff` pin |
| `make project-lint` | Locked Ruff, mypy, Bandit, complexity, supply-chain, compile checks | Stops before Ruff unless the selected interpreter matches the direct `ruff` pin |
| `make project-test` | Full pytest, coverage, installer and CI release evidence | Repository test evidence |

All checks remain subject to the Work Item Contract, Summary, required
scenario evidence, human decisions, and PR review. Green local checks do not
mean production readiness, compliance, or release authorization.

## Locked quality-toolchain recovery

The repository validates Ruff through the same `PYTHON` interpreter that will
run format or lint. A mismatch is a red quality result; do not substitute a
global Ruff executable or bypass the failed gate. From the repository root,
recreate the local hash-locked environment and rerun the named failed command:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
make project-format-check
```

Use `make project-lint` as the final line when lint was the failed entrypoint.
These commands provide repository-local development recovery only; they do not
install, select, or manage an adopter project's toolchain.
