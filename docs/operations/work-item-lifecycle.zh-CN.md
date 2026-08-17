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

每个 Work Item 严格对应一个 Contract、一个专用 branch 和一个 PR。相互独立的 Work Item 只有在专用 branch 和 worktree、声明的 scope、evidence ownership 以及共享 serialized projection 约束彼此兼容时，才可以同时处于 active 状态。并行调度和 projection lease 协调由 Agent/Orchestrator 负责；governance gate 仍然 fail-closed。一个被 blocked 的 Work Item 不会阻塞没有依赖关系且兼容的 Work Item。在 WI 途中发现问题时，只要仍在已授权的 scope 内，就优先在当前 WI 中解决；如果需要增加 path 或权限，必须先修改当前 Contract 并重新验证。只有真正独立的变更、无法在安全的当前 scope 内解决，或用户明确要求时，才新建 Work Item。并行不会混淆 Work Item 的 identity；共享 branch-integrated projection 仍依据 closed projection inventory 串行处理。`ai-finish` 在 PR 前归档证据。只有 provider 报告已合并后，`ai-close-work-item` 才验证归档、Head SHA、同步 base、干净 worktree 和远程 branch 缺失。

## 停止条件
任何 gate 失败、Unknown 未解决、范围不一致、不兼容的 parallel boundary 或缺少人的决定，都必须停止。不要猜测 Green 就等于已关闭。远程失败后不要删除 Work Item 的 checkout。如果 candidate 缺少或重叠 closed serialized-projection inventory，必须 fail-closed 拒绝，并保持相关 Work Item 相互隔离。

## 下一步
1. 使用[决定状态](../concepts/decision-states.zh-CN.md)。
2. 阅读 [Cockpit 状态](../reference/how-to-read-cockpit-status.zh-CN.md)。
3. 失败时使用[恢复指南](recovery.zh-CN.md)。
