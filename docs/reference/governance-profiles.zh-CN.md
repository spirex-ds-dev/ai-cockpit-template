---
author: Ray
title: "治理配置级别"
description: 面向 AI Cockpit 工单的 Light、Standard、Strict 与 release 操作升级的风险质量路由。
audience:
  - adopter
  - maintainer
status: current
authority: translation
canonical: docs/reference/governance-profiles.md
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - risk_based_quality_routing
keywords:
  - ai-cockpit
  - governance-profile
  - quality-routing
---
# 治理配置级别

AI Cockpit 根据仓库证据选择足够且最小的质量图。级别顺序为
`light < standard < strict`；混合变更采用最高级别，未知或空路径证据至少采用 Standard。Release 是操作类别，不是第四个治理档位。

## 级别

| 级别 | 典型变更 | 调度目标 |
| --- | --- | --- |
| Light | 文档、注释、不可执行示例、纯格式变更 | `quality-fast` |
| Standard | 普通源码、测试、缺陷修复、小型重构 | `quality-standard` |
| Strict | 治理、CI、安装器、安全、依赖、破坏性/公共 API、迁移、校准、证据 Schema | `quality-full` |

Standard 复用现有 Fast、项目测试、引用影响和完整测试削弱检查；Strict 复用现有 Full 图。
若 Strict 工单的操作、资源或能力声明涉及 Release，额外运行 `quality-release` 的
release-preflight 和分发验证。`make quality` 继续作为 Full 的兼容别名，`make ai-cockpit-quality`
是按证据路由的工单入口。

## 会话归属

每个公开质量级别和直接 `project-test` 都会在 coverage 或报告写入者运行前取得一个非阻塞、
工作树本地的内核锁。同一工作树的第二次调用会立即失败关闭，不写入质量证据，并输出
`Retry: make quality`。锁会在 owner 退出时由操作系统释放，因此不得删除锁文件。不同工作树
使用不同锁路径，可以并行运行。

## Contract 证据

Contract 的 `governanceProfile` 记录 `selected`、`source`、`reasons` 和 `override`。
路由器读取 `.ai/quality/governance-routing.yaml`，合并 Contract base 之后的已提交、已暂存、
未暂存和未跟踪路径，并向 `target/quality/governance-profile.json` 写入自动/最终级别、理由、
所需分组、调度目标和 override 处置。生成的当前状态、工单 Start Receipt 与当前 Outcome 仍保留在证据中，
但不会单独抬升级别；只有这类证据的差分采用 Standard。无效 Git base、路径穿越或损坏策略均失败关闭。

在首个 Work Item 建立前，已安装的采用方没有 Contract base。仅在这个边界下，路由器以 `HEAD`
为基线，同时继续纳入已暂存、未暂存和未跟踪的安装器变更。显式 `--base` 或 active Contract 的
`baseCommit` 始终优先；无效的显式 base 仍然失败关闭。

```sh
make ai-cockpit-quality CONTRACT=.ai/work-items/active/<task>.contract.json
make ai-cockpit-quality GOVERNANCE_PROFILE=strict
```

显式级别只能升级，不能降低自动结果。降级必须在 Contract 中记录 `human_override`，包括批准证据、
理由、已知风险、未运行检查，以及到期时间或当前工单的精确范围。过期、不完整或错配证据会被拒绝，
并恢复自动级别；不能形成永久或静默例外。

## 边界

Receipt 是仓库证据，不是授权令牌。系统不认证批准者身份、不修改 Hosted 分支保护、不声称路径能
证明语义风险，也不以本地或缓存结果替代发布证据。采用方可通过 `AI_COCKPIT_STRICT_CHECK` 配置项目特有
Strict 检查；工单生命周期 Gate 仍由 `ai-finish` 独立执行。未配置发布检查时，Release 目标失败关闭。
