---
author: Ray
title: "Implementation Knowledge"
description: "以自然语言为入口，查询经过验证、来源于归档的 Work Item 实现知识。"
audience:
  - adopter
  - reviewer
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - implementation_knowledge_query
  - implementation_knowledge_projection
keywords:
  - ai-cockpit
  - implementation-knowledge
  - evidence-bound
  - work-item
---

# Implementation Knowledge

## 这项能力帮助你做什么

当你想从以前已经治理过的变更中学习时使用 Knowledge。例如：“哪个已经验证过的
Work Item 处理了订单服务，它留下了哪些文件和证据？”结果来自对经过验证的实现记录
进行确定性查询，而不是 Agent 凭记忆给出的听起来很自信的答案。

## 使用前要准备什么

Knowledge 记录来源于已经完成的 Work Item 证据。Contract、Summary、仓库证据和最终
Outcome 仍然是权威来源。如果 Work Item 尚未得到可用 Outcome，或记录缺失、过期，就不
一定有可验证结果。

## 先用自然语言提出请求

你可以对 Agent 说：

> “请找出和 orders 有关、影响 OrderService、状态为 verified 的 Work Item，并告诉我
> Work Item ID、状态、证据路径以及下一步该检查什么。”

Agent 可以把请求转成精确过滤条件。AI Cockpit 不会假装查询引擎理解任意自然语言含义：
底层接口是结构化、只读并且按条件取交集的。自然语言句子是 HCI 入口，精确过滤器和返回
记录才是证据边界。

## 系统会做什么

1. 识别请求中实际说出的主题、组件、日期、commit、Work Item 或状态过滤条件。
2. 读取经过验证的索引和匹配的 Knowledge 记录。
3. 根据来源路径和冻结的 SHA-256 摘要检查每条记录。
4. 按稳定的 Work Item ID 和 knowledge path 顺序返回结果。
5. 你在复用设计前检查记录中的证据和限制。

过滤条件使用 **AND** 语义。支持 Work Item ID、topic、component、merged commit、精确
日期、包含起止日期范围，以及 Knowledge state（`verified`、`partial`、`unknown`、
`superseded`）。

## 使用事例：得到可检查的结果

请求：

> “请显示 2026 年 1 月的订单服务变更，并且只要 verified 的。”

预期结果：

```text
Query: topic=orders, component=OrderService, date-from=2026-01-01,
       date-to=2026-01-31, status=verified
Matches: 1
Next: 打开返回的 knowledgePath 和 evidenceRefs，再把设计用于新的 Work Item。
```

如果结果为空，表示没有记录同时满足所有过滤条件，不表示仓库从未处理过这个主题。你可以
有意识地放宽一个精确条件，或请人指定其他证据来源。

如果记录过期、格式错误、互相冲突或 supersession 关系无效，验证会 fail closed，或让记录
保持可见的 partial/unknown。不要静默选择“看起来最新”的文件。

## Knowledge 不会做什么

它不是：

- 语义、向量、模糊或 RAG 搜索；
- 相关性评分、推荐引擎或设计权威；
- 可以推翻 Contract、Summary、Outcome 或来源证据的第二事实源；
- 写入器：查询不会修改记录、索引、报告或 Work Item；
- 保证归档实现一定适合新的仓库。

只有当 Contract、Summary 或 Outcome 明确提供日期时才可按日期查询。系统不会从文件时间
戳或 commit 历史猜日期。Supersession 只采用明确关系，不从相似度推断。历史记录可以保持
`partial`。

## 高级入口

完成来源 Summary 和 Outcome 后生成或重建记录：

```sh
make ai-generate-knowledge \
  TASK=<work-item-id> \
  CONTRACT=.ai/work-items/active/<work-item-id>.contract.json \
  SUMMARY=.ai/work-items/active/<work-item-id>.summary.json \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

验证记录和索引：

```sh
make ai-check-knowledge-index
make check-ai-knowledge
```

使用精确过滤查询：

```sh
make ai-knowledge-query TOPIC=orders COMPONENT=OrderService STATUS=verified
make ai-knowledge-query DATE_FROM=2026-01-01 DATE_TO=2026-01-31
```

JSON 结果包含规范化查询、匹配数、稳定的 `results` 和兼容别名 `matches`。每条结果提供
`workItemId`、`knowledgePath`、`state`、`latestKnownRecord`、`supersessionStatus` 和完整记录。

## 停止条件和相关入口

证据缺失、过期、矛盾或超出记录声明来源时停止。不要凭记忆填补缺口，应请求新的、有证据
边界的 Work Item。

- [Task Outcome Report](../features/task-outcome-report.zh-CN.md)
- [Human Benefit Report](../features/human-benefit-report.zh-CN.md)
- [能力一览与边界](../capabilities.zh-CN.md)
- [Work Item 生命周期](../operations/work-item-lifecycle.zh-CN.md)
