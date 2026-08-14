---
author: Ray
title: "为什么需要 AI Cockpit"
description: "说明 AI Cockpit 解决的问题，以及人需要做出的决定。"
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, purpose, north-star, human-agent-trust]
---

# 为什么需要 AI Cockpit

## Purpose

本页回答一个问题：**在 AI Agent 修改仓库之前，为什么要使用 AI Cockpit？**

## Audience

适合判断项目是否适合团队的人，也适合向非技术人员解释项目的人。

## Outcome

读完后，你应该能说明项目解决的问题、North Star，以及 AI Cockpit 负责什么、仍由人或外部工具负责什么。

## Scenario

Agent 提议修改一份文档。说明听起来合理，但没有说清可修改哪些文件、需要哪些测试，也没有人能判断这个分支是否安全合并。AI Cockpit 会在修改悄悄变成团队责任之前，把这些问题显式化。

## Explanation

AI 辅助开发很快，但速度可能掩盖不确定性。Agent 可能误解请求、扩大范围、跳过检查，或者在没有评审证据的情况下给出自信的解释。

AI Cockpit 是 **Repository Governance Layer（仓库治理层）**。它把人的请求转化为有边界的 Work Item，把预期范围连接到可复核证据；当证据缺失、过期、矛盾或存在风险时，把控制权交还给人。

它的 North Star 是 **Calibrated Human-Agent Trust（校准后的人机信任）**。这不是尽可能信任 Agent，而是在证据支持时依赖 Agent，在证据不足时让调查、介入或停止变得清晰。

它采用 **Evidence Governance（证据治理）**。项目治理证据，但不替代产生测试、覆盖率、SBOM、漏洞扫描、provenance、签名或 provider 证明的工具。

```text
人的意图 → 有边界的 Contract → 变更 → 证据 → 人的决定
```

## Action or decision

当变更需要清晰范围、可复现检查和负责人的决定时，使用 AI Cockpit。如果需求是 Agent Runtime、Workflow Engine、Security Sandbox、身份提供方或企业合规系统，应选择负责该能力的独立工具。

## Stop conditions

不要把 Agent 的文字、看起来绿色的状态或仅仅存在的文件当作 proof。请求、范围、权限、证据或外部控制不清楚时，应停止并调查。

## Next steps

1. [设计思想](philosophy/design-philosophy.zh-CN.md) — 让控制强度与证据风险相称的原则。
2. [架构](architecture.zh-CN.md) — 意图如何成为可复核证据。
3. [能力与边界](capabilities.zh-CN.md) — 仓库能够、不能够声明什么。

## Technical depth

治理路径是 `Intent → Contract → Implementation → Verification → Summary → Cockpit → Human Decision`。Native Governance Evidence 由本仓库产生，Delegated Domain Evidence 由独立工具或 provider 产生。完整边界见 [Human-Agent Trust Layer](trust-layer.zh-CN.md)。
