---
author: Ray
title: "Architecture"
description: AI Cockpit repository layout and component architecture.
keywords:
  - ai-cockpit
  - architecture
  - repository-layout
  - work-item-contract
---

# Architecture

```text
.ai/
  cockpit/
    README.md
    checks.yaml
    current_status.md
  guards/
    agent_risk_policy.yaml
    ai_review_policy.yaml
    backtrack_policy.yaml
    cockpit_status_policy.yaml
    coverage_policy.yaml
    file_boundary.yaml
    file_ownership.yaml
    scope_policy.yaml
    summary_policy.yaml
  work-items/
    _templates/
      work_item_contract.example.json
      work_item_summary.example.json
    active/
    archive/
.cursor/
  rules/
    ai-cockpit.mdc
examples/
  csharp/
  flutter/
  go/
  java/
  kotlin/
  php/
  python/
  ruby/
  rust/
  swift/
  typescript/
docs/
  assets/
    ai-cockpit-demo.gif
scripts/
  ai_archive_work_item.py
  ai_check_agent_risk.py
  ai_check_backtrack.py
  ai_check_coverage_guard.py
  ai_check_guards.py
  ai_check_review_policy.py
  ai_check_scope.py
  ai_check_status.py
  ai_check_status_consistency.py
  ai_check_summary.py
  ai_check_work_item.py
  ai_checkpoint.py
  ai_common.py
  ai_finish.py
  ai_generate_status.py
  ai_observability.py
  ai_start.py
  install_ai_cockpit.py
target/
  ai_observability.jsonl
  ai_*.json
templates/
  make/
    Makefile.ai
  stacks/
    *.mk
install.sh
Makefile
AGENTS.md
CLAUDE.md
GEMINI.md
```

## Core Components

| Component | Purpose |
| --- | --- |
| Work Item Contract | Declares task scope, sources, acceptance, verification, and rollback note. |
| Scope Guard | Checks actual git diff against `scope` and `outOfScope`. |
| Backtrack Guard | Blocks protected test, snapshot, or Work Item evidence deletion by default. |
| Coverage Guard | Blocks configured production changes without matching test changes by default. |
| Agent Risk Guard | Hard gate against prompt-is-advice, mid-task drift, and unknown-overclaim risks. |
| AI Review Policy | Report-only check that flags governance and CI changes needing explicit review focus. |
| Checkpoint | Mid-task integrity snapshot that compares scope, acceptance, and verification state. |
| Status Consistency Guard | Verifies `current_status.md` matches the set of active Work Items. |
| Change Summary | Records changed files, checks, risk, generated files, and destructive changes. |
| Cockpit Status | Generates the one-screen status view for the active AI task. |
| Observability | Appends structured JSONL events to `target/ai_observability.jsonl` for every check. |
| Finish Flow | Runs checks and archives the Work Item when ready. |

## Diff and Evidence Semantics

The Work Item baseline is a Git commit captured at start. The effective change set is the union of `baseCommit...HEAD`, staged/unstaged changes against `HEAD`, and untracked files. A path that was dirty at start is excluded only while its content fingerprint remains unchanged. `AI_BASE_COMMIT` overrides the local baseline in CI so pull requests can use their merge-base.

Verification is registry-controlled execution, not a Summary-supplied command. A version 2 Contract names check IDs from `.ai/cockpit/checks.yaml`; each registered entry must resolve to an explicit Make target. The finish runner stores structured execution metadata bound to the check ID, execution commit, Contract hash, and normalized command hash. This record improves validation and traceability but is not a cryptographic attestation.

PR validation discovers every archived Contract, Summary, or review record changed in the complete name-status diff. New evidence must add its Contract and Summary together. Existing archive evidence is immutable: modification, deletion, and rename are rejected instead of allowing a later Work Item to claim an older record. Each non-exempt path must then have at least one paired owner: the path is in that Contract's scope, outside its outOfScope, and present in that Contract's paired Summary `changedFiles`. Dirty-baseline exclusions are intentionally disabled for this aggregate check.

PR archive evidence must use Contract version 2. Version 1 remains readable for local historical inspection but is rejected when newly added or modified in a PR, preventing downgrade around the check registry and execution-record requirements.

Repository approval fields record process intent; they do not establish human identity. AI Cockpit is a change-control workflow rather than a hostile-code sandbox. Trusted approval and independent project-test execution belong in the hosting platform's protected review and CI controls.
