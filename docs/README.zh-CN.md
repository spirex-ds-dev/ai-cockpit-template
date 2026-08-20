---
author: Ray
title: "AI Cockpit 文档"
description: "用于理解、采用和运行 AI Cockpit 的读者优先中文入口。"
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - documentation_architecture
---

# AI Cockpit 文档

[English](README.md) | [日本語](README.ja.md)

这是理解 AI Cockpit 的五分钟入口。无需先读实现细节；先回答四个问题：项目是什么、
为什么存在、它控制什么，以及哪些事情必须由人决定。

## 理解项目

按项目 North Star 的顺序阅读：

1. **North Star / 身份** — AI Cockpit 是仓库治理层（Repository Governance Layer）：它把仓库证据转化为有边界的决定，帮助人和 Agent 在证据基础上调整信任。参见[Human-Agent Trust Layer](trust-layer.zh-CN.md)。
2. **目的** — 它让变更意图、范围、证据、不确定项（Unknown）和人的决定可见，避免 Agent 默默改写变更目标。参见[为什么需要 AI Cockpit](purpose.zh-CN.md)。
3. **设计思想** — 证据优先于自我声明；控制强度与风险相称；证据不足时按安全规则停止（fail closed）。参见[设计思想](philosophy/design-philosophy.zh-CN.md)。
4. **架构** — 变更从意图开始，依次经过 Contract（作业契约）、实现、验证、Summary（结果摘要）、Cockpit，最后由人决定。参见[架构](architecture.zh-CN.md)。
5. **能力与边界** — Cockpit 管理的是仓库变更证据，不是 Agent Runtime、Workflow Engine、Security Sandbox、身份提供方或人工评审本身的替代品。参见[能力与边界](capabilities.zh-CN.md)。
6. **人的决定** — 先读[决定状态](concepts/decision-states.zh-CN.md)，再读[Cockpit 状态](reference/how-to-read-cockpit-status.zh-CN.md)和[Work Item 生命周期](operations/work-item-lifecycle.zh-CN.md)，确认何时继续、调查或停止。

## 按读者目标选择

| 目标 | 从这里开始 | 读完后应该能够 |
| --- | --- | --- |
| 判断是否采用 | [安装](getting-started/installation.zh-CN.md) | 理解前置条件、确认点和会产生的证据。 |
| 开始使用 | [首次校准](getting-started/first-calibration.zh-CN.md) → [首个 Work Item](getting-started/first-work-item.zh-CN.md) | 从可信 base 创建第一个有边界的任务。 |
| 查看安全边界 | [注入边界](security/injection-boundary.zh-CN.md) | 区分 AI Cockpit 的责任和外部安全控制的责任。 |
| 评审结果 | [质量门](operations/quality-gates.zh-CN.md) → [Cockpit 状态](reference/how-to-read-cockpit-status.zh-CN.md) | 不把 Agent 的说明当作 proof，正确阅读检查与证据。 |
| 从停止中恢复 | [恢复](operations/recovery.zh-CN.md) | 保留 Work Item，修复缺失证据后再重试。 |
| 维护或审计 | [文档架构（英文参考）](reference/documentation-architecture.md) | 找到 canonical owner、语言政策和参考资料深度。 |

## 先看能力一览

如果你还不知道应该打开哪一页，请先看[能力与边界](capabilities.zh-CN.md)。
它是能力索引：每项能力只用一句话说明用途、当前状态、责任边界，并提供“详细说明”
链接。点击进入详细页面后，再查看前置条件、自然语言请求、使用事例、预期结果、
停止/恢复方式以及可选的高级命令。

| 你想做什么 | 从能力一览进入 |
| --- | --- |
| 了解一个已完成、有警告或被阻止的结果 | [Outcome、Summary 和 Human Benefit Report](features/task-outcome-report.zh-CN.md) |
| 查找以前已经验证过的实现 | [Implementation Knowledge](reference/implementation-knowledge.zh-CN.md) |
| 同时推进多个相互独立的 Work Item | [Work Item 并行处理](features/work-item-parallelism.zh-CN.md) |
| 理解状态、恢复和关闭 | [Work Item 生命周期](operations/work-item-lifecycle.zh-CN.md) |
| 安装、校准或更新已有安装 | [升级](upgrade.zh-CN.md) |

自然语言事例描述的是人可以让自己的 Agent 执行的目标。AI Cockpit 仍然只是有边界的
仓库治理层；它不会把一句话变成无限制的工作流、调度器或外部证明。

这个入口先帮助你理解项目，再引导到安装、使用和技术参考。重要主题会优先提供中文、
日文和英文入口；尚未完成翻译或仍在迁移的页面会明确标注，不能据此认为全部文档已经
完成多语言覆盖。当前边界是：P1 的 commands 和 schemas 技术参考目前只有英文
canonical 路径，P2 的文档权威边界参考默认不要求翻译。这些是明确的语言覆盖政策，
不能据此宣称全部文档已经完成多语言覆盖。具体的 P0/P1/P2 规则见[文档架构（英文参考）](reference/documentation-architecture.md)。

### 技术参考

以下是为维护者和贡献者准备、并明确标注语言状态的技术入口：

- [Commands — 英文技术参考（P1）](reference/commands.md)
- [Schemas — 英文技术参考（P1）](reference/schemas.md)
- [文档权威边界 — 英文参考（P2，默认不要求翻译）](reference/documentation-authority-boundary.md)
