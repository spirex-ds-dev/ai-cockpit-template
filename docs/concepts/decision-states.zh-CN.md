---
title: "决定状态"
description: "从证据走向人的决定的易读指南。"
author: Ray
audience:
  - adopter
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# 决定状态

## 目的
帮助非技术读者决定应评审、调查还是停止。

## 读者
采用者、贡献者、维护者和评审者。

## 结果
你能说清状态含义、人的决定和安全的下一步。

## 场景
在 check、preflight 或 finish 后打开 `.ai/cockpit/current_status.md`。

## 决定

| 状态 | 含义 | 人的决定 | 安全的下一步 |
| --- | --- | --- | --- |
| Green | 必需证据是最新的，且支持有边界的行动。 | 阅读证据，决定是否继续。 | 按声明的下一步执行；Green 本身不授权 merge 或 release。 |
| Yellow | 证据缺失、过期、矛盾或存在剩余风险。 | 决定调查、记录风险或停止。 | 阅读列出的原因，修复或记录缺口。 |
| Red | 必需控制失败、超出范围或缺少授权。 | 停止，只决定如何满足恢复条件。 | 保留 Work Item，解决明确的 blocker。 |
| Unknown | 无法可靠解释证据。 | 不作继续决定。 | 请求缺失来源或人工澄清。 |

## 停止条件
不要从颜色推测，不要复制其他任务的 status，也不要把 Agent 说明当 proof。停止必须写明缺失证据和恢复条件。

## 下一步
1. 阅读[Cockpit 状态怎么读](../reference/how-to-read-cockpit-status.zh-CN.md)。
2. 查看 [Work Item 生命周期](../operations/work-item-lifecycle.zh-CN.md)。
3. 已停止时使用[恢复指南](../operations/recovery.zh-CN.md)。
