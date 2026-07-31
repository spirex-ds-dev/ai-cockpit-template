---
author: Ray
title: "Execution Plan Index"
description: "Index and retention policy for auditable execution plans."
keywords:
  - execution-plan
  - audit
  - work-item
---
# Execution Plan Index

本目录保存当前执行计划和历史关闭索引。不可变 Work Item archive 是完成事实的权威来源。

## 保留规则

| 分类 | 处理方式 |
| --- | --- |
| 当前执行 | 保留原文，标注执行中并链接 Work Item。 |
| 已完成/需审计 | 引用扫描后可压缩为关闭索引；必须保留 archive evidence 路径和 Git 恢复方式。 |
| 已替代/错误计划 | 新 Work Item 完成引用扫描并记录替代证据后删除；不得删除 Contract、Summary 或 manifest。 |

## 当前计划

当前没有执行中的跨周期整改计划。新的工作必须以新的 Work Item Contract 和当时的用户指示为准，不能把历史计划当作继续执行授权。

## 本周期关闭索引

[2026-07-25 AI Cockpit 全面整改执行计划](2026-07-25-ai-cockpit-comprehensive-remediation.md) 已在 v0.5.47 发布、发布后采用审计 corrective PR #539 合并并关闭后完成。本计划保留为历史关闭索引：

- 公开发布：[v0.5.47](https://github.com/spirex-ds-dev/ai-cockpit-template/releases/tag/v0.5.47)，tag target `3b383c8bf2b0b13264edbfaa4a40449d1ac48911`；
- 最终 corrective：[PR #539](https://github.com/spirex-ds-dev/ai-cockpit-template/pull/539)，合并提交 `e14e567cf3073272727392c99084216e00733bfc`；
- 权威完成事实：[Work Item archive index](../../../.ai/work-items/archive/index.json)；
- 本轮最终 closure receipt：`target/task-closure-receipts/post-publish-adoption-pr-audit-corrective-20260731.closure.md`。

原计划正文和所有历史计划仍保留；Git 历史可恢复任何本次索引化修改。

## 历史保留计划

下列计划已完成或属于专项历史记录，保留原文和关联证据：

- [2026-07-14 评审整改循环](2026-07-14-review-remediation-loop.md)
- [2026-07-14 SBOM 与 Trust](2026-07-14-supply-chain-sbom-trust.md)
- [2026-07-15 治理整改](2026-07-15-governance-remediation.md)
- [2026-07-15 Supply Chain Evidence](2026-07-15-supply-chain-evidence.md)
- [2026-07-16 Archive History Threshold](2026-07-16-decouple-archive-history-threshold.md)
- [2026-07-20 全面评审整改（修订版）](2026-07-20-comprehensive-review-remediation.md) — 已被 2026-07-21 计划替代，保留审计历史。
- [2026-07-21 最新评审整改](2026-07-21-review-remediation.md) — 工单 1–17 已完成，PR #168 合并，上一版已发布，最后工单已关闭。
- [2026-07-21 Bootstrap Adoption 评审整改](2026-07-21-bootstrap-adoption-review-remediation.md) — WI01–WI15 已完成，PR #172–#186 合并，上一版已发布，保留完整审计证据。
- [2026-07-22 Conditional GO 全面评审整改](2026-07-22-conditional-go-review-remediation.md) — 已完成；保留其串行 Work Item 生命周期的审计历史。
- [2026-07-22 Project Calibration and Update Recalibration](2026-07-22-project-calibration-recalibration.md) — 已完成并压缩为 archive-backed closure index。
- [2026-07-22 Installed Lifecycle Management 评审整改](2026-07-22-installed-lifecycle-review-remediation.md) — 工单 1–16 已完成并压缩为 archive-backed closure index。
- [2026-07-22 AI Cockpit Governance Hardening](2026-07-22-ai-cockpit-governance-hardening.md) — 已完成并压缩为 archive-backed closure index。
- [2026-07-24 Release Post-Merge Source Verification](2026-07-24-release-postmerge-source-verification.md) — 已完成的发布流程纠偏记录；不是当前发布指令。
- [2026-07-25 Interactive Installation and Calibration Wizard](2026-07-25-interactive-installation-calibration-wizard.md) — WI0–WI11 已完成并关闭；WI12 盘点确认无重复执行计划可删除，canonical plan 与 append-only issue log 保留，完成事实见 [archive index](../../../.ai/work-items/archive/index.json) 与 [WI11 final report](../../../.ai/work-items/archive/2026/wizard-final-verification-and-user-report.summary.json)。

## Retention decision for the Interactive Wizard plan

The read-only WI12 inventory found one canonical execution plan and one append-only issue log. No superseded duplicate execution-plan document was identified, so no plan document is removed. The canonical plan remains the implementation and audit narrative; the issue log remains the user-review entry point; Work Item Contracts, Summaries, manifests, and archive index entries are immutable evidence and are retained.

相邻的 `../specs/` 属于独立设计证据。计划压缩或删除必须由 Contract
声明 scope，先完成引用扫描，并在 Summary 记录权威 archive 与 Git 恢复路径。
