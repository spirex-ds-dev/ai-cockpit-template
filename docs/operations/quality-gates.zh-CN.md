---
author: Ray
title: "质量门禁运行说明"
description: AI Cockpit 质量门禁、证据和工单追踪运行说明。
capabilityClaims:
  - risk_based_quality_routing
keywords:
  - ai-cockpit
  - quality-gates
  - ci
  - evidence
---

# 质量门禁运行说明

AI Cockpit 保持 `make quality` 向后兼容：它等价于 `make quality-full`。
本地快速反馈使用 `make quality-fast`，发布准备使用 `make quality-release`。

## 采用方质量配置

安装后的模板始终提供 `make quality`。实际的格式化、Lint 和测试由采用方在
`Makefile.ai.stack` 中拥有的 `PROJECT_FORMAT_CHECK`、`PROJECT_LINT` 与
`PROJECT_TEST` 配置。必须为三项都配置项目命令；缺失或空值会失败关闭，并指出
需要修复的变量。

Hosted snapshot 准备使用同一个入口。质量检查失败时不会写出 receipt。请先在
`Makefile.ai.stack` 中配置缺失变量，再执行 `make quality`，随后执行
`make ai-prepare-hosted-verification-snapshot CONTRACT=<active-contract>`。

## 责任归属

- `quality-fast` 负责格式、Lint、差分、Schema、文档元数据、项目配置和状态策略检查。
- `quality-full` 另外负责完整测试、证据、供应链和项目一致性分组。专门 Trust 测试仍可作为独立调试目标运行，但不会在完整 pytest 后重复运行。
- `quality-release` 追加安装和发布证据检查。快速结果或缓存结果不能替代发布证据。
- 兼容性任务只验证解释器/平台矩阵，不运行完整质量图。
- Hosted smoke 为完整 `project-test` 集合中的每个条目分配唯一所有者：按历史时长均衡的 `project-test-core`、`project-test-governance`、`project-test-installer`、`project-test-lifecycle` 与 `project-test-release` runner。每个 runner 发布绑定源的 JUnit、coverage、timing、log 和 receipt 工件。`project-test-aggregate` 是 `always()` 的失败关闭消费者：缺失、取消、失败、过期、SHA 不匹配或不完整 shard 都会被拒绝，`template-smoke` 不能复用 aggregate receipt。本地 `make project-test` 保留为串行诊断等价入口。
- 阻断发布的全历史 secret scan 由唯一独立 owner `secret-scan` 执行，并与 project-test 图并行启动。`template-smoke` 同时等待该 source checkout scan 成功和失败关闭 aggregate receipt；这只移除可避免的尾部等待，不会移除安全验证。
- 安装给采用方的发行内容包含运行时骨架、策略和必要基线，但不包含模板维护用的 Work Item starts、decision 历史或 archive 历史。安装器在遍历前剪枝这些目录，并在单次安装中复用不可变的源文件清单。

## 证据与失败行为

每次 `make quality` 都会在 `target/quality/sessions/` 下创建全新目录，并绑定提交、Hosted run/attempt 或唯一的本地标识。`scripts/run_quality_gate.py` 实时流式输出门禁日志，同时为每个门禁记录完整日志和一份 JSON 计时证据，包括 session/run 标识、命令、提交、耗时、退出码、超时或取消状态、缓存状态、输出 digest 和有界尾部。顶层调用会在退出时重新绑定 `current-session.txt`，因此嵌套 dry-run 或测试 fixture 不能成为 Hosted 发布选择的 session。Telemetry 包装器只传递经过验证且仍打开的 Make jobserver descriptor；无效或不可用的 descriptor 不会被转发。`project-test` 还会写入 JUnit 证据，日志中包含最慢用例报告。`scripts/summarize_quality_gates.py` 输出包含总墙钟时间、门禁总耗时、并行效率、最慢门禁、失败尾部、跳过和最终决策的 JSON 与 Markdown 汇总。

Hosted CI 使用 `if: always()` 上传完整 session 目录和外层日志，因此成功、失败、取消和超时都会保留诊断证据。缺失计时或工件证据即失败关闭；缓存命中不是最终证据。

`template-smoke` 的剩余质量调用有 25 分钟执行上限。对于忽略初始信号的残留子进程，`timeout` 随后仅给予有限的 30 秒强制终止宽限。这样仍保留心跳和诊断证据，但会得到终态失败门禁，PR 不会无限停留在 in-progress。该上限不允许跳过或降级任何质量门。

手动触发 smoke 时必须声明用途。用于绑定源提交的性能测量时，执行
`gh workflow run smoke.yml --ref <measurement-branch> -f purpose=hosted_measurement`。
`release_preparation` 仍是严格默认值并执行发布状态证据检查；性能测量触发不声明发布意图。

基线与候选样本必须写入独立 receipt。每个比较至少需要五个成功、唯一 workflow run/attempt 的样本，且样本必须来自一个精确 SHA/tree 和相同 runner 类；cache hit 永远不能代替验证。

Hosted 前后计时是证据声明，不是推断。如果无法取得 WI-20 基线或 hosted run，必须记录结构化 `not-run` 原因、run ID 和限制，不能报告性能改善。

`scripts/determine_quality_scope.py` 根据变更路径选择 Fast、Full 或 Release。未知或混合范围默认 Full。只有 `.ai/quality/gates.yaml` 声明输出不冲突时才允许并行。

## 追踪要求

每个工单在 PR、合并、归档和分支清理前，都必须双向检查“指示 → 计划 → 实现 → 验收”链路。没有实现证据的验收项，或没有计划验收项的实现指示，都是遗漏，必须记录并修正后才能继续。

完整流程仍为：Contract、实现、验证与 Summary、PR、合并、`make ai-close-work-item`，最后清理本地和远程分支。本文件描述执行证据，不声称 AI Cockpit 是安全沙箱或可独立保证企业合规。
