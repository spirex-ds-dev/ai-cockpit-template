---
author: Ray
title: "安装故障排除"
description: "按现象组织的 AI Cockpit 安装恢复说明。"
---

# 安装故障排除

不确定时就停止；不要用更弱的替代方案让安装看起来像成功。

## 工作区不干净

先保存或解释已有修改；安装时绝不覆盖它们。

## 没有初始 commit 或默认分支

请仓库负责人先建立工程基线，再安装。

## 缺少 Python、Make 或其他工具

安装或申请批准的工具链，再重新检查准备情况。

## Release 验证失败

不得静默选择旧 Release；请进入[严格验证路径](../getting-started/installation-security.zh-CN.md)。

## 已有 Active Work Item、文件冲突、Cockpit Status 过期或无法创建 PR

保留证据，写明缺失事实和负责人，然后启动或恢复对应的 Work Item；不得绕过生命周期。

## Hosted CI 没有运行

记录准确 commit 和失败 Job，然后联系仓库或 CI 负责人。

## 卸载 AI Cockpit

请使用独立的[卸载路径](uninstall.zh-CN.md)。它会先收集事实并创建可审核的移除计划；
绝不会静默删除工程工作。
