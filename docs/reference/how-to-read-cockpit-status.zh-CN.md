---
title: "如何阅读 Cockpit 状态"
description: "把生成的 status 转换为人的决定。"
author: Ray
audience:
  - adopter
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# 如何阅读 Cockpit 状态

## 目的
把生成的 status 转换为可理解、有边界的决定。

## 读者
Work Item 的所有评审者，包括非技术批准人。

## 结果
你能在不猜测的情况下阅读结论、证据、风险和下一步。

## 场景
在 preflight、verification、finish 或 gate 失败后阅读当前 status。

## 决定
按 `Key Conclusion`、`Recommendation`、`Decision Drivers`、`Evidence`、`Scenario Coverage` 顺序阅读。颜色不是分数。

| 颜色 | 人的决定 | 安全的下一步 |
| --- | --- | --- |
| Green | 证据足以评审；决定是否继续。 | 阅读证据；不要把它当作 merge 或 release 授权。 |
| Yellow | 剩余风险或证据不完整，需要有意识的决定。 | 阅读风险和原因，调查或记录决定。 |
| Red | 存在硬 blocker 或歧义，必须停止。 | 停止并遵循明确的恢复条件。 |
| Unknown | 信号不足以可靠解释。 | 请求澄清或缺失证据。 |

## 停止条件
如果 status 过期、损坏、属于其他任务或缺少证据，不要手工编辑，也不要猜测或推测。status 是 Contract、Summary 和检查的投影。

## 下一步
1. 使用[决定状态](../concepts/decision-states.zh-CN.md)。
2. 查看 [Work Item 生命周期](../operations/work-item-lifecycle.zh-CN.md)。
3. 停止时使用[恢复指南](../operations/recovery.zh-CN.md)。
