---
author: Ray
title: "AI Cockpit"
description: 面向 Codex、Gemini、Claude、Cursor、Antigravity 等 AI 编码代理、与目标应用语言无关的协作式工程环境与变更治理模板。
keywords:
  - ai-agents
  - ai-agent
  - ai-workflow
  - code-review
  - llmops
  - ai-safety
  - codex
  - gemini
  - claude
  - cursor
  - antigravity
  - agentic-coding
  - developer-tools
  - developer-workflow
  - governance
  - template
  - automation
  - ci
---

# AI Cockpit

质量门禁责任、计时证据和工单追踪流程见[质量门禁运行说明](docs/operations/quality-gates.zh-CN.md)。

企业控制边界请参阅[企业控制清单](docs/reference/enterprise-control-checklist.md)和[机器可读状态矩阵](docs/reference/enterprise-control-matrix.json)。仓库内证据不等于外部控制已验证；发布前必须完成 WI-16 日语能力评估。

请从面向初学者的[安装手顺](docs/getting-started/installation.zh-CN.md)开始：它只使用六段短提示词，然后把工程校准交给独立的 Work Item。[30 秒开始](docs/getting-started/30-second-start.zh-CN.md)、[标准采用指南](docs/getting-started/standard-adoption-guide.zh-CN.md)和[安全与发布验证](docs/getting-started/security-release-verification.zh-CN.md)仍提供深入路径。安全负责人可使用[严格安装与供应链验证](docs/getting-started/installation-security.zh-CN.md)；校准和故障排除也各有独立文档。历史计划和归档记录属于证据上下文，不是当前操作指示。

[English](README.md) | [日本語](README.ja.md)

AI Cockpit 的产品边界是 Repository Governance Layer，而不是 Agent Runtime、Workflow Engine 或 Security Sandbox。仓库记录支持评审；可信身份、生产隔离、企业审计/合规和发布平台证据仍由外部控制提供。

AI 编码代理可能会：

- 重写无关文件
- 悄悄删除测试
- 绕过验证
- 让 reviewer 猜不出发生了什么

不应在缺少边界明确、独立执行的 review 时接受 AI 生成的变更。关键不是让人更相信 agent，而是让人能基于证据判断何时可以依赖、调查、人工介入或阻止其工作继续。

**AI Cockpit enables calibrated trust between humans and AI agents through evidence-based governance.**

Calibrated trust（校准信任）不意味着最大化对 agent 的信任，而是让人在证据支持依赖时依赖 agent，在证据缺失、过时、矛盾或不足时进行人工介入。

Runtime 安装不等于校准完成。当前 `configure_ai_cockpit` 主要生成和校验 Project Profile 提案；可暂停恢复的十 Stage 会话与 Candidate 激活已经是实现的 Runtime 能力，但仍需要在对象工程中执行并经人工确认。更新必须先执行 Impact Assessment，再根据结果重新校准。详见 [Capability Truth Matrix](docs/reference/capability-truth-matrix.md)；门禁覆盖的是可声明、可复核的 deterministic known-risk cases，不是所有 semantic risk，也不判断 Agent 的内部状态。

## Why AI Cockpit exists

AI Cockpit 不是业务技能或 Agent Runtime，而是 Human-Agent Trust Layer：使用可复核证据判断智能体何时可以继续、何时必须由人类决策、何时必须停止治理路径。阅读[Human-Agent Trust Layer](docs/trust-layer.zh-CN.md)。

## 交互入口

在 TTY 中无参数执行 `./install.sh`，或使用 `--interactive`，会进入八步
Installation Wizard。它只接受一个数字 mode（`1` New Adoption、`2` Upgrade、
`3` Dry Run），展示写入计划，并在明确确认前不写入；不会 commit、push、创建 PR
或 merge。当前底层 selector 本身不显示这些标签，因此 prompt-first 安装手顺提供
数字对应表与审核上下文；非交互的无参数执行 fail closed，明确的 legacy flags
继续保持其 deterministic 行为。安装后由代理使用已安装的
`make cockpit-calibrate-session ARGS="..."` 进行可暂停/恢复的十阶段校准。
`make cockpit-calibration-wizard` 只存在于模板维护仓库，不会安装到采用方工程。
Unknown 或 stale 证据会阻断，Candidate 激活必须分别得到 Reviewer 和 Owner 确认。

移动端实例是 evidence fixture 与文档场景。Hosted 验证目前只覆盖最小 Swift
Package 和 Android smoke；Xcode project/workspace、CocoaPods、工程特定 Gradle
variant、host JDK 和 instrumented execution 必须由采用方校准，Wizard 不作保证。

## 什么是 AI Cockpit？

**AI Cockpit 是面向 AI 辅助软件开发的代码仓库治理层。** 这是实现上述使命的具体产品边界。

它**不是** Agent Runtime，也**不是** Workflow Engine，更**不是** Security Sandbox。

其哲学是 **Evidence over Self-Declaration（证据优于自我声明）**。其机制是 **Evidence Governance**：AI Cockpit 创建治理记录、评估委派证据，并将两者压缩为 Human Decision State。

AI Cockpit 是写入后的差分治理流程，不是文件系统权限边界或安全沙箱。它通过显式 scope、委派式 checks、review 证据和可审计的任务记录来提供 AI Change Governance。Work Item 的完整流程是：最新远端基线 → 专用分支 → Contract/Preflight → 实现与检查 → Summary/归档 → push → PR → merge → `make ai-close-work-item` → 同步干净基线并清理分支。

AI Cockpit 提供：

- **治理**: Scope 边界、验证需求、策略执行
- **代码仓库上下文**: 显式 intent、约束、架构知识
- **验证**: 针对声明契约的独立变更验证
- **可审计性**: 完整记录变更内容、变更原因、验证方式
- **Intent**: 一级表达——不仅仅是"实现什么"，还有"工作为何存在"

AI Cockpit 不会取代 Claude Code、Codex、Cursor、Gemini CLI 等 agent。Agent 随模型能力持续演进。**治理应保持稳定。**

AI Cockpit governs evidence; it does not replace evidence-producing tools。Native Governance Evidence / Delegated Domain Evidence 的分类与 Release 责任边界见[设计哲学](docs/philosophy/design-philosophy.md)。

![AI Cockpit demo](docs/assets/ai-cockpit-demo.gif)

**AI 改了 37 个文件。Cockpit 阻止了 merge。**

AI Cockpit 让 AI 生成的变更有边界、可审查、可审计。

我反复看到 AI 重写无关文件、回退已完成工作、绕过 review 预期。所以我围绕 scope、checks、summary 和 status 构建了一个治理层，以显式契约作为核心控制机制。

## 30 秒理解

Before：

```text
AI 改了 24 个文件。
没人知道为什么。
测试可能已经消失。
Review 从混乱开始。
```

After：

```text
任务范围已声明。
检查被强制执行。
Summary 已生成。
Cockpit 已更新。
Review 从上下文开始。
```

<!-- install-prerequisites: python3.11,git-initial-commit,curl,gnu-make,posix -->

**前置条件：**支持 POSIX shell 的 Linux、macOS 或 WSL；Python 3.11+；Git、curl 和 GNU Make；以及至少已有一个提交且工作树干净的 Git 仓库。所选 stack 的 formatter、测试运行器、SDK 和构建插件也必须预先安装。

版本历史与能力演进在[路线图](docs/roadmap.md)中维护，而不是放在这个简短入口页中。

## 安装权威公开投影所指向的运行时

初学者先把下面提示词复制给已打开目标工程的代理：

```text
请严格按照完整中文安装手顺为这个工程安装 AI Cockpit。先只读检查前置条件和工程，
逐步解释术语，只使用权威公开固定 release（除非我提供已验证 private mirror）。
每一步必须显示证据、预期结果、PASS/STOP 和应联系的人。写入、commit、push、
准备 PR、人工 merge、lifecycle closure、configuration 必须分别向我确认。
绝不能把后续步骤放进一个连续 shell block 自动执行。
```

以下是**高级手工备用命令**，不是初学者首选。只执行到本地 finish/archive 后停止：

<!-- command-evidence: adopter_required -->
```sh
STACK="${STACK:-generic}" # generic、python、go、rust、typescript、java、android、kotlin、flutter、swift、ruby、php 或 csharp
PUBLIC_REPOSITORY="${AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY:-https://github.com/spirex-ds-dev/ai-cockpit-template.git}"
RAW_BASE="${AI_COCKPIT_TEMPLATE_RAW_BASE:-https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template}"
RELEASE_TAG="$(curl -fsSL "${RAW_BASE}/main/release.json" | python3 -c 'import json,sys; value=json.load(sys.stdin)["releaseTag"]; assert isinstance(value,str) and value; print(value)')"
INSTALLER="$(mktemp)"
trap 'rm -f "$INSTALLER"' EXIT
curl -fsSL "${RAW_BASE}/${RELEASE_TAG}/install.sh" -o "$INSTALLER"
AI_COCKPIT_TEMPLATE_REPO="$PUBLIC_REPOSITORY" \
  AI_COCKPIT_TEMPLATE_REF="$RELEASE_TAG" sh "$INSTALLER" --stack "$STACK" --update-makefile --create-adoption
make ai-finish TASK=adopt_ai_cockpit
```

停止并审核 archive/diff。另行取得人工 commit 批准后：

<!-- command-evidence: adopter_required -->
```sh
ADOPTION_CONTRACT="$(python3 -c 'import json; entries=[item for item in json.load(open(".ai/work-items/archive/index.json"))["entries"] if item["workItemId"]=="adopt_ai_cockpit"]; assert len(entries)==1; print(entries[0]["contractPath"])')"
ADOPTION_BASE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["baseCommit"])' "$ADOPTION_CONTRACT")"
git add .
git commit -m "adopt AI Cockpit governance"
make check-ai-pr AI_BASE_COMMIT="$ADOPTION_BASE"
```

停止。另行批准 push、创建 PR、通过 hosted CI，并由人 merge。再次取得 lifecycle
closure 批准后，才单独执行：

<!-- command-evidence: adopter_required -->
```sh
make ai-close-work-item TASK=adopt_ai_cockpit
```

closure 同步默认分支以后，另行开始 configuration：

<!-- command-evidence: adopter_required -->
```sh
CONFIG_BASE="$(git rev-parse HEAD)"
make ai-start TASK=configure_ai_cockpit TITLE="Configure AI Cockpit for this project" MODE=code
```

对于对象工程，完成本地 finish/archive 后必须先人工允许 `git commit`，再单独人工允许 `git push`。PR 可以由工具准备，但合并必须人工完成。PR 手动合并后，还必须再次人工允许 `make ai-close-work-item TASK=<task>`；不得启用自动合并或自动删除分支。该保守门禁只适用于安装和升级的对象工程，模版工程自身维护流程保持不变。

该命令强制读取权威公开 `release.json` 投影，并只下载其中固定 tag 的安装器。投影不可访问或无效时立即停止，绝不从最高 tag 猜测版本。将其视为已验证公开版本前，还必须同时确认平台 Release 稳定且非 draft、tag 固定 metadata 与 source commit 一致、installer 和 archive asset 可下载、digest 全部一致。单独的 tag 或仓库内 `release.json` 都不构成平台发布证据。公开版本的能力可能落后于源码树；创建首次采用 PR 前请先阅读[完整中文安装手顺](docs/getting-started/installation.zh-CN.md)。
如果发布元数据或标签并非公开可访问，就不要把这条快速安装流程当成匿名安装路径。`AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY` 和 `AI_COCKPIT_TEMPLATE_RAW_BASE` 只用于解析 release tag 和获取安装器，而安装器本身仍会通过 `AI_COCKPIT_TEMPLATE_REPO` 和 `AI_COCKPIT_TEMPLATE_SOURCE` 选择 clone / source。此时应改用本地克隆或显式配置的源码来源。

先审阅并扩展生成的配置 Contract scope，再修改 Project Profile、Guard、质量命令和 CI。然后在启用阻断型门禁前，根据目标工程校准治理运行时：

<!-- governance-flow: install,configure-work-item,onboard,doctor,calibrate,confirm,validate,readiness,develop -->

```sh
make ai-onboard
# 或分步执行:
make cockpit-doctor
make cockpit-calibrate
# 审阅 .ai/project_profile.proposed.yaml，再创建并批准 .ai/project_profile.yaml。
make check-ai-project-profile
make check-ai-guard-calibration
make check-ai-adoption-ready
make ai-finish TASK=configure_ai_cockpit
```

停止并审核 configuration archive/diff。另行批准 commit 后：

<!-- command-evidence: adopter_required -->
```sh
git add .
git commit -m "configure AI Cockpit for this project"
make check-ai-pr AI_BASE_COMMIT="$CONFIG_BASE"
```

Doctor 不修改项目策略，只记录检测事实、证据、置信度、建议和 unknown。Calibration 只生成候选文件，不覆盖 Guard，也不自动批准高风险路径。人工明确确认且 Readiness 检查通过后，再启动受治理的 AI 任务：

```sh
make ai-start TASK=example_change TITLE="Example change" MODE=code
```

带检查和审计记录完成它：

```sh
make ai-finish TASK=example_change
```

## 工作方式

完整的治理闭环是 **Intent → Contract → Implementation → Verification → Summary → Cockpit → Human Decision**。下方的简短生命周期描述的是操作顺序，而不是对这套架构闭环的替代。

```text
Plan -> Scope -> Verify -> Summarize -> Status -> Archive
```

| 层 | 作用 |
| --- | --- |
| Work Item Contract | 在 AI 修改文件前声明任务边界。 |
| Scope Guard | 检测超出声明 scope 的变更，并阻止完成、归档或合并门禁通过。 |
| Backtrack Guard | 检测受保护测试、snapshot 或 Work Item 记录的删除，并阻止已配置门禁通过。 |
| Coverage Guard | 要求每个生产代码路径都有由项目关联规则匹配的测试路径变更；它不分析测试内容，也不证明运行时覆盖率。 |
| Agent Risk Guard | 针对「prompt 仅是建议」、「mid-task 漂移」和「过度声明」风险的硬门控。 |
| AI Review Policy | 标记需要在 Change Summary 中明确说明 review 重点的治理和 CI 变更（仅报告）。 |
| Checkpoint | Mid-task 完整性快照，用于在完成前检测 scope 漂移。 |
| Status Consistency Guard | 验证 Cockpit 状态与当前 active Work Item 集合是否一致。 |
| Change Summary | 记录改了什么、验证了什么、还剩什么风险。 |
| Cockpit Status | 用一个生成视图展示当前 AI 任务状态，并反映 Governance Compression 的结果。 |
| Finish Flow | 只有检查通过后才归档 Work Item。 |

## 信任模型

- `ai-start` 记录 `baseCommit` 和任务开始前脏文件的内容指纹。
- Contract v2 只能引用 `.ai/cockpit/checks.yaml` 中注册的 check ID，不能提供任意命令。
- `ai-finish` 记录 check ID、退出码、执行 commit、Contract hash、command hash 和脱敏输出摘要；这些是结构化记录，不是密码学证明。
- 安装器会分发相同的 PR validator 和 Make target。归档 Work Item 后，CI 运行 `make check-ai-pr AI_BASE_COMMIT=<merge-base>`。
- 每个非豁免 PR 路径必须由同一对 Contract/Summary 同时声明 scope 和 `changedFiles`。
- restricted/destructive approval 是 Contract 内的自声明流程记录；可信人工批准应由 CODEOWNERS、受保护 CI environment 或平台身份事件提供。
- AI Cockpit 用于减少误操作和流程漂移，不是针对恶意代理的安全沙箱。对于上述命令选择的公开版本，项目测试或 `make ai-cockpit-quality` 必须作为独立 required CI check 运行。

## 它会拦住什么

```text
[BLOCKED]
Scope violation detected.

Unauthorized file modification:
- src/auth/payment.rs

Allowed scope:
- src/auth/session.rs
- tests/auth/session_test.rs
```

## 支持

代理：

```text
Codex, Gemini, Claude, Cursor, Antigravity, and other coding agents
```

技术栈：

```text
generic, rust, flutter, typescript, python, go, java, android, kotlin, swift, ruby, php, csharp
```

兼容性等级：

<!-- stack-tiers: verified=python,go,rust,typescript,java,kotlin,ruby,php,csharp,flutter,android,swift; workflow-implemented=; preset-only=generic -->

- **Hosted CI 已验证：** `python`、`go`、`rust`、`typescript` 在 `real-stack-quality` 中运行；`java`、`kotlin`、`ruby`、`php`、`csharp` 在 `extended-real-stack-quality` 中运行；`flutter`、`android`、`swift` 在 `mobile-stack-quality` 中对最小工程执行 `make ai-cockpit-quality`。
- **Swift 验证范围：** 这里只验证一个最小 Swift 软件包，不代表真实 iPhone/iPad 工程、Xcode workspace 或 CocoaPods 依赖已经可用；这些布局必须在安装后完成工程校准。
- **初学者平台手顺：** 从[完整中文安装手顺](docs/getting-started/installation.zh-CN.md)进入 [iOS](docs/getting-started/examples/ios.zh-CN.md)、[Android](docs/getting-started/examples/android.zh-CN.md)或 [Java](docs/getting-started/examples/java.zh-CN.md)实例。发现平台文件只说明“可能是哪种工程”，不能证明开发工具、设备、签名凭据或云端 CI 已工作。
- **仅预设：** `generic` 在完成配置前会按设计失败关闭。
- **不支持的运行环境：** 原生 Windows shell。请使用 WSL 或其他 POSIX 环境。

技术栈预设是可按项目修改的起点，不负责安装依赖。目标项目必须已具备 formatter、测试运行器、SDK 和构建插件；例如 Java 和 Android 预设要求 Gradle Wrapper 与 Spotless 配置，Python 预设要求 Ruff 和 pytest。`examples/` 仅覆盖部分技术栈，目前并未包含每一种预设。

治理运行时本身不依赖目标语言，但技术栈预设和默认 guard 路径并不代表完整的框架支持。将其设为 CI 必需检查前，必须根据目标仓库调整 `Makefile.ai.stack` 和 `.ai/guards/coverage_policy.yaml`。

安装只完成治理运行时部署，并不代表生产适配完成。Project Profile、Guard、质量命令和 CI 适配由独立的 `configure_ai_cockpit` Work Item 覆盖。Adoption Readiness 还要求已批准的 Project Profile、Profile 与 Guard 一致、质量命令非占位、Coverage 路径已确认，并在 CI 中配置 `ai-cockpit-quality` 和 `check-ai-pr`。该检查只验证静态完整性，不是安全证明，也不能证明项目命令本身有效。

<!-- release-capabilities: auditable-adoption,sha256-verification -->
<!-- public-quality-target: ai-cockpit-quality -->

公开发行契约包含可审计的首次采用流程，并要求快速安装同时绑定公开标签、源提交、安装器摘要以及可下载发行归档的 SHA256。任一绑定或归档资产缺失、错误时，快速安装都会失败关闭；调用方提供的 `AI_COCKPIT_TEMPLATE_SHA256` 只是附加断言。项目质量命令、Coverage 路径和 CI 仍需针对目标工程明确适配。

## 运行环境要求

- Python 3.11 或更高版本。
- 具有 merge-base 和 three-dot 差分（`...`）支持的 Git 环境。
- 兼容 POSIX shell 和 GNU Make 的命令执行环境。
- 官方支持 Linux 和 macOS 运行和 CI。原生 Windows shell 暂不支持，请在 WSL (Windows Subsystem for Linux) 或其他 POSIX 终端中运行。

仓库的 `make quality` 会运行全部测试，要求脚本总覆盖率不低于 85.10%，并对生命周期关键脚本设置分文件回归下限；同时对 `scripts/` 和 `tests/` 执行 Ruff，对全部治理脚本执行 Mypy，以精确的已评审 low-risk baseline 和零未登记中高风险 finding 校验 Bandit，并执行 Python 编译、差分检查和文档一致性检查。

## 迁移与兼容性

- `contractVersion: 2` 通过严格的 Check ID 映射机制防止注入风险。
- `.ai/work-items/archive/` 中的历史 `v1` Contract 记录以只读方式被保留和兼容，但全新创建的任务必须使用 `v2` 格式。

## 进阶文档

- [完整中文安装手顺](docs/getting-started/installation.zh-CN.md)
- [概念导读（日文）](docs/overview.ja.md)
- [路线图 (V1〜V4)](docs/roadmap.md)
- [字段说明手册](docs/contract-fields.md)
- [配置](docs/configuration.md)
- [架构](docs/architecture.md)
- [设计思想](docs/design-philosophy.md)
- [案例：AI rollback corruption](docs/case-study-ai-rollback-corruption.md)
- [语言 examples](examples/)
已知风险 Guard 只对明确声明的危险模式提供确定性覆盖；有限回归测试不等于能够识别所有未知语义风险。工单必须经过 Contract/Preflight、实现与检查、Summary/归档、PR、合并和分支清理的完整生命周期。
