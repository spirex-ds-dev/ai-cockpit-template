---
author: Ray
title: "质量门禁运行说明"
description: AI Cockpit 质量门禁、证据和工单追踪运行说明。
keywords:
  - ai-cockpit
  - quality-gates
  - ci
  - evidence
---

# 质量门禁运行说明

AI Cockpit 保持 `make quality` 向后兼容：它等价于 `make quality-full`。
本地快速反馈使用 `make quality-fast`，发布准备使用 `make quality-release`。

## 责任归属

- `quality-fast` 负责格式、Lint、差分、Schema、文档元数据、项目配置和状态策略检查。
- `quality-full` 另外负责完整测试、证据、供应链和项目一致性分组。专门 Trust 测试仍可作为独立调试目标运行，但不会在完整 pytest 后重复运行。
- `quality-release` 追加安装和发布证据检查。快速结果或缓存结果不能替代发布证据。
- 兼容性任务只验证解释器/平台矩阵，不运行完整质量图。
- Hosted smoke 明确拆为 `template-smoke`（唯一完整质量门所有者）、`installation-smoke` 和 `release-evidence` 三个 Job；后两个依赖质量所有者，不能再次调用完整质量图。

## 证据与失败行为

`scripts/run_quality_gate.py` 为每个门禁记录一份 JSON 计时证据和一份日志，包括命令、提交、耗时、退出码、超时、缓存状态、输出 digest 和失败尾部。`scripts/summarize_quality_gates.py` 输出包含总墙钟时间、门禁总耗时、并行效率、最慢门禁、失败尾部、跳过和最终决策的 JSON 与 Markdown 汇总。缺失计时证据即失败关闭；缓存命中不是最终证据。

Hosted 前后计时是证据声明，不是推断。如果无法取得 WI-20 基线或 hosted run，必须记录结构化 `not-run` 原因、run ID 和限制，不能报告性能改善。

`scripts/determine_quality_scope.py` 根据变更路径选择 Fast、Full 或 Release。未知或混合范围默认 Full。只有 `.ai/quality/gates.yaml` 声明输出不冲突时才允许并行。

## 追踪要求

每个工单在 PR、合并、归档和分支清理前，都必须双向检查“指示 → 计划 → 实现 → 验收”链路。没有实现证据的验收项，或没有计划验收项的实现指示，都是遗漏，必须记录并修正后才能继续。

完整流程仍为：Contract、实现、验证与 Summary、PR、合并、`make ai-close-work-item`，最后清理本地和远程分支。本文件描述执行证据，不声称 AI Cockpit 是安全沙箱或可独立保证企业合规。
