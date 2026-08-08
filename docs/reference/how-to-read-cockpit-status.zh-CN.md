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

## 活跃 Task Outcome

每个活跃 Status 都包含 `Task Outcome` 投影。它与 `Key Conclusion` 是独立的生命周期信号，用于确认当前 Work Item 是否已由 `ai-finish` 输出 Outcome。

两个信号有意回答不同问题，因此在 Finish 稳定证据期间颜色可以不同。`Signal Domain: governance_review` 表示 Contract/Summary 证据是否可供审查；`Signal Domain: work_item_lifecycle` 表示 Finish 是否已输出 Outcome。只能在其声明的 domain 内解读各自颜色，任何一方都不覆盖另一方。

| Presence / traffic light | 含义 | 恢复边界 |
| --- | --- | --- |
| `absent` / `yellow` | Finish 尚未持久化 Outcome；在实现或验证进行中这是正常状态。 | 继续已声明的验证或运行 `make ai-finish`；不得将 Work Item 视为可归档。 |
| `present` / `red` | 已绑定的 blocked 或 failed Outcome 记录失败 gate 和恢复条件。 | 完成所述恢复并重跑失败 gate。红色 Outcome 永不授权 archive、merge 或 release。 |
| `present` / `green` | 已为这个准确的 Work Item 生成并绑定 completed Outcome。 | 继续标准的 review 与 archive 生命周期；绿色不授权 merge 或 release。 |

该投影只从活跃 Contract、Summary 与同一 Work Item 的 Outcome JSON/Markdown 证据生成。畸形、陈旧、跨工单或与 Summary 矛盾的 Outcome 会使状态生成/检查 fail-closed；不要手工修复 `current_status.md`，也不要复制其他 Work Item 的 Outcome。
如果先前已有绿色投影、但后续 Finish gate 变为阻塞，Finish 会在返回前从 blocked Outcome 重新生成 Status。若该刷新无法通过校验，系统会移除陈旧的生成状态，而不会保留错误的绿灯；请读取任务绑定的 blocked Outcome 并修复所报告的 gate。

## Recommendation 的含义

| Recommendation | 含义 |
| --- | --- |
| `ready_for_review` | 工作和证据齐备，可以集中审查正确性。 |
| `ready_with_risks` | 可以审查，但必须确认记录的残余风险。 |
| `needs_investigation` | 状态不完整或有歧义，需要人工调查。 |
| `blocked` | 存在硬阻塞，解决前停止审查。 |

## 生成文件边界

`current_status.md` 是生成文件，不要手工编辑。所有结论必须回溯到 Contract、Summary、验证、场景覆盖和审查证据；Status 本身不证明生产能力、外部平台身份、日语能力或发布完成。
