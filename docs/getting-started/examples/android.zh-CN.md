---
author: Ray
title: "Android 安装实例"
description: 面向初学者的 Android 工程 AI Cockpit 校准实例。
keywords: [ai-cockpit, android, gradle, 安装]
---

# Android 安装实例

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
## 复制 Android 提示词

```text
阶段 1～4、6、7 只读逐项引导；阶段 5 只提出 Candidate diff，不写入，实际写入
只由中文主手顺第 9 步另行批准。用中文解释 Gradle、module、flavor、variant、
JDK、SDK、unit test、device test。每阶段输出证据、含义、建议值、未证明内容、
预期结果、STOP/联系谁。不得编造 Gradle task，也不得声称 JDK、Android SDK、
emulator/device、签名、secret、hosted run 可用；每阶段等待，不修改文件。
```

例：发现 `gradlew` 只表示工程提供 Gradle Wrapper，不证明需要的 JDK/Android SDK
已安装。module 证据明确后才推荐 `android`；variant 未知时联系 Android owner。

每次只复制一行：

<!-- platform-step-table: copy-request,example,pass,stop -->
| 阶段 | 精确请求 | 示例与选择 | PASS | STOP/联系 |
| --- | --- | --- | --- | --- |
| 1 检测 | “只读列 Wrapper/settings/build/catalog、所有 module、flavor、build type、variant、tests、manifest、generated、CI。” | 有 `gradlew` 不代表 module 叫 app。 | module/test 已映射。 | module/variant Unknown；Android owner。 |
| 2 工具链 | “显示 Wrapper、AGP、Kotlin、JDK、SDK level、device、signing、credential、CI image 证据。” | Wrapper 不证明 JDK/SDK 可用。 | version/environment 有证据。 | JDK/SDK/device/secret 缺失；Android/CI owner。 |
| 3 边界 | “提出 `android`/`generic`，逐 module 列 source/test 和 cache/build/generated 排除。” | 混合 monorepo 可暂用 generic。 | 每个 module 有证据。 | 路径无 owner；module owner。 |
| 4 命令 | “从 files/CI 复制 Wrapper task，解释 module/flavor/build type/variant、前提、成功/失败。” | unit、lint、device、release 分开。 | exact task 有证据。 | 编造 task/variant 未知；Android/CI owner。 |
<!-- platform-stage5: proposal-only -->
| 5 校准 | “提出 generation、manifest、R8、migration、signing、bundle、permission、privacy/security、reviewer 的 Candidate diff；不写入或激活。” | release signing 需人工 reviewer。 | 提议 diff 的高风险/生成路径完整。 | owner/generator 缺失；build/release owner。 |
| 6 恢复 | “保留输出，解决确切 JDK/SDK/device/secret/generated drift 后重跑同一 Wrapper task。” | unit 不能代替 device evidence。 | 同一 task 通过。 | 较弱替代；停止。 |
| 7 验证 | “对应十阶段、variant-specific local/hosted、PR Head SHA、人工 merge、closure、删分支。” | hosted smoke 不是本 variant 证据。 | 都匹配本 repo/commit。 | 缺证据；repo owner。 |

下方七个小节只是表格行的只读解释，不要再次执行。
<!-- platform-stage: detect-project -->
## 1. 检测工程

只读列出 `gradlew`、settings/build/version catalog、module、product flavor、
build type、unit test、`androidTest`、manifest、生成目录和 CI；不能假设 app module 名为 `app`。

<!-- platform-stage: collect-toolchain-evidence -->
## 2. 收集工具链证据

记录 Wrapper/AGP/Kotlin/JDK 声明、SDK level、variant、emulator/device、signing、
credential 和 CI image。Gradle Wrapper 不证明 JDK、Android SDK、设备、secret 或 hosted CI 可用。

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. 选择 stack 与边界

已证实的 Android 布局选 `android`；特殊混合 monorepo 在 module 边界校准前选
`generic`。逐 module 映射 `src/main`、`src/test`、`src/androidTest`，按工程证据排除 `.gradle`、`build`、SDK 和生成物。

<!-- platform-stage: discover-quality-commands -->
## 4. 发现质量命令

只用文件/CI 证明的 Wrapper task，明确 module、flavor、build type、variant。
unit、lint、instrumented/device、release build 是不同证据，不得编造 task 名。

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. 校准生成物与关键路径

只提出 resource/code generation、manifest、ProGuard/R8、migration、signing 的 Candidate 项目，
release bundle、permission、privacy/security 配置和 reviewer。

<!-- platform-stage: stop-and-recover -->
## 6. 停止与恢复

JDK/SDK 不匹配、variant 未知、device 不可用、secret 缺失、daemon/cache 状态不明或 generated drift 时停止。收集证据并重跑相同 Wrapper task，不能用更轻任务冒充通过。

<!-- platform-stage: verify-platform-adoption -->
## 7. 验证 Android 采用

十阶段校准、variant 特定命令证据、unit/device 与 local/hosted 分离结果、人工审核 PR 和 lifecycle closure 均为必需。
