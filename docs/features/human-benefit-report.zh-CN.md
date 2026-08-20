---
author: Ray
title: Human Benefit Report
description: 从证据中简洁说明一个受治理任务的价值、剩余风险和下一项人的决定。
audience:
  - adopter
  - reviewer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - human_benefit_report
  - implementation_approach_report
---

# Human Benefit Report

## 这项能力帮助你做什么

当你需要给人一个简短但可靠的答案时使用它：**完成了什么、发现了什么问题、解决了
什么、还剩什么风险、下一步应该做什么？** 它是经过验证的 Task Outcome 的人类可读投影。

## 用自然语言提出请求

你可以说：

> “请给出这个 Work Item 的人类交接摘要，包括已完成内容、阻塞问题、有证据的已解决问题、
> 剩余风险、Unknown、人类决定和下一安全动作。”

Agent 可以展示已持久化的 `humanHandoff`，但不能把没有证据的收益改写成事实。

## 结果长什么样

默认顺序按人的决定组织：

```text
Task Result
Status: Success / Partial / Blocked / Failed

What was completed
Problems found
Stops triggered
Problems resolved
Risks avoided
Remaining risks
Unknowns
Human decisions
Verification
Impact
Next action
```

其中的问题、风险、警告和强制停止数量是证据记录数量，不是生产力、时间、金额、安全性
或信任分数。

## 使用事例

如果 Work Item 补上了缺失的文档链接，交接摘要可以写成：

```text
完成：补上了缺失的能力一览链接。
已解决问题：文档入口现在能够到达能力一览。
证据：Contract、变更文件和通过的文档链接检查。
剩余风险：Hosted provider 评审尚未确认。
下一步：先评审 PR，等待 provider 结果后再合并。
```

证据缺失时，必须写成“已报告”或“inference”，或者保持 Yellow/Red。摘要简短不等于
可以跳过评审。

## 报告缺失或过期时

先停止并验证 Task Outcome。报告缺失、格式错误、过期、属于其他任务或与归档 Outcome
不一致时均不可使用。应修复来源记录并重新生成投影，不要手工编辑投影来制造完成感。

## 高级入口和生命周期

`humanHandoff` 从 `.ai/work-items/active/<task>.outcome.json` 派生。`ai-finish` 把 Review
Report 写入 `.ai/cockpit/task_report.json` 和 `.ai/cockpit/task_report.md`。provider 确认
合并后，`ai-close-work-item` 会在清理分支前把 Final Report 写在 Closure Receipt 旁边。

```sh
make generate-human-benefit-report \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
make check-human-benefit-report \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

Review Report 不能证明 PR 创建、Hosted CI、合并、清理、人已阅读或 provider 身份。Final
Report 只能重复 closure adapter 已验证的事实。两者都不能证明平台隔离、企业合规或生产安全。

参见[Task Outcome Report](task-outcome-report.zh-CN.md)、[决定状态](../concepts/decision-states.zh-CN.md)
和[Work Item 生命周期](../operations/work-item-lifecycle.zh-CN.md)。
