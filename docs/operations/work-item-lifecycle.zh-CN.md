---
title: "Work Item 生命周期"
description: "一次受治理变更的安全顺序。"
author: Ray
audience:
  - contributor
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Work Item 生命周期

## 目的
让人和 Agent 的工作顺序可见，避免跳过控制点。

## 读者
贡献者、维护者和评审者。

## 结果
你知道何时继续、何时暂停，以及何时 Work Item 才真正关闭。

## 场景
从可信 base 开始，直到合并后的清理，都使用这条路线。

## 决定
顺序是 `latest remote base → Contract → preflight → implementation → verification → Summary/Outcome → archive → commit/push → PR → merge → closure → cleanup`。

每个 Work Item 只有一个专用 branch 和一个 PR。`ai-finish` 在 PR 前归档证据。只有 provider 报告已合并后，`ai-close-work-item` 才验证归档、Head SHA、同步 base、干净 worktree 和远程 branch 缺失。

## 停止条件
任何 gate 失败、Unknown 未解决、范围不一致或缺少人的决定，都必须停止。不要猜测 Green 就等于已关闭。当前 Work Item 未关闭前不要开始下一个；远程失败后不要删除 checkout。

## 下一步
1. 使用[决定状态](../concepts/decision-states.zh-CN.md)。
2. 阅读 [Cockpit 状态](../reference/how-to-read-cockpit-status.zh-CN.md)。
3. 失败时使用[恢复指南](recovery.zh-CN.md)。
