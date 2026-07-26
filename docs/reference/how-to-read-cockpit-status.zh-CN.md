---
author: Ray
title: "阅读 Cockpit Status"
description: 读取生成的 current_status.md，并将状态连接到人工审查决定。
keywords:
  - ai-cockpit
  - cockpit-status
  - reviewer-guide
---

# 阅读 Cockpit Status

这是给审查者、维护者和批准者的快速阅读指南。开始实现前，必须先查看最新的 Preflight Review；Cockpit Status 不能替代实现前暂停。

## 阅读顺序

1. 活跃 Work Item 中的 `Preflight Review`
2. `Key Conclusion`（Color、Conclusion、Evidence Basis、Next Action）
3. `Recommendation`
4. `Decision Drivers`
5. `Governance Signals`
6. `Evidence`
7. 如果存在，查看 `Scenario Coverage`

## Key Conclusion 与颜色语义

`Key Conclusion` 从 canonical recommendation 确定性派生。颜色是审查语义，不是分数、置信度、质量评级，也不是 Agent 的自我表扬：

| 颜色 | 含义 | 下一步 |
| --- | --- | --- |
| `Green` | 证据足以进入人工审查。 | 阅读证据，由人决定是否 commit 或 merge。 |
| `Yellow` | 只有理解已记录的残余风险后才能继续审查。 | 决定前阅读 Residual Risk 和 Decision Drivers。 |
| `Red` | 证据不完整/有歧义，或存在硬阻塞。 | 调查或停止，直到阻塞被解决。 |

`Evidence Basis` 指向由 Contract、Summary 和验证证据派生的显示区块；它不是第二个事实源。`Next Action` 只是流程提示，不会授权 merge、release 或外部操作。

## Recommendation 的含义

| Recommendation | 含义 |
| --- | --- |
| `ready_for_review` | 工作和证据齐备，可以集中审查正确性。 |
| `ready_with_risks` | 可以审查，但必须确认记录的残余风险。 |
| `needs_investigation` | 状态不完整或有歧义，需要人工调查。 |
| `blocked` | 存在硬阻塞，解决前停止审查。 |

## 生成文件边界

`current_status.md` 是生成文件，不要手工编辑。所有结论必须回溯到 Contract、Summary、验证、场景覆盖和审查证据；Status 本身不证明生产能力、外部平台身份、日语能力或发布完成。
