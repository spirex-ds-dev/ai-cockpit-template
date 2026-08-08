---
author: Ray
title: Human Benefit Report
description: 从证据中简洁说明单个受治理任务的价值和待决事项。
---

# Human Benefit Report

Human Benefit Report 简洁回答任务做了什么、发现多少有证据的问题、发生了哪些停止、哪些问题已解决、避免了什么风险、哪些决定来自人、还剩什么风险以及下一安全动作。

Task Outcome 是唯一机器事实源。`ai-finish` 在 `.ai/cockpit/task_report.json` 和 `.ai/cockpit/task_report.md` 生成 Review Report；`check-ai-pr` 将其与已归档 Outcome 对照，缺失、格式错误、陈旧或不一致时失败关闭。

当归档重写该 Outcome 的 active 路径时，归档事务会重新生成这对精确的 report，并在同一份归档 Summary 中记录两个路径。只有完整的当前归档事务可以拥有该 report pair；缺失、陈旧、格式错误或跨任务的 report 仍然是 unowned。

验证提供方合并事实后，`ai-close-work-item` 在删除分支前把 Final Report 写入 `target/task-closure-receipts/`。Final Report 只增加 PR URL、合并提交、已同步基础分支、清理意图和继续工作的目录，并保持同步后的 `main` 干净。

问题数是 findings、risks、warnings 和 forced stops 的证据记录数，不是唯一根因数，也不是生产力、时间、金额、安全性或信任分数。Review Report 不能证明 Hosted CI、合并、清理、人类已阅读或提供方身份；Final Report 也不能证明平台隔离、企业合规或生产安全。
