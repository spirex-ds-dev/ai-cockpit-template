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

这是理解 AI Cockpit 的五分钟入口。无需先读实现细节；先回答三个问题：项目是什么、
为什么存在、它控制什么以及哪些事情必须由人决定。

## 理解项目

按项目 North Star 的顺序阅读：

1. **North Star / 身份** — AI Cockpit 是 Repository Governance Layer，把仓库证据
   转化为有边界的决策，支持校准后的人机信任。参见[Human-Agent Trust Layer](trust-layer.zh-CN.md)。
2. **目的** — 它让 Intent、范围、证据、Unknown 和人的决定可见，避免 Agent 默默改写
   变更目标。参见[为什么需要 AI Cockpit](purpose.zh-CN.md)。
3. **设计思想** — 证据优先于自我声明，控制强度与风险相称，并在证据不足时 fail closed。
   参见[设计思想](philosophy/design-philosophy.zh-CN.md)。
4. **架构** — 通过 Intent → Contract → Implementation → Verification → Summary →
   Cockpit → Human Decision 的一条治理路径工作。参见[架构](architecture.zh-CN.md)。
5. **能力与边界** — Cockpit 治理证据，但不是 Agent Runtime、Workflow Engine、Security
   Sandbox、身份提供方，也不是人工评审的替代品。参见[能力与边界](capabilities.zh-CN.md)。
6. **人的决定** — [决定状态](concepts/decision-states.zh-CN.md)，然后阅读[Cockpit 状态](reference/how-to-read-cockpit-status.zh-CN.md)和 [Work Item 生命周期](operations/work-item-lifecycle.zh-CN.md)。
   说明何时继续、调查或停止。

## 按读者目标选择

| 目标 | 从这里开始 | 读完后应该能够 |
| --- | --- | --- |
| 判断是否采用 | [安装](getting-started/installation.zh-CN.md) | 理解前置条件、确认点和会产生的证据。 |
| 开始使用 | [首次校准](getting-started/first-calibration.zh-CN.md) → [首个 Work Item](getting-started/first-work-item.zh-CN.md) | 从可信 base 创建第一个有边界的任务。 |
| 查看安全边界 | [注入边界](security/injection-boundary.zh-CN.md) | 区分 AI Cockpit 的责任和外部安全控制的责任。 |
| 评审结果 | [质量门](operations/quality-gates.zh-CN.md) | 不把 Agent 的说明当作 proof，正确阅读检查与证据。 |
| 从停止中恢复 | [恢复](operations/recovery.zh-CN.md) | 保留 Work Item，修复缺失证据后再重试。 |
| 维护或审计 | [Documentation Architecture](reference/documentation-architecture.md) | 找到 canonical owner、语言政策和参考资料深度。 |

入口页面先解决项目理解，再引导到技术参考。P0 topic 仍为 `planned` 时，表示迁移工作尚未
完成，不能宣称完整的多语言覆盖。
