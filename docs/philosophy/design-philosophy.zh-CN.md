---
author: Ray
title: "设计思想"
description: "塑造 AI Cockpit 的原则：不为流程而增加流程。"
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, design-philosophy, evidence, calibrated-trust]
---

# 设计思想

## Purpose

本页回答：**当 Agent 和人共同操作一个仓库时，应该用什么原则设计治理控制？**

## Audience

适合判断某个流程、检查或文档是否属于 AI Cockpit 的人。

## Outcome

你将理解为什么项目重视校准后的人机信任、证据优先于自我声明、与风险相称的控制强度，以及人的责任。

## Scenario

团队因为“更安全”而想增加一张审批表。设计思想会先问：它解决哪种协作失败？会产生什么证据？是否只是增加没人能维护的仪式？

## Explanation

### 发现，而不是发明

每个组件都必须回应真实的协作需要。不要因为更大的清单看起来更完整就增加流程；要把控制追溯到它处理的风险和证据。

### 遵循 North Star

North Star 是 **Calibrated Human-Agent Trust（校准后的人机信任）**。当证据支持依赖时，人可以依赖 Agent；当证据缺失、过期、矛盾或不足时，人可以调查、介入或停止。

### 先收敛，再创造

架构师不是先强行规定方案，而是去除不必要的复杂性，直到核心结构清晰。价值决定方向；约束、证据和实践揭示最小可行结构。

### 尊重不同责任

人负责意图、授权、价值判断和最终责任。Agent 擅长执行、分析、一致性检查和整理证据。AI Cockpit 支持协作，但不替代人的判断。

### 证据优先于自我声明

Agent 的说明可以帮助理解变更，但不是独立 proof。测试、差异、批准、签名和外部证明，只有由负责的工具或 provider 产生时才是证据。

```text
价值 → 原则 → 有边界的机制 → 证据 → 人的决定
```

## Action or decision

如果控制能让已知风险及其证据更容易评审，就保留它。如果需要运行时隔离、身份、provider 政策或领域专属证明，应交给负责的专业工具。

## Stop conditions

控制没有明确风险、证据产生路径，或声明超过证据支持范围时，停止推进。不能用流程语言掩盖不确定性来制造信任。

## Next steps

1. [架构](../architecture.zh-CN.md) — 这些原则产生的结构。
2. [能力与边界](../capabilities.zh-CN.md) — 仍由外部负责的内容。
3. [Human-Agent Trust Layer](../trust-layer.zh-CN.md) — 完整的证据边界。

## Technical depth

North Star/Mission 是 Calibrated Human-Agent Trust；认识论原则是 Evidence over Self-Declaration；机制是 Evidence Governance；产品边界是 Repository Governance Layer；实现由 Intent、Contract、Verification、Summary、Status 和 Archive 组成。
