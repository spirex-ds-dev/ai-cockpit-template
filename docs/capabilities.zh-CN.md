---
author: Ray
title: "能力与边界"
description: "用通俗语言说明 AI Cockpit 能够声明什么，以及哪些责任仍在外部。"
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
keywords: [ai-cockpit, capabilities, boundaries, evidence]
---

# 能力与边界

AI Cockpit 的产品边界是 **Repository Governance Layer（仓库治理层）**。

## Purpose

本页回答：**AI Cockpit 控制什么，哪些事情仍必须由其他人、工具或 provider 控制？**

## Audience

适合在采用、安全评审或判断仓库检查能否证明更大范围属性之前阅读。

## Outcome

你将知道哪些说法有仓库证据支持，哪些属于模板或采用者责任，以及哪些明确不在项目范围内。

## Scenario

采用者看到本地质量检查通过，就问这是否证明生产隔离和 Agent 身份。不能。检查只支持有边界的仓库决定；外部声明需要负责系统提供自己的证据。

## Explanation

### AI Cockpit 可以治理

- Work Item 的范围、排除项、验收条件和证据来源。
- 注册检查、变更摘要、状态信号、人的决定和归档可追溯性。
- 对仓库本地、门禁可以确定性停止或要求调查的已知情形进行控制。

### AI Cockpit 本身不能证明

- Agent Runtime 行为、通用 Prompt Injection 防护或所有语言中的语义安全。
- Security Sandbox 隔离、身份认证、分支保护或外部不可变审计。
- 没有漏洞、企业合规、provider 发布或生产就绪。
- 仅因为模板包含相关材料，就证明采用者已经安装或校准。

当前逐行实现状态以 [Capability Truth Matrix](reference/capability-truth-matrix.md) 为准。它区分 `implemented`、`template_only`、`adopter_installed` 和 `planned`；正文不能扩大这些状态的含义。

```text
本地治理证据 → 有边界的仓库决定
外部/领域证据 → 外部责任与声明
```

## Action or decision

对每个重要声明，询问：谁产生证据、覆盖什么范围、证据缺失时安全的下一步是什么？本仓库能验证的声明保留在本地；不能验证的声明链接到外部责任方。

## Stop conditions

声明没有当前证据、把 `planned` 或 `template_only` 描述成 implemented，或把外部责任说成本地保证时，停止合并或采用决定。

## Next steps

1. [架构](architecture.zh-CN.md) — 证据如何流动、由谁负责。
2. [Decision States（英文 fallback）](concepts/decision-states.md) — 如何处理 green、yellow、red。
3. [Capability Truth Matrix（英文 fallback）](reference/capability-truth-matrix.md) — 逐行证据与限制。

## Technical depth

能力声明绑定精确的 matrix ID 和重新生成的证据。检查通过只证明声明范围内的证据，不构成普遍的安全或合规声明。Native 与 Delegated Domain Evidence 分开保存，以便重建来源和责任。
