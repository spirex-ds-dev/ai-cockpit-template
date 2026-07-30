---
author: Ray
title: "Japanese Assessment Depth Corrective Implementation Plan"
description: TDD and lifecycle plan for replacing the shallow Japanese report with a comprehensive release gate.
---

# Japanese Assessment Depth Corrective Implementation Plan
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Objective

Make the mandatory Japanese assessment comprehensive, reproducible, and
release-blocking without combining the resulting capability fixes into this
Work Item.

## Instruction → plan → implementation → acceptance

| Instruction | Plan | Implementation evidence | Acceptance evidence |
| --- | --- | --- | --- |
| Japanese capability is mandatory before release. | Add the assessment as a release-preflight prerequisite. | `Makefile`; `scripts/ai_japanese_capability.py` | `tests/test_makefile.py`; direct blocking gate execution |
| Evaluate Japanese comprehensively, not by English inference. | Add a versioned independent corpus and domain matrix. | `tests/fixtures/japanese-capability-corpus.json`; assessor | `tests/test_japanese_capability.py` |
| Every issue must be corrected. | Emit stable finding IDs and named next Work Items for every blocker. | JSON/Markdown reports; comprehensive plan | report finding assertions and traceability gate |
| Do not lose STOP/risk/next action/human question. | Require structured output/lifecycle parity evidence. | assessor cases | positive and missing-evidence regressions |
| Prevent stale evidence. | Derive Markdown from JSON and compare both to current source. | assessor `--write`/`--check` | stale JSON and Markdown tests |
| Complete every Work Item lifecycle. | Archive, one PR, Hosted CI, merge, closure, branch cleanup. | Contract/Summary/Manifest | `ai-finish`, aggregate PR, Hosted checks, `ai-close-work-item` |

## Tasks

1. Write red tests for the expanded schema, corpus, blockers, deterministic
   digests, stale report rejection, and release-preflight prerequisite.
2. Add the independent corpus and implement deterministic domain evaluators.
3. Generate authoritative JSON and derived Markdown from current repository
   evidence.
4. Register stable finding IDs and the ordered corrective queue in the
   comprehensive plan and bidirectional traceability.
5. Verify focused tests, report check, expected release blocking, docs
   metadata, fast quality, and full `ai-finish`.
6. Complete commit, aggregate PR, push, Hosted CI, merge,
   `make ai-close-work-item`, branch cleanup, and synchronized main.
7. Start the first finding corrective; do not enter WI-17 until all findings
   are corrected and a fresh assessment has zero in-scope blockers.
