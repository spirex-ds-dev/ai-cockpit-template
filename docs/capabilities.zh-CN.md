---
author: Ray
title: "能力一览与边界"
description: "以可快速浏览的能力索引连接自然语言用户指南，并明确每项能力的责任边界。"
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
  - adopter_capability_manifest
  - adopter_work_item_status_interface
  - adopter_governance_cost_metrics
  - adopter_performance_diagnosis
  - human_benefit_report
  - implementation_approach_report
  - implementation_knowledge_query
  - implementation_knowledge_projection
  - work_item_intelligence_interface
keywords: [ai-cockpit, capabilities, boundaries, evidence]
---

# 能力一览与边界

本页是能力一览。先浏览能力目标、状态和责任边界，再点击“详细说明”。详细页面
会给出实际使用路径、自然语言事例、停止条件和高级命令。

## Purpose

本页回答 AI Cockpit 能帮助人理解什么、每项能力在哪里停止，以及下一步应该打开哪一页。

## Audience

适合 adopter、评审者和维护者在进入详细使用路径前快速浏览能力地图。

## Outcome

读完后，你应该能够按目标选择能力，阅读它的状态和责任边界，并知道何时必须交给人或外部系统。

## Scenario

你知道想得到什么结果——例如了解以前的实现、同时处理独立 Work Item，或从停止中恢复——但不知道应该打开哪一页或使用哪个命令。先从能力索引开始，再点击一个“详细说明”链接。

AI Cockpit 的产品边界是 **Repository Governance Layer（仓库治理层）**：它把仓库证据转化为有边界的 Work Item 决定。它不是 Agent Runtime、Workflow Engine、Security Sandbox、身份提供方，也不是人工评审的替代品。

## Explanation

下表的状态使用 adopter capability manifest 的词汇。它只说明声明的能力表面，
不构成普遍的安全、生产就绪或 provider 保证。[Capability Truth Matrix（能力事实矩阵）](reference/capability-truth-matrix.md)
提供逐行证据和限制。

| 能力/用户目标 | Manifest 状态 | 能帮你做什么 | 边界或责任方 | 详细说明 |
| --- | --- | --- | --- | --- |
| 能力清单 | `implemented` | 查看哪些面向 adopter 的能力已被统一声明和检查。 | 模板和 installer 声明能力表面；adopter 仍需提供自己的安装证据。 | [高级能力事实参考](reference/capability-truth-matrix.md) |
| Work Item Status Interface | `adopter_installed` | 阅读证据派生的 Work Item 状态和索引。 | 它只发布本地投影，不执行、调度或重试任务。 | [Status Interface](reference/work-item-status-interface.md) |
| 治理成本指标 | `adopter_installed` | 了解一个 Work Item 的治理成本提示。 | 它只报告本地可观测证据，不是生产力、时间、金额或信任分数。 | [高级指标参考](reference/governance-cost-metrics.md) |
| 性能诊断 | `adopter_installed` | 查看有证据支持的耗时和可能瓶颈。 | 它只诊断已有的计时证据，不承诺优化或更快运行。 | [高级诊断参考](reference/performance-diagnosis.md) |
| Task Outcome 与 Human Benefit Report | `adopter_installed` | 了解发生了什么、解决了什么、剩下什么以及下一安全动作。 | Outcome 由证据派生；Human Benefit Report 是投影，不是第二个事实源。 | [Outcome 与报告](features/task-outcome-report.zh-CN.md) |
| Implementation Knowledge 查询 | `adopter_installed` | 按精确的主题、组件、日期、commit 或状态筛选历史 Work Item。 | 查询只读、确定性、来源于归档；不是语义搜索或 RAG。 | [Knowledge 使用指南](reference/implementation-knowledge.zh-CN.md) |
| Implementation Knowledge 投影 | `adopter_installed` | 从完成的证据派生并维护经过验证的实现记录和索引。 | 正常流程通过依赖映射只刷新受影响的记录；映射缺失或不可信时会明确全量重建/重新验证或 fail closed，历史越大时这类恢复可能成本更高。 | [Knowledge 使用指南](reference/implementation-knowledge.zh-CN.md) |
| Work Item 问题解决边界 | `adopter_installed` | 判断发现的问题是否应留在当前 Work Item。 | Contract、权限和 base 仍覆盖时在当前任务内修复；否则建立独立 Work Item。 | [生命周期与恢复](operations/work-item-lifecycle.zh-CN.md) |
| 模板 Capability Truth 材料 | `template_only` | 阅读模板使用的证据模型和能力声明限制。 | 模板材料本身不证明 adopter 已安装、已校准或拥有外部保证。 | [Capability Truth Matrix](reference/capability-truth-matrix.md) |
| Implementation Approach 报告 | `adopter_installed` | 阅读有证据边界的实现方式说明。 | 它由 Summary、Outcome 和 Human Benefit Report 承载，不是 Agent 自述。 | [Outcome 与报告](features/task-outcome-report.zh-CN.md) |

## Action or decision

| 如果你想…… | 从这里开始 |
| --- | --- |
| 理解结果并决定下一步 | [Outcome、Summary 与 Human Benefit Report](features/task-outcome-report.zh-CN.md) |
| 查找以前验证过的实现 | [Implementation Knowledge](reference/implementation-knowledge.zh-CN.md) |
| 同时处理相互独立的 Work Item | [Work Item 并行处理](features/work-item-parallelism.zh-CN.md) |
| 查看状态、从停止中恢复或关闭 Work Item | [Work Item 生命周期](operations/work-item-lifecycle.zh-CN.md) |
| 安装或更新已有安装 | [升级](upgrade.zh-CN.md) |

## 如何使用这个索引

先说目标，不要先背命令。例如：“我想确认以前的 Work Item 是否真的解决了订单服务
的问题。”然后点击对应的详细说明，先读停止条件，再在需要可重复本地检查时使用高级命令。

自然语言请求是一种人和 Agent 的交互方式。Agent 可以把它转换成受 Contract 约束的命令；
AI Cockpit 仍然会检查声明的范围和仓库证据。一句话不会授予权限、扩大范围、调度其他
Work Item 或制造外部证明。

## Stop conditions

出现以下情况时，暂停采用、合并或继续决定：

- 当前状态或证据缺失、过期、矛盾，或超出声明范围；
- 把 `planned` 或 `template_only` 材料说成当前 adopter 保证；
- 把外部责任说成本地证明；
- 需要 AI Cockpit 不负责的 scheduler、retry controller、身份提供方、Security
  Sandbox 或 release 声明才能成立。

## Next steps

1. [Outcome 与报告](features/task-outcome-report.zh-CN.md) — 理解结果和下一安全动作。
2. [Implementation Knowledge](reference/implementation-knowledge.zh-CN.md) — 查找有证据边界的历史实现。
3. [Work Item 并行处理](features/work-item-parallelism.zh-CN.md) — 安全处理相互独立的 Work Item。
4. [Work Item 生命周期](operations/work-item-lifecycle.zh-CN.md) — 恢复、评审并关闭 Work Item。

## Technical depth

英文、中文和日文的能力一览保持相同的行、状态、边界和详细链接。部分技术参考仍只有
英文；它们会明确标为高级 fallback，不会被默认为已翻译的普通用户指南。

需要了解证据契约时，阅读[Capability Truth Matrix](reference/capability-truth-matrix.md)；
需要了解实施过程时，阅读[Work Item 生命周期](operations/work-item-lifecycle.zh-CN.md)。
