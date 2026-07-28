---
author: Ray
title: "Android 安装实例"
description: 面向初学者的 Android 工程 AI Cockpit 校准实例。
keywords: [ai-cockpit, android, gradle, 安装]
---

# Android 安装实例

先完成[中文安装手顺](../installation.zh-CN.md)第 1～4 步。不要从上到下一次执行
本页。当前位于主手顺第 5～6 步时，逐行复制下表第 1～4 行；完成后返回主手顺
第 7 步。其他时候只使用下方对应表里与当前主步骤一致的一行。

下面的 setup 提示词只复制一次，它只规定代理如何引导。代理回答后，每次只执行
**主操作表**的一行。后面的填写示例表只用于理解，不是第二套需要复制的步骤。

表中用词：证据（evidence）、责任人（owner）、检查人（reviewer）、发布身份
（signing）、设置文件（manifest）、测试数据（fixture）、完整结束处理（closure）。
代理必须同时显示正式名称和日常含义。

| 中文主手顺 | 本页动作 | 完成后返回 |
| --- | --- | --- |
| 第 1～4 步 | 不操作；先完成调查 | 第 5 步 |
| 第 5～6 步 | 逐行复制表格 1～4 | 第 7 步 |
| 第 7～8 步 | 不操作；完成写入/Adoption closure | 第 9 步 |
| 第 9 步 | 在校准过程中使用第 5 行 | 返回并完成第 9 步其余内容，再进入第 10 步 |
| 平台第 1～5 行产生的 STOP | 复制第 6 行 | 原来被阻断的平台阶段 |
| 第 13 步后 | 只复制一次第 7 行 | 第 14/15 步 |

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-prompt: copy-ready -->
## 复制 Android 提示词

```text
阶段 1～4、6、7 只读逐项引导；阶段 5 只提出 Candidate diff，不写入，实际写入
只由中文主手顺第 9 步另行批准。用中文解释 Gradle、module、flavor、build type、
variant、JDK、SDK、unit test、device test，并说明 variant 是 flavor 与 build type
组合形成的产品配置。每阶段输出证据、含义、建议值、未证明内容、
预期结果、STOP/联系谁。不得编造 Gradle task，也不得声称 JDK、Android SDK、
emulator/device、签名、secret、hosted run 可用。现在不要开始阶段 1；等待我复制
主操作表第 1 行。此后每阶段等待，不修改文件。
```

例：发现 `gradlew` 只表示工程提供 Gradle Wrapper，不证明需要的 JDK/Android SDK
已安装。module 证据明确后才推荐 `android`；variant 未知时联系 Android owner。

### 主操作表

每次只复制一行：

<!-- platform-stage5: proposal-only -->
<!-- platform-step-table: copy-request,example,pass,stop -->
| 阶段 | 精确请求 | 示例与选择 | PASS | STOP/联系 |
| --- | --- | --- | --- | --- |
| 1 检测 | “只读列 Wrapper/settings/build/catalog、所有 module、flavor、build type、variant、tests、manifest、generated、CI。” | 有 `gradlew` 不代表 module 叫 app。 | module/test 已映射。 | module/variant Unknown；Android owner。 |
| 2 工具链 | “显示 Wrapper、AGP、Kotlin、JDK、SDK level、device、signing、credential、CI image 证据。” | Wrapper 不证明 JDK/SDK 可用。 | version/environment 有证据。 | JDK/SDK/device/secret 缺失；Android/CI owner。 |
| 3 边界 | “提出 `android`/`generic`，逐 module 列 source/test 和 cache/build/generated 排除。” | 混合 monorepo 可暂用 generic。 | 每个 module 有证据。 | 路径无 owner；module owner。 |
| 4 命令 | “从 files/CI 复制 Wrapper task，解释 module/flavor/build type/variant、前提、成功/失败。” | unit、lint、device、release 分开。 | exact task 有证据。 | 编造 task/variant 未知；Android/CI owner。 |
| 5 校准 | “提出 generation、manifest、R8、migration、signing、bundle、permission、privacy/security、reviewer 的 Candidate diff；不写入或激活。” | release signing 需人工 reviewer。 | 提议 diff 的高风险/生成路径完整。 | owner/generator 缺失；build/release owner。 |
| 6 恢复 | “保留输出，解决确切 JDK/SDK/device/secret/generated drift 后重跑同一 Wrapper task。” | unit 不能代替 device evidence。 | 同一 task 通过。 | 拒绝较弱替代并 STOP，联系阻断阶段指定的 owner；证据补齐后重跑同一阶段。 |
| 7 验证 | “输出逐项证据表，每行包含 variant、证据路径/链接、commit SHA、PASS/STOP 和缺失项；覆盖十阶段、local/hosted、PR Head SHA、人工 merge、closure 与删分支。” | hosted smoke 不是本 variant 证据。 | 所有行匹配本 repo/commit 且无缺项。 | 缺证据；repo owner。 |

<!-- platform-filled-example: seven-stages -->
### 虚构 `SampleShop` 的填写示例

每一行都是独立示例。遇到 STOP 不继续；得到 owner 的回答后重跑同一阶段，确认 PASS
才进入下一阶段。后续行表示前面的 STOP 已经解决后的显示示例。

| 阶段 | 代理回答示例 | 用户复制的回答 | 成功显示 | 停止时提交的信息 |
| --- | --- | --- | --- | --- |
| 1 | “发现 `:app`、`:catalog`、demo/prod flavor、unit/device test。” | `把所有 module 与 variant 列为候选；暂不运行 task。` | module、variant、test 清单。 | 把 settings/build 文件名交给 Android owner。 |
| 2 | “Wrapper 8.9、AGP 8.7、JDK 17、compileSdk 35；SDK/device 未确认。” | `SDK 与 device 保持 Unknown 并 STOP。` | 每个版本的来源行。 | 把版本清单交给 Android/CI owner。 |
| 3 | “`src/main` 是维护源码，`build/` 是输出；建议 android preset。” | `同意有证据的边界。` | 每个 module 的包含/排除路径。 | 把无 owner 的路径交给 module owner。 |
| 4 | “从 CI 取得 `:app:testDemoDebugUnitTest`；device task 未确认。” | `只记录 unit task，device evidence 保持 Unknown 并 STOP；联系 Android/CI owner 后重跑阶段 4。只有证据证明无需 device test 时才可写 not applicable。` | 准确 task、来源与成功条件。 | 把 task 与 variant 交给 CI owner。 |
| 5 | “signing、R8、permission、release bundle 是关键路径。” | `只提出带 reviewer 的 Candidate diff，不要写入或激活。` | 建议路径与 reviewer。 | 把 owner 不明项交给 release owner。 |
| 6 | “JDK mismatch 导致失败。” | `保存日志，准备 JDK 17 后重跑同一 Wrapper task。` | 同一 task 成功。 | 把日志、JDK、task 交给 build owner。 |
| 7 | “已检查 variant-specific CI、PR Head SHA、merge、closure、删分支。” | `列出全部链接，只有无缺项才把 Android adoption 标为 PASS。` | 全部证据绑定同一 commit。 | 把缺失项和 PR URL 交给 repo owner。 |

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

只提出以下 Candidate 项目：resource/code generation、manifest、ProGuard/R8、
migration、signing、release bundle、permission、privacy/security 配置和 reviewer。

<!-- platform-stage: stop-and-recover -->
## 6. 停止与恢复

JDK/SDK 不匹配、variant 未知、device 不可用、secret 缺失、daemon/cache 状态不明或 generated drift 时停止。收集证据并重跑相同 Wrapper task，不能用更轻任务冒充通过。

<!-- platform-stage: verify-platform-adoption -->
## 7. 验证 Android 采用

十阶段校准、variant 特定命令证据、unit/device 与 local/hosted 分离结果、人工审核 PR 和 lifecycle closure 均为必需。
