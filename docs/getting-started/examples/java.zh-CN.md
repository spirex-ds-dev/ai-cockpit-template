---
author: Ray
title: "Java 安装实例"
description: 面向初学者的 Java 工程 AI Cockpit 校准实例。
keywords: [ai-cockpit, java, maven, gradle, 安装]
---

# Java 安装实例

先完成[中文安装手顺](../installation.zh-CN.md)第 1～4 步。安装第 5～6 步使用平台
阶段 1～4；返回第 7～8 步完成写入/Adoption closure；校准时使用阶段 5；遇阻用
阶段 6；主手顺第 13 步后用阶段 7。本页不替代 lifecycle。

| 中文主手顺 | 本页动作 | 完成后返回 |
| --- | --- | --- |
| 第 1～4 步 | 不操作；先完成调查 | 第 5 步 |
| 第 5～6 步 | 逐行复制表格 1～4 | 第 7 步 |
| 第 7～8 步 | 不操作；完成写入/Adoption closure | 第 9 步 |
| 第 9 步 | 复制第 5 行 | 第 10 步 |
| 任一 STOP | 复制第 6 行 | 原来被阻断的步骤 |
| 第 13 步后 | 只复制一次第 7 行 | 第 14/15 步 |

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-prompt: copy-ready -->
## 复制 Java 提示词

```text
阶段 1～4、6、7 只读逐项引导；阶段 5 只提出 Candidate diff，不写入，实际写入
只由中文主手顺第 9 步另行批准。用中文解释 Maven、Gradle、Wrapper、module、JDK、
profile、unit test、integration test。每阶段输出证据、含义、建议值、未证明内容、
预期结果、STOP/联系谁。不得编造命令，也不得声称 JDK、build tool、service、
credential、network 或 hosted run 可用；每阶段等待，不修改文件。
```

例：发现 `pom.xml` 只表示工程描述了 Maven build，不证明 Maven、所需 JDK 或
integration service 可用。module 映射后才推荐 `java`；profile 未知时联系 Java owner。

每次只复制一行：

<!-- platform-step-table: copy-request,example,pass,stop -->
| 阶段 | 精确请求 | 示例与选择 | PASS | STOP/联系 |
| --- | --- | --- | --- | --- |
| 1 检测 | “只读列 Maven/Gradle wrapper/manifest、module、toolchain、JDK、source/test、plugin、coverage、generated、packaging、CI。” | `pom.xml` 不证明单 module 或工具可用。 | module/build family 已映射。 | 布局 Unknown；Java owner。 |
| 2 工具链 | “显示 wrapper、JDK/vendor、mirror、service、credential、network、hosted image 证据。” | JDK 声明是需求，不是本机可用证明。 | 环境有证据。 | JDK/service/credential/network Unknown；Java/CI owner。 |
| 3 边界 | “提出 `java`/`generic`，列维护 source/test/resource 和 target/build/cache/generated/vendor 排除。” | 混合 monorepo 映射前用 generic。 | 每条路径有 owner。 | 生成/源码 ownership 不清；module owner。 |
| 4 命令 | “从 files/CI 复制 wrapper lifecycle/task，解释 profile/module/filter/service/coverage、前提、成功/失败。” | compile/unit/integration/package/publish 分开。 | exact command 有证据。 | 编造 command/profile 或 service 缺失；Java/build owner。 |
<!-- platform-stage5: proposal-only -->
| 5 校准 | “提出 annotation/schema/client generation、migration、catalog、signing/publishing、security/release、reviewer 的 Candidate diff；不要写入。” | publish 不由 unit test 单独证明。 | 提议 diff 的 generator/关键路径完整。 | generator/reviewer 缺失；build/release owner。 |
| 6 恢复 | “保存输出，解决 JDK/module/profile/service/network/generated drift 后重跑同一命令。” | unit 不能代替 integration。 | 同一命令通过。 | 较弱替代；停止。 |
| 7 验证 | “对应十阶段、module/profile local/hosted、PR Head SHA、人工 merge、closure、删分支。” | 模板 fixture 不是采用方证据。 | 都匹配 repo/commit。 | 缺证据；repo owner。 |

下方七个小节只是表格行的只读解释，不要再次执行。
<!-- platform-stage: detect-project -->
## 1. 检测工程

只读列出 Maven/Gradle wrapper 与 manifest、module、toolchain、JDK 声明、
source/test set、integration-test plugin、coverage、generated source、packaging 与 CI；不能假设只有一个 module。

<!-- platform-stage: collect-toolchain-evidence -->
## 2. 收集工具链证据

记录 wrapper、所需 JDK/vendor、mirror、service、credential 和 hosted image。
发现 `pom.xml` 或 Gradle 文件不证明 Maven、Gradle、正确 JDK、网络服务、secret 或 hosted CI 可用。

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. 选择 stack 与边界

Java 布局已证实则选 `java`；混合 monorepo 在 module 映射前选 `generic`。
识别维护中的 source/test/resource，按证据排除 target/build/cache/generated/vendor。

<!-- platform-stage: discover-quality-commands -->
## 4. 发现质量命令

优先工程 wrapper，只从文件/CI 提取 lifecycle/task；解释 profile、module、test
filter、integration service 和 coverage 输出。compile、unit、integration、静态分析、package、publish 是不同证据，不得编造命令。

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. 校准生成物与关键路径

只提出 annotation/code、schema/client generation、migration、dependency lock/catalog 的 Candidate 项目，
signing/publishing、security 配置、release automation 和 reviewer。

<!-- platform-stage: stop-and-recover -->
## 6. 停止与恢复

JDK 不匹配、module/profile 未知、service/credential 缺失、仅网络可用依赖或 generated
drift 时停止。收集 owner/CI 证据后重跑相同命令，不能用 unit test 代替 integration evidence。

<!-- platform-stage: verify-platform-adoption -->
## 7. 验证 Java 采用

十阶段校准、module/profile 特定命令、local/hosted 分离证据、人工审核 PR 和 lifecycle closure 均为必需。
