---
author: Ray
title: AI Cockpit Governance Hardening Implementation Plan
description: Execution plan for serial lifecycle, budget, Contract readiness, and release evidence gates.
---

# AI Cockpit Governance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将串行 Work Item 顺序、预算影响、Contract 前置和发布证据分层固化为 Skill 指引与仓库硬门禁。

**Architecture:** Skill 描述执行顺序和停止条件；Python guards 读取本地 Contract、Archive、Git 和复杂度报告，输出结构化 fail-closed 错误；Makefile 将 guards 接入 Preflight/finish/质量入口。历史归档继续只读兼容。

**Tech Stack:** Python、pytest、Make、JSON/YAML、Markdown、Git metadata。

## Global Constraints

- 一个 Work Item 对应一个专用分支和一个 PR。
- Contract 未通过 Preflight 时不得修改实现、测试、文档或治理配置。
- 前置 Work Item 未完成 PR 合并、ai-close、分支清理和 main 同步时不得启动后继 Work Item。
- 超出复杂度预算必须有明确 repayment record，或拆分为独立预算修复 Work Item。
- 历史、候选、已发布 Release 证据不得互相冒充；所有发布声明必须绑定 source SHA 和实际证据。

### Task 1: Contract semantic readiness gate

**Files:** `scripts/ai_check_work_item.py`, `scripts/ai_preflight_review.py`, `tests/test_ai_check_work_item.py`

- [ ] Add failing tests for code-mode placeholder intent, acceptance, sources, scenario coverage, and verification.
- [ ] Run the focused tests and confirm they fail for the placeholder fixture.
- [ ] Implement one shared semantic-placeholder validator used by Contract check and Preflight.
- [ ] Run the focused tests and confirm they pass.

### Task 2: Serial lifecycle and budget gates

**Files:** `scripts/ai_check_serial_order.py`, `scripts/ai_check_budget_impact.py`, `Makefile`, `templates/make/Makefile.ai`, tests

- [ ] Add failing tests for an incomplete predecessor and an unrecorded budget overrun.
- [ ] Implement deterministic local checks with actionable evidence paths.
- [ ] Wire both checks into `ai-preflight`, `ai-finish`, and the template Makefile.
- [ ] Run focused and integration checks.

### Task 3: Release evidence and documentation

**Files:** `docs/reference/ai-cockpit-work-item-lifecycle.md`, `docs/superpowers/plans/2026-07-22-ai-cockpit-governance-hardening.md`, `.ai/guards/governance_complexity_policy.yaml`

- [ ] Document historical/candidate/published evidence boundaries and the exact lifecycle gate order.
- [ ] Record the budget gate configuration and repayment semantics without changing current limits.
- [ ] Run documentation, governance, and release consistency checks.

### Task 4: Skill solidification and full verification

**Files:** local AI Cockpit Skill guidance and repository verification records

- [ ] Update the AI Cockpit Skill with the four hardening rules and required gate commands.
- [ ] Run all declared AI checks, project quality, and regression tests.
- [ ] Finish, archive, push, review, merge, close, and synchronize the Work Item.

## Completion Definition

The Work Item is complete only after the Contract/Summary are archived, its PR is merged, `make ai-close-work-item` succeeds, both branches are deleted, main equals origin/main, and the Skill/guard behavior is covered by passing regression tests.
