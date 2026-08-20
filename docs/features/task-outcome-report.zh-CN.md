---
author: Ray
title: Task Outcome Report
description: 以证据说明一个受治理 Work Item 改变了什么、发现了什么、避免了什么，以及还需要人决定什么。
audience:
  - adopter
  - reviewer
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - human_benefit_report
  - implementation_approach_report
---

# Task Outcome Report

## 这项能力帮助你做什么

Work Item 结束时，你应该能够回答：**发生了什么、修复了什么、还剩什么、下一步
最安全的决定是什么？** Task Outcome 提供有证据支持的答案。它不同于回答“能否继续
执行”的 Cockpit Status，也不同于可选的、面向 PR 评审的展示摘要。

## 使用前要准备什么

Work Item 应该有 Contract、Summary、验证证据和明确的当前状态。如果任务曾经停止或
包含 Unknown，先读清这些事实，再决定是否完成。报告不能补造缺失的证据。

## 用自然语言提出请求

你可以对 Agent 说：

> “请说明这个 Work Item 交付了什么、解决了哪个问题、什么证据证明结果、还剩什么
> 风险，以及我下一步需要决定什么。”

Agent 可以用仓库中有边界的报告命令来回答。这句话只是人和 Agent 的交互方式，不会
自动产生事实源、授予权限或证明人已经作出决定。

## 四种视图，一条证据链

| 视图 | 回答什么 | 不是什么 |
| --- | --- | --- |
| Contract | 这个 Work Item 被允许并要求做什么？ | 任务已经成功的证明。 |
| Summary | Agent 在修改和验证过程中记录了什么？ | 原始检查或人的决定的替代品。 |
| Task Outcome | 这个任务的价值、发现、停止、解决、剩余风险和证据是什么？ | PR 已合并或 provider 已批准的证明。 |
| Human Benefit Report | 给人看的简洁结果和下一安全动作是什么？ | 第二个事件日志或自由发挥的成功声明。 |

Task Outcome 是报告投影使用的机器事实源。Human Benefit Report 从经过验证的 Outcome
派生，每个事实声明都绑定 `evidenceRefs`。

## 使用事例：从问题到有证据的解决

假设 Work Item 允许修复订单服务的文档。你问：

> “订单服务的文档问题解决了吗？现在可以合并吗？”

有用的报告应该显示这样的链条：

```text
问题：文档入口没有进入已经验证过的能力页面。
动作：在 Contract 范围内补上缺失入口。
验证：文档元数据和内部链接检查通过。
结果：有证据的问题已解决；是否评审和合并仍要由人根据 PR/provider 证据决定。
```

每一行都应指向 Contract、变更文件、检查回执和 Summary 字段。只有“看起来已经修好”
而没有这些引用，仍然只是 inference，不是 verified resolution。

## 使用事例：警告或停止

如果本地检查通过但 Hosted CI 尚未运行，结果必须明确写出缺失的 provider 证据。Yellow
Outcome 可以告诉你等待或补充该证据。Red Outcome 必须写出失败门禁、原因、位置、证据
和恢复动作。不能因此声称已合并、已发布、安全或生产就绪。

## 报告包含什么

完整报告可以包含 Outcome Summary、Task Overview、Delivered Changes、Findings、Risks、
Warnings、Interventions、Forced Stops、Resolutions、Recurrence Prevention、Avoided Impact、
Residual Risks、Human Decisions 和 Evidence。没有内容的部分也要明确写为 `None`。

归档前会直接交付 conversational `humanHandoff`，其中包括完成情况、通过的检查、保留
事项、风险、Red 原因、人类问题和下一动作。没有证据引用的声明会标成 inference，不能
通过 Markdown 渲染变成事实。

## 报告不完整时怎么办

报告缺失、过期、格式错误、属于其他任务或存在矛盾时，停止并修复来源证据。如果修复
需要超出 Contract 的新路径、权限或行为，应先修订并重新验证 Contract，或建立真正独立
的 Work Item。不要直接编辑报告来掩盖问题。

## 高级入口

机器源是 `.ai/work-items/active/<task>.outcome.json`，派生的 Markdown 是
`.ai/work-items/active/<task>.outcome.md`。Review Report 是
`.ai/cockpit/task_report.json` 和 `.ai/cockpit/task_report.md`。

```sh
make ai-finish TASK=<work-item-id> REPORT_LANGUAGE=zh-CN
make check-ai-task-outcome OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
make check-human-benefit-report OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

`ai-finish` 只有在明确请求 archive 且已经直接交付人类报告时才归档。provider 报告 PR
已合并后，再用 `make ai-close-work-item TASK=<work-item-id>` 验证关闭事实，之后才能清理分支。

## 边界和相关入口

报告不证明平台隔离、企业合规、provider 身份、人已阅读、生产就绪或普遍安全性；也不
替代 Cockpit Status 或产生它的原始证据。

- [Human Benefit Report](human-benefit-report.zh-CN.md)
- [Work Item 生命周期](../operations/work-item-lifecycle.zh-CN.md)
- [决定状态](../concepts/decision-states.zh-CN.md)
- [能力一览与边界](../capabilities.zh-CN.md)
