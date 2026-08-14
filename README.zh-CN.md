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

请先打开[中文文档入口](docs/README.zh-CN.md)，按读者目标理解项目。

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

决策和恢复路径集中在[中文文档入口](docs/README.zh-CN.md)。

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

当前能力声明和责任边界见[能力与边界](docs/capabilities.zh-CN.md)。

<!-- readme-section: documentation -->
## 文档入口

从[中文文档入口](docs/README.zh-CN.md)选择目标：理解项目、判断是否采用、开始第一个
受治理任务、评审结果、从停止中恢复，或维护与审计。入口会优先使用同语言 canonical
页面；尚未翻译的 P0 会明确标为 planned，而不是静默切换语言。
