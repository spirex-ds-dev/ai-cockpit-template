---
author: Ray
title: "Work Item 并行处理"
description: "在保持范围、证据和共享投影安全的前提下，同时处理相互独立的 Work Item。"
audience:
  - adopter
  - contributor
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
  - work_item_intelligence_interface
keywords: [ai-cockpit, work-item, parallelism, concurrency, evidence]
---

# Work Item 并行处理

## 这项能力帮助你做什么

当你希望多个相互独立的 Work Item 同时推进时，使用本指南。这是 **Work Item 的并行
处理能力**，不是宣称评估或每条验证命令都可以并行运行。

目标很简单：独立工作可以同时进行；只要共享文件、生成投影、证据或串行生命周期决定，
就必须等待并按顺序处理。

## 使用前要准备什么

派发第二个 Work Item 前确认：

- 两个目标确实独立；
- 每个 Work Item 都有自己的 Contract、分支、工作树和明确范围；
- 两个任务不会修改同一文件或生成投影；
- 不会读取另一个任务仍在生成的可变证据；
- 两个任务都有可信且明确的 base，可以独立验证；
- 人或外部 Agent/Orchestrator 有权协调它们。

## 用自然语言提出请求

你可以对 Agent 说：

> “请同时推进文档索引任务和独立的校准参考任务。为每个任务创建独立 Work Item、分支、
> 工作树、范围、证据和最终评审。如果它们共享文件或生成投影，就把共享部分串行处理，
> 不要合并两个任务的身份。”

Agent/Orchestrator 负责派发、并发、重试和 provider 协调。AI Cockpit 负责每个 Work Item
自己的 Contract、范围、证据、验证、Summary、Outcome 和关闭；它不是 scheduler 或 retry
controller。

## 系统会做什么

1. 协调者比较两个 Contract 以及路径/证据所有权。
2. 兼容的 Work Item 使用不同的分支和工作树。
3. 每个 Agent 只在自己的范围内工作，并记录自己的证据。
4. 共享路径、共享生成输出或共享串行投影一次只处理一个。
5. 每个 Work Item 独立验证，并产生自己的 Summary 和 Outcome。
6. 协调者聚合结果，但不合并 Work Item 身份。
7. 每个 Work Item 仍按正常 PR 和 `ai-close-work-item` 生命周期合并与关闭。

## 安全事例

```text
Work Item A：更新 docs/getting-started/ 下的 onboarding 文档。
Work Item B：评审 docs/security/ 下的另一个参考页面。

两个任务使用不同分支、工作树、范围、证据和 PR：
可以同时推进，最后分别评审。
```

如果配置的检查图允许，并且检查不会写入或读取同一份可变证据，有限的验证也可以并行。
这只是验证优化，不是合并 Work Item 身份。

## 不安全事例

```text
Work Item A：重新生成 docs/reference/capability-truth-matrix.json。
Work Item B：修改证据绑定到该矩阵的能力声明。

共享的是证据投影。应串行处理，或者修订所有权，让一个 Work Item 拥有完整的 source-bound 变更。
```

不要因为目标看起来相关就把两个任务放进一个分支、工作树或 Contract。也不要让协调者把同一
路径分配给两个 Work Item 来掩盖冲突。

## WIII 能做什么，不能做什么

Work Item Intelligence Interface（WIII）是当前工作树内只读的机器可读投影，帮助 Agent
查看本地 Work Item intelligence。它不是 scheduler、DAG engine、retry controller、agent
manager、分布式锁服务或跨工作树协调服务。

外部 Agent 或 Orchestrator 负责派发和并发。WIII 视图不能证明另一个工作树干净、provider
已经合并 PR 或人已经批准下一步。

## 并行处理停止时怎么办

出现以下情况时，停止并保持 Work Item 分离：

- 路径或生成投影重叠；
- base 不兼容或过期；
- 证据所有权不明确；
- 必需检查会写共享状态，但没有安全边界；
- 某个 Work Item 需要 Contract 未声明的权限或范围；
- 协调者无法证明哪个 Work Item 拥有变更路径。

恢复方式是把冲突部分串行化，在修改范围前修订并重新验证 Contract，或创建真正独立的
后继 Work Item。不要盲目重试，也不要在远程失败后删除工作树。

## 高级入口

精确的所有权和有限并行验证规则见：

- [Agent 并行 Work Item](../reference/agent-parallel-work-items.md)
- [安全的并行验证](../reference/safe-parallel-verification.md)
- [Work Item Intelligence Interface](../reference/work-item-intelligence-interface.md)
- [Work Item 生命周期](../operations/work-item-lifecycle.zh-CN.md)

当前工作树的 WIII 投影应通过仓库配置的 status/intelligence 入口读取，不能替代 Contract、
验证、PR 或关闭命令。

## 相关入口

- [能力一览与边界](../capabilities.zh-CN.md)
- [Task Outcome Report](task-outcome-report.zh-CN.md)
- [恢复](../operations/recovery.zh-CN.md)
