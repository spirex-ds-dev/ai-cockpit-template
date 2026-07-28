---
author: Ray
title: "iOS 安装实例"
description: 面向初学者的 iOS 工程 AI Cockpit 校准实例。
keywords: [ai-cockpit, ios, xcode, swift, 安装]
---

# iOS 安装实例

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
| 第 9 步 | 在校准过程中使用表格第 5 行 | 返回并完成第 9 步其余内容，再进入第 10 步 |
| 平台第 1～5 行产生的 STOP | 复制第 6 行 | 原来被阻断的平台阶段 |
| 第 13 步后 | 只复制一次第 7 行 | 第 14/15 步 |

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-prompt: copy-ready -->
## 复制 iOS 提示词

```text
阶段 1～4、6、7 只读逐项引导；阶段 5 只提出 Candidate diff，不写入，实际写入
只由中文主手顺第 9 步另行批准。先解释每个 Xcode/Swift 术语。每阶段输出：
发现的证据、中文含义、建议 Wizard/Calibration 值、仍未证明的内容、预期结果、
STOP/联系谁。不得编造 xcodebuild、scheme、destination、签名、simulator、
CocoaPods 或 hosted CI。现在不要开始阶段 1；等待我复制主操作表第 1 行。此后每阶段
等待我的回答，不修改文件。
```

例：发现 `MyApp.xcworkspace` 只表示“有 Xcode workspace”，不表示 Xcode 或可运行
scheme 已存在。建议从 `swift` preset 开始并校准工程命令；缺 scheme/destination
证据时联系 iOS owner。

### 主操作表

每次只复制一行：

<!-- platform-stage5: proposal-only -->
<!-- platform-step-table: copy-request,example,pass,stop -->
| 阶段 | 精确请求 | 示例与选择 | PASS | STOP/联系 |
| --- | --- | --- | --- | --- |
| 1 检测 | “只读列出 Xcode project/workspace、Package.swift、依赖文件、app/extension、scheme、tests、CI。” | 有 workspace 不等于可运行 app。 | 布局/owner 清楚。 | 混合/未知；iOS owner。 |
| 2 工具链 | “显示 Xcode/Swift version、依赖管理、scheme、destination、signing、simulator/device、hosted macOS 证据。” | CI 固定 Xcode 不证明本机可用。 | 所需工具/环境都有证据。 | version/scheme/destination/signing/host 缺失；iOS/release owner。 |
| 3 边界 | “提出 `swift` 或 `generic`，列维护源码及 generated/vendor/output 排除与理由。” | `swift` 只是起点，非 SPM 命令仍要校准。 | 每个路径有解释。 | preset 隐藏混合布局；module owner。 |
| 4 命令 | “从 repo/CI 原样复制命令，解释 scheme、destination、configuration、前提、成功和失败；不得编造。” | test 与 archive/signing 是不同证据。 | 命令/环境有证据。 | 命令、secret 或 device 缺失；iOS/CI owner。 |
| 5 校准 | “提出 generator、entitlement、privacy manifest、signing、archive/release、migration、deploy、reviewer 的 Candidate diff；不要写入或激活。” | 签名路径需 release reviewer。 | 提议 diff 的关键/生成路径完整。 | owner/再生成规则缺失；build/release owner。 |
| 6 恢复 | “保存失败证据，写出缺失事实/owner，拿到证据后更新 Candidate 并重跑同一检查。” | Unknown destination 保持阻断。 | 同一要求后来通过。 | 拒绝较弱替代并 STOP，联系阻断阶段指定的 owner；证据补齐后重跑同一阶段。 |
| 7 验证 | “输出逐项证据表，每行包含要求、证据路径/链接、commit SHA、PASS/STOP 和缺失项；覆盖十阶段、local/hosted、PR Head SHA、人工 merge、closure 与删分支。” | 模板 SPM fixture 不是采用方 Xcode 证据。 | 所有行属于本 repo/commit 且无缺项。 | 缺平台/lifecycle 证据；repo owner。 |

<!-- platform-filled-example: seven-stages -->
### 虚构 `SampleNotes` 的填写示例

每一行都是独立示例。遇到 STOP 不继续；得到 owner 的回答后重跑同一阶段，确认 PASS
才进入下一阶段。后续行表示前面的 STOP 已经解决后的显示示例。

| 阶段 | 代理回答示例 | 用户复制的回答 | 成功显示 | 停止时提交的信息 |
| --- | --- | --- | --- | --- |
| 1 | “发现 `SampleNotes.xcworkspace`、app target、unit-test target；shared scheme 未确认。” | `shared scheme 是 Unknown。不要改动，请联系 iOS owner。` | workspace 与 target 清单。 | 把所有检测路径交给 iOS owner。 |
| 2 | “CI 声明 Xcode 16.2、scheme SampleNotes、iPhone 16 Simulator。” | `把三项记为候选并 STOP；向 iOS owner 取得本机可用性证据后重跑阶段 2。` | 工程/CI 的来源行。 | 把版本与 CI 文件名交给 owner。 |
| 3 | “`Sources/` 是维护源码，`DerivedData/` 是输出；建议以 swift preset 为起点。” | `同意有证据的边界；不要确定非 SPM 命令。` | 分开显示包含/排除路径。 | 把无法判断的路径交给 module owner。 |
| 4 | “已从 CI 复制准确 test command；archive/signing command 未确认。” | `只记录 test command；archive/signing 保持 Unknown 并 STOP。` | command 来源、前提、成功显示。 | 把 command 和缺失事实交给 CI/release owner。 |
| 5 | “entitlement 与 privacy manifest 是关键路径；Release Team 审核 signing。” | `只提出 Candidate diff，不要写入或激活。` | 建议路径与 reviewer。 | 把 owner 不明项交给 release owner。 |
| 6 | “缺少 simulator，test 失败。” | `保存日志，准备相同 destination 后重跑同一 test。` | 同一 command 成功。 | 把日志、Xcode 版本、destination 交给 owner。 |
| 7 | “已检查 PR #123、Head SHA、hosted check、merge、closure、删分支。” | `逐项显示链接，只有全部齐全才把 iOS adoption 标为 PASS。` | 七类证据都绑定同一 commit。 | 把缺失项和 PR URL 交给 repo owner。 |

下方七个小节只是表格行的只读解释，不要当作第二套流程再次执行。
<!-- platform-stage: detect-project -->
## 1. 检测工程

让代理只读列出 `.xcodeproj`、`.xcworkspace`、`Package.swift`、`Podfile`、
`Cartfile`、scheme、app/extension、unit/UI test target 和 CI 文件，并区分纯 SPM package 与 Xcode app/workspace。

<!-- platform-stage: collect-toolchain-evidence -->
## 2. 收集工具链证据

记录工程/CI 声明的 Xcode/Swift 版本、依赖管理器、scheme、签名需求和 simulator/device 条件。发现 Xcode 文件不代表 Xcode、CocoaPods、simulator、签名身份或 hosted macOS CI 可用；Unknown 必须阻断。

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. 选择 stack 与边界

Swift/Xcode 布局以 `swift` preset 为起点；非 SPM 工程必须用工程证据替换 SPM
默认命令。只有混合仓库证据表明 Swift preset 会误导时才选 `generic`。源码通常包含 app/framework；DerivedData、`.build`、Pods、生成代码和 vendor 默认排除。

<!-- platform-stage: discover-quality-commands -->
## 4. 发现质量命令

让代理从仓库或 hosted workflow 原样提取命令，并解释 scheme、destination、configuration 和前提。不得编造 `xcodebuild`/`pod`。unit、UI/device、archive、signing 分别记录。

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. 校准生成物与关键路径

只提出以下 Candidate 项目：代码/工程文件生成、entitlement、signing、privacy
manifest、release/archive 配置、migration 与部署脚本；签名和发布路径指定人工 reviewer。

<!-- platform-stage: stop-and-recover -->
## 6. 停止与恢复

scheme/destination 未知、缺 Xcode/CocoaPods、签名未解决、生成物脏、只在 CI 存在的 secret 时停止。向 owner 收集证据，更新 Candidate 后重跑同一检查，不得降级。

<!-- platform-stage: verify-platform-adoption -->
## 7. 验证 iOS 采用

十阶段校准、仓库证据命令、local/hosted 分离结果、人工审核 PR 与 lifecycle closure
全部完成才算成功。AI Cockpit 的最小 SPM fixture 不能证明采用方 Xcode app。
