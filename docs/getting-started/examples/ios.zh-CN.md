---
author: Ray
title: "开始 iOS 校准"
description: AI Cockpit 安装后，面向 iOS 工程的简单 Work Item 校准入口。
keywords: [ai-cockpit, ios, xcode, swift, 校准]
---

# 开始 iOS 校准

在 AI Cockpit 安装完成后使用本页。开始前不需要理解 Xcode、签名、scheme 或校准内部机制。

<!-- platform-entry: work-item-first -->
## 只复制一次

```text
这是一个 iOS 工程。请创建校准 Work Item 的计划，但暂时不要修改文件。
请只读检查仓库，并用简单中文告诉我：这是哪种 iOS 工程、发现了什么、哪些内容是
Unknown、以及还需要我确认什么。不要猜测 Xcode、scheme、simulator、signing、device、
命令或 CI 事实。写入前必须等待我的确认。
```

## 接下来会发生什么

Agent 会创建可审核的校准 Work Item。你先确认计划，再只批准其中列出的修改。仅发现
工程文件或 workspace，并不代表 Xcode、scheme、simulator、签名或 hosted macOS CI 已准备好。

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-next: calibration-and-recovery -->
## 需要帮助？

Work Item 会提问的内容请看[工程校准指南](../calibration.zh-CN.md)。如果某项是 Unknown 或
检查停止，请看[安装故障排除](../../troubleshooting/installation.zh-CN.md)。Unknown 必须保持
Unknown，不能用较弱的检查替代。
