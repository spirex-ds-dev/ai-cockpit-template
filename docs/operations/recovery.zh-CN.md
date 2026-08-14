---
title: "恢复"
description: "让停止或失败的 Work Item 以 fail-closed 方式重试。"
author: Ray
audience:
  - contributor
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# 恢复

## 目的
把停止变成有边界的重试，而不是临时绕过。

## 读者
负责停止 Work Item 的贡献者和维护者。

## 结果
你能保留证据、修复明确缺口，并只重试受影响的阶段。

## 场景
在 preflight、verification、hosted verification 或 closure 停止后使用。

## 决定
1. 阅读停止原因和恢复条件。
2. 保留 Contract、Summary、branch、checkout 和失败输出。
3. 只做范围内修复并更新证据。
4. 重跑失败 gate，再运行声明的 aggregate checks。
5. 状态改变时再次请求人工评审。

## 停止条件
不要绕过 gate、根据其他 Work Item 的 status 猜测、用本地证据替代 hosted 证据，或在远程失败后删除 checkout。不清楚时停止并请求澄清。

## 下一步
1. 重读[决定状态](../concepts/decision-states.zh-CN.md)。
2. 遵循 [Work Item 生命周期](work-item-lifecycle.zh-CN.md)。
3. 安装问题见[故障排查](../troubleshooting/installation.zh-CN.md)。
