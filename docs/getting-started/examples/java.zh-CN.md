---
author: Ray
title: "开始 Java 校准"
description: AI Cockpit 安装后，面向 Java 工程的简单 Work Item 校准入口。
keywords: [ai-cockpit, java, maven, gradle, 校准]
---

# 开始 Java 校准

在 AI Cockpit 安装完成后使用本页。开始前不需要理解 JDK、Maven、Gradle、module、服务或校准内部机制。

<!-- platform-entry: work-item-first -->
## 只复制一次

```text
这是一个 Java 工程。请创建校准 Work Item 的计划，但暂时不要修改文件。
请只读检查仓库，并用简单中文告诉我：这是哪种 Java 工程、发现了什么、哪些内容是
Unknown、以及还需要我确认什么。不要猜测 JDK、build tool、module、profile、service、
credential、命令或 CI 事实。写入前必须等待我的确认。
```

## 接下来会发生什么

Agent 会创建可审核的校准 Work Item。你先确认计划，再只批准其中列出的修改。仅发现
Maven 或 Gradle 文件，并不代表 JDK、wrapper、service、凭据或 hosted CI 已准备好。

## Maven 多模块修正模板

仅在 Maven 失败可能涉及内部模块、私有 mirror 或多个 Java lane 时使用。把下面事实记录到 active Work Item；
不要从 `pom.xml` 猜测值。

1. 选择一个构建路径：单个由工程声明的 **reactor command**，或明确声明的 module dependency order。记录所选
   command 或有序 module list、working directory，以及它为何适用于该工程。不能仅因存在 directory 就单独运行 module。
2. 执行 Maven 前，记录选定 `settings.xml` 的 path、approved mirror 是否可达、所需 private-repository access
   是否可用。不得在 Work Item 或 command transcript 中粘贴 credential、token、password 或 private repository URL。
3. 每个 Java lane 都要记录所需 Java major，以及 Maven command 选择的实际 `java` runtime。actual major 不同的
   lane 为 **blocked**；先选择 approved toolchain 或修正 lane declaration，再 retry。

如果缺少 settings file、mirror、access grant、reactor command、dependency order 或 Java-major 事实，应报告
`blocked`，写清缺失事实和 recovery condition：取得 project owner 的 approved configuration，记录到 Work Item，
然后重新执行已声明的 project command。此模板不会配置 Maven、安装 JDK、访问 private repository，也不证明 adopter build 已通过。

## Java runtime lane gate

已安装的 Java preset 会在每个 formatter、test 或 lint command 前检查 runtime。在
`Makefile.ai.stack` 中记录工程已批准的 lane 和 major；它们是需要校准的事实，不能从 build file 推断：

```make
AI_COCKPIT_JAVA_LANE = java17
AI_COCKPIT_JAVA_REQUIRED_MAJOR = 17
AI_COCKPIT_JAVA_COMMAND = java
```

如果工程已批准的 environment manager 通过 `JAVA_HOME` 选择 runtime，检查器会观察
`JAVA_HOME/bin/java`；否则观察 `AI_COCKPIT_JAVA_COMMAND`（默认是 `PATH` 中的 `java`）。major
缺失或不匹配时，会在 delegated command 执行前 **blocked**。应选择工程已批准的 runtime，或修正记录的
major，再 retry。preset 不会安装、切换或修改 JDK、`JAVA_HOME` 或 environment manager。

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-next: calibration-and-recovery -->
## 需要帮助？

Work Item 会提问的内容请看[工程校准指南](../calibration.zh-CN.md)。如果某项是 Unknown 或
检查停止，请看[安装故障排除](../../troubleshooting/installation.zh-CN.md)。Unknown 必须保持
Unknown，不能用较弱的检查替代。
