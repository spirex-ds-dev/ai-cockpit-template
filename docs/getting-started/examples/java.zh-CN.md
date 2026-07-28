---
author: Ray
title: "Java 安装实例"
description: 面向初学者的 Java 工程 AI Cockpit 校准实例。
keywords: [ai-cockpit, java, maven, gradle, 安装]
---

# Java 安装实例

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
## 复制 Java 提示词

```text
阶段 1～4、6、7 只读逐项引导；阶段 5 只提出 Candidate diff，不写入，实际写入
只由中文主手顺第 9 步另行批准。用中文解释 Maven、Gradle、Wrapper、module、JDK、
profile、unit test、integration test。每阶段输出证据、含义、建议值、未证明内容、
预期结果、STOP/联系谁。不得编造命令，也不得声称 JDK、build tool、service、
credential、network 或 hosted run 可用。现在不要开始阶段 1；等待我复制主操作表
第 1 行。此后每阶段等待，不修改文件。
```

例：发现 `pom.xml` 只表示工程描述了 Maven build，不证明 Maven、所需 JDK 或
integration service 可用。module 映射后才推荐 `java`；profile 未知时联系 Java owner。

### 主操作表

每次只复制一行：

<!-- platform-stage5: proposal-only -->
<!-- platform-step-table: copy-request,example,pass,stop -->
| 阶段 | 精确请求 | 示例与选择 | PASS | STOP/联系 |
| --- | --- | --- | --- | --- |
| 1 检测 | “只读列 Maven/Gradle wrapper/manifest、module、toolchain、JDK、source/test、plugin、coverage、generated、packaging、CI。” | `pom.xml` 不证明单 module 或工具可用。 | module/build family 已映射。 | 布局 Unknown；Java owner。 |
| 2 工具链 | “显示 wrapper、JDK/vendor、mirror、service、credential、network、hosted image 证据。” | JDK 声明是需求，不是本机可用证明。 | 环境有证据。 | JDK/service/credential/network Unknown；Java/CI owner。 |
| 3 边界 | “提出 `java`/`generic`，列维护 source/test/resource 和 target/build/cache/generated/vendor 排除。” | 混合 monorepo 映射前用 generic。 | 每条路径有 owner。 | 生成/源码 ownership 不清；module owner。 |
| 4 命令 | “从 files/CI 复制 wrapper lifecycle/task，解释 profile/module/filter/service/coverage、前提、成功/失败。” | compile/unit/integration/package/publish 分开。 | exact command 有证据。 | 编造 command/profile 或 service 缺失；Java/build owner。 |
| 5 校准 | “提出 annotation/schema/client generation、migration、catalog、signing/publishing、security/release、reviewer 的 Candidate diff；不要写入或激活。” | publish 不由 unit test 单独证明。 | 提议 diff 的 generator/关键路径完整。 | generator/reviewer 缺失；build/release owner。 |
| 6 恢复 | “保存输出，解决 JDK/module/profile/service/network/generated drift 后重跑同一命令。” | unit 不能代替 integration。 | 同一命令通过。 | 拒绝较弱替代并 STOP，联系阻断阶段指定的 owner；证据补齐后重跑同一阶段。 |
| 7 验证 | “输出逐项证据表，每行包含 module/profile、证据路径/链接、commit SHA、PASS/STOP 和缺失项；覆盖十阶段、local/hosted、PR Head SHA、人工 merge、closure 与删分支。” | 模板 fixture 不是采用方证据。 | 所有行匹配 repo/commit 且无缺项。 | 缺证据；repo owner。 |

<!-- platform-filled-example: seven-stages -->
### 虚构 `SampleOrders` 的填写示例

每一行都是独立示例。遇到 STOP 不继续；得到 owner 的回答后重跑同一阶段，确认 PASS
才进入下一阶段。后续行表示前面的 STOP 已经解决后的显示示例。

| 阶段 | 代理回答示例 | 用户复制的回答 | 成功显示 | 停止时提交的信息 |
| --- | --- | --- | --- | --- |
| 1 | “发现 Maven Wrapper、`api`/`service` module、unit/integration test。” | `把所有 module 与 test 类型列为候选。` | module、build、test 清单。 | 把 `pom.xml` 路径交给 Java owner。 |
| 2 | “toolchain 是 Temurin JDK 21；integration DB 未确认。” | `DB 保持 Unknown 并 STOP。` | JDK 与 service 的来源行。 | 把 toolchain/service 信息交给 Java/CI owner。 |
| 3 | “`src/main` 是维护源码，`target/` 是输出；建议 java preset。” | `同意有证据的边界。` | 每个 module 的包含/排除路径。 | 把 ownership 不明项交给 module owner。 |
| 4 | “CI 有 Wrapper unit command；integration profile 未确认。” | `只记录 unit；integration 保持 Unknown 并 STOP。联系 build owner 后重跑阶段 4；只有证据证明无需 integration test 时才可写 not applicable。` | 准确 command、来源与成功条件。 | 把 profile/service 信息交给 build owner。 |
| 5 | “schema generation、migration、publishing 是关键路径。” | `只提出带 reviewer 的 Candidate diff，不要写入或激活。` | 建议 generator、路径与 reviewer。 | 把 owner 不明项交给 release owner。 |
| 6 | “integration 无法连接 DB。” | `保存日志，准备相同 service 后重跑同一 integration command。` | 同一 command 成功。 | 把日志、profile、service 交给 owner。 |
| 7 | “已检查 module/profile CI、PR Head SHA、merge、closure、删分支。” | `列出全部链接，只有无缺项才把 Java adoption 标为 PASS。` | 全部证据绑定同一 commit。 | 把缺失项和 PR URL 交给 repo owner。 |

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

只提出以下 Candidate 项目：annotation/code、schema/client generation、migration、
dependency lock/catalog、signing/publishing、security 配置、release automation 和 reviewer。

<!-- platform-stage: stop-and-recover -->
## 6. 停止与恢复

JDK 不匹配、module/profile 未知、service/credential 缺失、仅网络可用依赖或 generated
drift 时停止。收集 owner/CI 证据后重跑相同命令，不能用 unit test 代替 integration evidence。

<!-- platform-stage: verify-platform-adoption -->
## 7. 验证 Java 采用

十阶段校准、module/profile 特定命令、local/hosted 分离证据、人工审核 PR 和 lifecycle closure 均为必需。
