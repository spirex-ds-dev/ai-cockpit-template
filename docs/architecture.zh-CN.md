---
author: Ray
title: "架构"
description: "说明 AI Cockpit 如何把意图转化为有边界的证据和人的决定。"
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, architecture, evidence-flow, boundaries]
---

# 架构

## Purpose

本页回答：**人的意图如何成为可复核的仓库决定？**

## Audience

适合想了解项目地图和责任边界，而不是目录列表的采用者、维护者和评审者。

## Outcome

你将理解主要流程、证据由谁负责，以及为什么有些控制仍在 AI Cockpit 之外。

## Scenario

有人要求 Agent“整理文档”。编辑前，请求会变成带范围和验收条件的 Contract。Agent 只修改该边界内的内容；检查产生证据；Summary 压缩结果；人决定下一步是否安全。

## Explanation

```text
Intent → Contract → Implementation → Verification → Summary → Cockpit → Human Decision
```

1. **Intent：**说明 Work Item 为什么存在、哪些约束重要。
2. **Contract：**在编辑前声明范围、排除项、验收条件、证据来源和必需检查。
3. **Implementation：**只修改声明的仓库表面。
4. **Verification：**运行注册的检查并记录结果。
5. **Summary：**保存变更文件、证据、风险和限制。
6. **Cockpit：**把 Repository Truth 压缩为 Human Decision State。
7. **Human Decision：**选择继续、调查、批准、阻止或恢复。

Intent、Contract、验证记录、Summary、Status 和 Archive 属于本仓库的 Native Governance Evidence。测试、覆盖率、SBOM、漏洞扫描、provenance、签名和 provider 证明属于 Delegated Domain Evidence，由专业工具或外部系统产生。AI Cockpit 可以绑定和治理这些证据，但不能仅靠重复描述让证据变成真实。

因此架构明确分为两侧：

```text
Repository Governance Layer | 外部 runtime、身份、sandbox、provider 和企业控制
```

左侧使仓库变更可评审；右侧仍由采用者、provider、审计方或其他领域系统负责。

## Action or decision（下一步行动与决定）

用这条流程判断新事实应该放在哪里。请求、范围、验证和人的决定放在受治理 Work Item 中；领域专属证明放在能够产生它的工具中；两者相互链接，但不重复所有权。

## Stop conditions

变更效果没有边界、证据所有者不清楚，或试图用本地记录证明外部控制时，停止推进。缺失的连接意味着需要调查，而不是可以猜测。

## Next steps

1. [能力与边界](capabilities.zh-CN.md) — 哪些声明属于本地、哪些责任属于外部。
2. [Human-Agent Trust Layer](trust-layer.zh-CN.md) — 证据、fail-closed 控制和恢复。
3. [安装](getting-started/installation.zh-CN.md) — 理解边界后的采用路径。

## Technical depth

规范边界包括 Work Item Contract、Scope/Backtrack/Coverage/Review Guards、Verification Registry、AI Change Summary、Cockpit Status 和 Archive Manifest。它们支持人的决定，但不提供通用语义风险检测、身份认证、运行时隔离、不可变审计或企业合规。
