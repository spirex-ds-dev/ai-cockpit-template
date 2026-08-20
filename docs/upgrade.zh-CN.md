---
author: Ray
title: "升级"
description: "面向普通用户的已有 AI Cockpit 安全更新入口。"
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
keywords: [ai-cockpit, upgrade, compatibility, migration]
---

# 升级

## 这项能力帮助你做什么

当项目已经有 AI Cockpit、你希望更新受管理文件时，使用本入口。升级是 adopter 项目的
独立 Work Item，不只是执行一条命令，也不等于校准或激活已经完成。

## 用自然语言提出请求

你可以对 Agent 说：

> “请为已有的 AI Cockpit 安排升级。先告诉我当前版本和目标版本、base 分支、受管理文件
> 变化、冲突、回滚证据，以及每一个需要我决定的地方。”

写入前先阅读生成的 Contract、Impact Assessment、目标 release source 和升级差异。只有
Candidate 成功激活后，才可以移除对现有 Active Configuration 的保护。

## 安全步骤

1. 从 adopter 仓库最新的远程默认分支建立独立升级 Work Item。
2. 记录当前安装、目标 release tag、remote、默认分支和 base commit。
3. 让 installer 生成计划和冲突报告；不要静默覆盖项目拥有的治理文件。
4. 阅读受管理文件差异和回滚备份目录。
5. 只有理解计划和冲突后才确认写入。
6. 将 adopter 的校准和本地检查作为独立证据执行。
7. 按普通 Work Item 生命周期评审、提交、推送和合并；installer 不执行这些外部 Git 操作。

## 使用事例和预期结果

请求：

> “升级时不要在 Candidate 失败时改掉当前配置；如果有 active Work Item 或未解决冲突就停止。”

预期结果：计划会列出 source 和 target，Contract/Summary 会记录变更，冲突会显式出现，
备份可用于回滚，激活失败时旧的 Active Configuration 仍然可用。

## 停止和恢复

存在 active Work Item、无法建立远程默认分支、受管理文件已经分叉、目标是 downgrade，或
冲突报告缺失/格式错误时，在写入前停止。先解决冲突或提供明确的 base 证据，再重试。
只有在有意进行并经过单独评审的恢复场景中，才使用 `--upgrade-with-active`。

## 高级入口

完整的 installer 选项、release source 变量、回滚行为和冲突报告契约见[升级技术参考（英文）](reference/upgrade.md)。
这是命令和文件细节的 canonical English reference。

installer 不会提交、推送、创建或合并 PR，也不会删除评审分支。这些动作需要单独的 Work
Item 证据以及人和 provider 的决定。

相关入口：[能力一览与边界](capabilities.zh-CN.md)、[Work Item 生命周期](operations/work-item-lifecycle.zh-CN.md)、
[恢复](operations/recovery.zh-CN.md)。
