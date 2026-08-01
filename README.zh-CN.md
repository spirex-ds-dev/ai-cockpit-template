---
author: Ray
title: "AI Cockpit"
description: 面向校准后人机信任的证据型仓库治理层。
audience:
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
---

# AI Cockpit

[English](README.md) | [日本語](README.ja.md)

<!-- readme-section: identity -->
## 它是什么

AI Cockpit 是用于 AI 辅助软件开发的 **Repository Governance Layer**。它把
仓库证据转化为人可以复核的、有边界的治理决策。

扩展说明见 [Human-Agent Trust Layer](docs/trust-layer.zh-CN.md)。

<!-- readme-section: problem -->
## 它解决什么问题

Agent 可能超出范围、削弱测试、跳过验证，或让评审者得不到证据。AI Cockpit
明确记录预期变更、实际差异、必需检查、Unknown 与人的决定。

<!-- readme-section: how-it-works -->
## 如何工作

```text
Evidence → Governance Decision → Human Control
```

每项变更使用一个 Contract、一个分支、一个 Summary/Outcome、一个 PR，以及
经过验证的关闭流程。Agent 的文字说明本身不是证据。

<!-- readme-section: decision-states -->
## 三色决策状态

- **Green：**必需证据支持有边界的下一步。
- **Yellow：**调查缺失、过期、矛盾或带风险的证据。
- **Red：**停止；必需控制失败或缺少权限。

参见 [Decision States](docs/concepts/decision-states.md)。

<!-- readme-section: quick-start -->
## 30 秒开始

用 coding agent 打开目标 Git 项目，然后按照
[30 秒开始](docs/getting-started/30-second-start.zh-CN.md) 操作。流程先只读，解析
固定发布版本，展示写入计划，并在安装步骤前请求确认。完整路径见
[安装](docs/getting-started/installation.zh-CN.md)。

<!-- readme-section: boundary -->
## 产品边界

AI Cockpit 不是 Agent Runtime、Workflow Engine、Security Sandbox、通用 Prompt
Injection 检测器、身份提供方、合规认证或人工评审替代品。外部身份、分支保护、
生产隔离和发布证明仍属于外部证据。

当前能力声明受 [Capability Truth Matrix](docs/reference/capability-truth-matrix.md)
约束。

<!-- readme-section: documentation -->
## 文档入口

- 开始：[安装](docs/getting-started/installation.zh-CN.md)、[First Calibration](docs/getting-started/first-calibration.md)、[First Work Item](docs/getting-started/first-work-item.md)
- 概念：[Trust Layer](docs/concepts/trust-layer.md)、[Evidence Governance](docs/concepts/evidence-governance.md)、[Decision States](docs/concepts/decision-states.md)
- 运维：[Quality Gates](docs/operations/quality-gates.zh-CN.md)、[Work Item Lifecycle](docs/operations/work-item-lifecycle.md)、[Recovery](docs/operations/recovery.md)
- 安全：[Threat Model](docs/security/threat-model.md)、[Injection Boundary](docs/security/injection-boundary.md)、[Supply Chain](docs/security/supply-chain.md)
- 参考：[Schemas](docs/reference/schemas.md)、[Commands](docs/reference/commands.md)、[Documentation Architecture](docs/reference/documentation-architecture.md)
- 历史：[Plans](docs/archive/plans/README.md)、[Reviews](docs/archive/reviews/README.md)、[Designs](docs/archive/historical-designs/README.md)
