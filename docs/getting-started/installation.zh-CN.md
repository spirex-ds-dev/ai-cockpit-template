---
author: Ray
title: "安装"
description: 面向零编程经验用户、以提示词为主的 AI Cockpit 完整安装与采用手顺。
keywords:
  - ai-cockpit
  - 安装
  - 初学者
  - 提示词
  - ai-agents
---

# 安装

这是完整的中文手顺，不是英文版摘要。你不需要编程经验。AI 编程代理可以检查和准备工作，但决定权始终在你手中。复制治理 Runtime、完成工程校准、创建第一个 PR、确认托管 CI、合并和完整 lifecycle closure，是相互独立的步骤；清理分支只是 closure 的一部分。

下文常用词的日常含义：

- **Runtime：**复制到工程中的治理文件与工具。
- **Calibration（校准）：**让通用规则适合当前工程。
- **Hosted CI（托管 CI）：**由 Git 服务商在你的电脑以外执行的检查。
- **Lifecycle closure（完整关闭）：**归档证据、核实已合并 PR、同步 base、清理分支。
- **Work Item（工单）：**一组独立受治理的工作、计划与证据。
- **Session（会话记录）：**持久化的校准回答记录。
- **Candidate（候选配置）：**尚未激活的配置提案。
- **Evidence / Owner / Reviewer：**证据、承担责任的人、独立检查的人。
- **Full self-check（完整自检）：**确认十项回答和 required checks 是否齐全。
- **SHA-256 / digest（摘要）：**用于发现内容变化的数字指纹。
- **Phase record（阶段记录）：**表示 Reviewer 或 Owner 已确认的 Session 记录。
- **Active configuration（当前配置）：**现在实际生效的配置。
- **Governance Simulation（治理模拟）：**激活前安全模拟 proposed rules 如何工作。

当前能力以 [Capability Truth Matrix](../reference/capability-truth-matrix.md)
为准。只想快速开始时阅读 [30 秒开始](30-second-start.zh-CN.md)；需要确认安全与发布证据时阅读[安全与发布验证](security-release-verification.zh-CN.md)。

<!-- prompt-safety: read-only-discovery -->
<!-- prompt-safety: explain-evidence-unknowns -->
<!-- prompt-safety: plan-before-write -->
<!-- prompt-safety: human-confirmation-before-write -->
<!-- prompt-safety: no-downstream-authority -->
<!-- prompt-safety: preserve-user-changes -->

## 如何使用本手顺

每个编号步骤都按相同方式进行：把提示词复制给已经打开工程的代理；等待“预期结果”；结果不一致或出现 Unknown 时停止；只批准当前一步，不一次批准后续所有步骤。

“仓库”是由 Git 管理的工程目录；“工作区”是当前看到的文件；“PR”是让人审核拟议修改的页面。遇到不懂的词，要求代理先用日常语言解释。

<!-- novice-stage: before-you-start -->
## 1. 开始前

准备：电脑上的目标工程、能读取该目录的 AI 编程代理、Git、Python 3.10
以上、GNU Make、至少一个已有 Git commit，以及创建分支和 PR 的权限。
不要误装到 AI Cockpit 模板仓库。先备份无法替代的本地资料。

Git 保存工程修改历史；commit 是一次经过确认的历史快照；Python 和 GNU Make
用于执行 AI Cockpit 本地检查。不知道是否已安装也没关系，暂时不要自己安装，
复制下面提示词：

```text
安装 AI Cockpit 前，请只读识别本机操作系统，并检查目标工程目录、代理访问权限、
Git、Python 版本、GNU Make、curl、初始 Git commit、branch/PR 权限。
每一项用表格说明：日常语言用途、观察到的证据、PASS 或 STOP、缺少时应联系的
人员/团队。不要推荐未经组织批准的工具安装器，也不要修改工程。
```

预期结果：你清楚要治理哪个工程、由谁审核第一个 PR。

<!-- novice-stage: open-your-project -->
## 2. 打开工程

在 AI 编程代理中打开目标工程目录，暂时不要创建文件。

复制：

```text
只显示：当前打开的目录、它是否为一个 Git 仓库的根目录、当前分支，以及已修改/
未跟踪文件数量。不要修改。用日常语言解释每一行。若不是 Git 根目录、误开了
AI Cockpit 模板而不是我的工程、或已有修改无法解释，立即 STOP。能从证据确认
工程负责人时写出负责人，否则写 Unknown。
```

预期结果：代理确认正确的 Git 根目录，并报告零修改，或逐项解释并保留所有已有
修改。目录错误时，打开正确工程后重新执行第 2 步。

<!-- novice-stage: copy-discovery-prompt -->
## 3. 复制只读调查提示词

完整复制下面的文本：

<!-- release-metadata-boundary: provider-discovers-latest-verifiable,tag-pinned-verifies-evidence -->
```text
我想在这个工程安装 AI Cockpit。首先只做只读调查。
除非我提供经过明确验证的 private mirror，否则使用权威公开 source
https://github.com/spirex-ds-dev/ai-cockpit-template.git。按从新到旧顺序检查正式
发布的语义化版本，动态选择 provider release、tag-pinned metadata、installer、
archive asset 与 digest 都完整且相互一致的最高版本。不得写死版本、选择
draft/prerelease，也不得把 moving `main` metadata 当作 digest 权威。如果更新的
正式 release 证据缺失或不一致，逐项列出失败并 STOP；得到我的明确决定后才可选择
较旧但证据完整的 release，禁止静默降级。为本次安装解析出选定 tag 后，读取
https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template/<resolved-tag>/release.json，
并且只用这份 tag-pinned metadata 验证 tag target、source commit、installer
digest、archive asset 和 SHA-256。证据缺失或不一致立即停止。
不要创建、编辑、删除、commit、push、创建或合并 PR，也不要发布。
保留所有与本任务无关的用户修改。

请调查并用没有编程经验的人也能理解的语言说明：
1. 仓库根目录、当前分支、工作区状态，以及是否已有初始 commit；
2. 由 remote HEAD 证明的默认 remote、默认分支和最新 fetch 后的 commit，
   不要假设是 origin 或 main；
3. Python 3.10+、Git、GNU Make 和 curl 是否存在；
4. 检测到的语言、构建系统和最合适的 AI Cockpit stack；
5. 已有的 AGENTS.md、GEMINI.md、CLAUDE.md、Makefile、CI、SECURITY.md、
   CODEOWNERS 和进行中的 .ai Work Item；
6. 有工程文件证据的生成文件、关键路径、测试、覆盖率和质量命令；
7. 所有 Unknown 和仅靠推测的内容。

把结果分成“已观察证据、推断、Unknown”，并解释技术词。如果工作区不干净、
没有初始 commit、缺少工具、无法证明默认分支、或已有 active Work Item，
请停止并给出恢复手顺。否则只提出安装计划，列出每个 Wizard 选项和会修改的
确切文件。得到我明确批准前不要写入。
```

预期结果：只读报告，而不是“修改文件列表”。若代理已经修改文件，立即停止；
只恢复代理能证明由它产生的修改，绝不能丢弃原有用户工作。

如果最新正式 release 验证失败，不要自行改用旧版本。先把失败证据交给 release
owner 审核；只有 owner 审核后才复制下面的限定恢复提示词：

<!-- release-fallback-approval: failed-newer-evidence,owner-review,reverify -->
```text
列出验证失败的较新正式 release、每项失败检查与证据、release owner 的审核记录，
以及本次安装建议使用的较旧 tag。对该 tag 重新执行完整的 provider、tag-pinned
metadata、installer、archive 与 digest 验证。全部通过后，只问一个 yes/no：
是否仅批准本次安装使用这个已验证的较旧 tag。不得写入、安装或扩张为其他权限。
```

<!-- novice-stage: review-read-only-report -->
## 4. 逐项确认只读报告

确认：目录正确；已有修改全部被理解并保留；存在初始 commit；默认 remote/分支来自证据而不是猜测；Python 版本和工具满足要求；stack 符合工程；Unknown 没有被隐藏。

复制：

```text
请在完全只读的前提下，逐项带我审核上面七项。每项显示：日常含义、确切观察证据、
PASS 或 STOP、STOP 时应联系的人/团队。询问我是否理解当前项，等待回答后才显示
下一项。不得隐藏 Unknown，也不得开始安装。
```

下面只是用于直接查看工作区证据的**高级手工备用命令**，只能在正确仓库根目录运行。

用途：显示已修改和未跟踪文件。成功：没有输出，或只显示你理解的已有修改。失败时：不要安装，让代理逐行解释并保护这些文件。

<!-- command-guide: purpose,success,failure -->
<!-- command-evidence: adopter_required -->
```sh
git status --short
```

<!-- novice-stage: choose-wizard-options -->
## 5. 审核 Wizard mode 与 installer 默认值

当前 interactive Wizard 只让人选择 New Adoption、Upgrade 或 Dry Run。stack 和
base/branch 由证据检测；其余项目是固定默认值或 CLI/environment 控制，不是额外画面。

| 类型 | 项目 | 通常行为 |
| --- | --- | --- |
| 可选择 | Mode | 未安装过选 **New Adoption**；已有安装才选 **Upgrade**；只预览选 **Dry Run**。 |
| 启动证据 | Source | 使用第 3 步动态选择的最高可验证正式 release；解析出的 tag 只在本次安装期间保持不变。local clone/private mirror 是明确的非公开信任路径。 |
| 自动检测 | Stack | Wizard 目前只根据 Python、Swift、Android 信号自动检测；无信号或混合布局会用 `generic`。`--stack` 是脚本方式的控制项，不是 Wizard 问题。 |
| 自动检测 | Base/branch | installer 从 remote/default-branch 证据推导；New Adoption 的 `--create-adoption` 创建专用分支。 |
| 固定默认 | Make 接入 | Wizard 默认关闭（`update_makefile=false`）；脚本安装使用 `--update-makefile` 前必须审核冲突。 |
| 固定默认 | Examples | 默认关闭（`with_examples=false`）；examples 不能证明工程 stack 可工作。 |
| 固定默认 | 替换 Glossary | 默认关闭（`replace_glossary=false`）；替换采用方内容前必须明确审核。 |
| 入口方式 | Interactive | `--interactive` 进入计划审核和最终写入确认。 |

先复制下面提示词，不需要自己解释技术选项：

```text
只根据只读报告解释唯一可选择的 Wizard mode，以及下面每个 detected/fixed
default 或 CLI/environment control。输出：可选择/检测/固定/CLI-only、日常含义、
当前值、工程证据、安全建议、STOP 条件。Unknown 不猜；不要启动或写文件。
```

普通行为：New Adoption、使用第 3 步动态选出的最高可验证正式 release（选定 tag
只在本次安装期间保持不变）、检测 stack（否则 `generic`）、专用 adoption branch、
不接入 Make、不安装可选 examples、保留现有
glossary、interactive 计划审核。与已有文件或组织规则冲突时联系仓库 owner。

维护专用选项为 `--upgrade` 和 `--upgrade-with-active`。`--dry-run`
必须保持只读。`AI_COCKPIT_TEMPLATE_REF` 指定明确的 source ref；
`AI_COCKPIT_TEMPLATE_SHA256` 只是附加断言，不能替代已发布元数据。

本文后续只适用于 **New Adoption**。选择 **Upgrade** 时在此停止，并在独立 Work
Item 中使用英文 [Upgrade guide](../reference/upgrade.md)；需要中文说明时先联系
upgrade/repository owner。选择 **Dry Run** 时审核“工作区未改变”的结果和完整计划，
然后停止；只有计划可接受后才返回本表选择 New Adoption。Dry Run 不是安装证据。

<!-- make-entrypoint-boundary: included-makefile-or-explicit-f -->
Wizard 默认不接入 Make。因此下文 `make <target>` 只有在 `include Makefile.ai`
经过单独审核并安装后才成立；否则代理必须使用 `make -f Makefile.ai <target>`。
代理要显示实际使用的入口；初学者无需自行编辑 Makefile 或输入命令。

<!-- make-composite-boundary: integration-required-before-ai-finish -->
单一直接 target 可以使用明确的 `Makefile.ai` 入口。但是，在 `ai-finish` 等复合
lifecycle target 之前，代理必须另行审核并安装 `include Makefile.ai`，因为其子步骤
目前仍调用普通 Make。接入缺失或冲突时，在复合 target 前 STOP，并联系 build/
repository owner。

移动/Java 工程先看同语言实例：[iOS](examples/ios.zh-CN.md)、
[Android](examples/android.zh-CN.md)、[Java](examples/java.zh-CN.md)。

<!-- novice-stage: review-installation-plan -->
## 6. 审核安装计划

<!-- installation-plan-release-binding: resolved-tag,metadata,asset,digest,installer,wizard -->
```text
请在不写入的前提下展示最终安装计划：动态解析出的 stable release tag、
tag-pinned metadata URL、archive asset、已验证 SHA-256、准确 installer 入口和
Wizard 启动方式、fetch 后的 base commit、新分支、stack、所有 installer 选项、
每个新增/修改/保留文件、冲突、回滚行为和写入后检查。说明 installer 使用的 tag
checkout、已验证 installer digest 与单独验证的 archive asset 都绑定同一 release；
不得把 archive 称为 installer 输入。逐项解释为何适合本工程，不能确定的写 Unknown。
最后只询问一个 yes/no：是否允许执行本次脚手架写入和验证。
不要请求 commit、push、PR、merge、release、删除或校准激活权限。
```

预期结果：精确计划和一个有限确认问题。若计划使用移动分支、猜测默认分支、隐藏冲突或把后续权限捆绑在一起，请拒绝。

<!-- novice-stage: approve-scaffold-write -->
## 7. 只批准脚手架写入

计划正确时，只允许执行列出的安装 transaction 和验证。installer 会先检查
marker/冲突，发现并 fetch 默认 base，创建 adoption 分支，写入 managed 文件；
中途失败会回滚部分安装。

预期结果：专用 adoption 分支与验证报告；不得 commit、push、创建 PR、merge 或发布。

批准前逐项看到：目标目录、干净工作区、选定 release 证据、fetch 后默认分支
commit、确切修改文件、冲突、rollback。然后完整复制：

```text
我只批准按已审核计划执行脚手架写入和写入后验证。保留无关用户修改；出现新路径、
冲突、Unknown 或验证失败立即停止。本批准不包含 commit、push、PR、merge、
删除分支、release 或 Calibration activation。写入后展示分类文件/验证报告并等待。
```

<!-- novice-stage: inspect-scaffold -->
## 8. 检查每类脚手架

要求代理输出“类别、路径、新增/修改/保留、用途、验证”表格，逐项检查：

```text
只读检查已安装脚手架。严格依次检查：(1) agent 入口，(2) glossary/policy/
guard/trust/profile，(3) adoption Contract/Summary/start receipt，
(4) scripts 与 Make 接入，(5) Cockpit Status/evidence，(6) CI 接入，
(7) 可选 examples。每类列出预期/实际路径、创建/修改/保留、日常语言用途、
验证结果和冲突恢复。缺必需路径、出现计划外路径、生成记录无效或冲突未解决时
STOP。不得 finish、commit、push 或 calibration。
```

- `AGENTS.md` 与可选 Gemini/Claude/Cursor 入口；
- `.ai/glossary.md`、policy、guard、trust schema、project profile；
- active Contract/Summary 与 start receipt；
- `scripts/`、`Makefile.ai`、`Makefile.ai.stack` 和 Makefile 接入；
- `.ai/cockpit/` 状态与证据；
- 已有 CI 文件与后续 configuration Work Item 必须拥有的 CI 修改；installer 不选择或安装 hosted CI；以及可选 `examples/`。

七类必须逐行检查，每次只复制当前行的请求：

<!-- scaffold-review-table: copy-request,expected,pass,stop -->
| 类别 | 复制给代理 | 应看到 | PASS | STOP 与恢复 |
| --- | --- | --- | --- | --- |
| 1. Agent 入口 | “只显示已安装或保留的 agent 指示文件，并解释哪个 agent 会读取哪个文件。” | `AGENTS.md` 等路径；原工程指示明确标为保留或经审核合并。 | 路径都在计划内，读取者清楚。 | 计划外覆盖或指示冲突；联系仓库 owner 并修改计划。 |
| 2. 治理文件 | “显示 glossary、policy、guard、trust、Project Profile 路径；区分默认值和仍需校准的值。” | 按用途分组的 `.ai/` 文件，不宣称默认值已适合工程。 | 必需文件有效，未校准项明确。 | 文件缺失/无效或无证据的工程结论；重跑验证或联系 owner。 |
| 3. Work Item 记录 | “显示 adoption Contract、Summary、start receipt，并把 scope 对应到每个安装修改。” | 一组 active `adopt_ai_cockpit` 记录。 | scope 覆盖全部且只覆盖 adoption。 | placeholder、记录缺失或范围外路径；先修记录。 |
| 4. Scripts 与 Make | “显示 scripts、`Makefile.ai`、`Makefile.ai.stack` 和经审核的 Makefile 修改，解释每个入口。” | Runtime 文件及 Make 接入开/关证据。 | 验证通过且已有 target 被保留。 | 冲突、无法执行或计划外 Make 修改；按冲突恢复。 |
| 5. Status 与证据 | “只读当前 Cockpit Status/安装证据，不要重新生成；与 active Contract 和实际 diff 比较。” | 现有 `.ai/cockpit/` 与当前 Work Item 并列显示。 | 无 stale、缺失或矛盾。 | 状态不一致；展示重新生成计划，等待独立写入批准。 |
| 6. CI 边界 | “显示保持不变的已有 CI，并列出后续 configuration 要处理的缺口；现在不要改 CI。” | workflow 证据与明确 gap 清单。 | 不声称 installer 已安装或跑通 hosted CI。 | 意外 CI 修改或 required jobs 未知；保留文件并联系 CI owner。 |
| 7. 可选 examples | “说明是否请求 examples、全部路径，以及为何它们不能证明本工程 stack。” | 没有 examples，或只有计划批准的路径。 | 选择与计划一致。 | 未请求文件或能力夸大；只能在修订计划获批后移除。 |

若第 5 行显示 stale，另行复制：

```text
请展示 Cockpit Status 重新生成的精确命令、会修改的文件、预期 diff、验证、rollback、
PASS/STOP 和仓库负责人。不要执行。只询问一个 yes/no：是否只批准本次重新生成。
```

源仓库的 `templates/` 和模板供应链证据不属于采用 payload。文件生成成功不等于校准、工程质量、CI、平台工具或生产准备已完成。

预期结果：每个路径都有解释并由 adoption Work Item 拥有。出现未解释或计划外路径时停止。

### 校准前完整关闭 Adoption Work Item
<!-- lifecycle-order: adoption-close-before-configuration -->

以下决定必须分开，不能一次授权。

**A. 只在本地 finish/归档：**

```text
只完成 adopt_ai_cockpit 的本地 finish。把每条 acceptance 对应到修改文件和验证，
更新 Summary，执行声明的 checks、before_finish 与 ai-finish，展示完整 diff。
不得 commit、push、创建 PR、merge、删除分支、closure 或开始 configuration。
```

PASS：archive、diff 和全部检查记录可见。STOP：检查失败、路径无法解释、acceptance
缺证据或混入用户修改；联系仓库 owner。

**B. 只 commit 已审核 archive：**

```text
我批准一个本地 commit，只包含刚审核的 adopt_ai_cockpit archive bundle。commit 后
显示 commit ID 和干净工作区证据并停止。不得 push、PR、merge、删分支、closure
或 configuration。
```

PASS：只有一个本地 commit，工作区干净且没有未审核路径。STOP：commit 混入未审核
路径或仍有 adoption 修改；联系仓库 owner。

**C. 独立批准 push 与准备 PR：**

```text
我只批准 push adopt_ai_cockpit 分支，并向已证明的默认分支准备 PR。保留 source
branch，禁用 auto-merge/provider 自动删分支，显示 PR 链接、Head SHA、required
hosted checks 后停止。不得 merge 或 closure。
```

PASS：PR 指向正确 base、Head SHA 是刚审核的 commit、required checks 已列出且
source branch 仍保留。STOP：push 被拒、base/Head SHA 错误、required check 缺失
或分支被自动删除；联系 repository/CI owner。

**D. 人工审核与 merge：** 人在 GitHub 查看 **Files changed**、**Conversation**、
**Checks**，required checks 通过后手动 merge。PR 创建不等于已 merge。

<!-- lifecycle-approval: adoption-closure-plan -->
**E1. merge 后只读审核 closure 计划：**

```text
人工已 merge adopt_ai_cockpit PR。只读验证 PR ownership、merged commit、
archive evidence、精确 closure 命令、对象分支和每项验证。不要修改，停止等待决定。
```

PASS：ownership、archive、commit、branch 与计划一致。STOP：任一不一致；把计划和
证据交给仓库 owner。

<!-- lifecycle-approval: adoption-closure-execute -->
**E2. 只批准 closure：**

```text
我只批准按已审核计划关闭 adopt_ai_cockpit。执行 ai-close-work-item，逐项验证远程/
本地 adoption branch 删除、工作区干净、fast-forward-only 同步、本地默认分支等于
remote，然后停止并显示结果。任一步失败都不得报告 closed；显示本地/远程分支的
实际状态并保留剩余证据。若某分支已经不存在，依据已合并 PR Head SHA 与 base
证据提出恢复计划，并联系仓库 owner。不得开始 configuration。
```

预期结果：adoption PR 已由人 merge，`adopt_ai_cockpit` 已关闭，远程/本地分支
已删除，本地默认分支与 remote 一致。此后才能继续。

<!-- novice-stage: complete-calibration -->
## 9. 完成十个校准阶段

adoption PR merge 且 lifecycle closure 验证后，才创建独立的
`configure_ai_cockpit` Work Item。代理使用已安装的 `cockpit-doctor`、
`cockpit-calibrate`、`cockpit-calibrate-session` target。只有已审核 Make 接入
时代理才用普通 `make`，否则使用
`make -f Makefile.ai`。仅模板维护仓库
具有 `make cockpit-calibration-wizard`，采用方安装后不能使用该命令。初学者优先
复制下面提示词，不手工拼接 Session 命令；激活前必须分别得到 Reviewer 与 Owner 确认。

Calibration Session 是 Configuration Work Item 内保存十个阶段回答的记录。代理代你
操作；你不需要输入它的命令或编辑 JSON。

<!-- calibration-answer-types: yes_no,alternative_input,unknown,not_applicable -->
<!-- calibration-yes-no: type=yes_no,values=Y-or-N -->
每个阶段只使用四种回答：**yes/no** 的 machine answer type 是 `yes_no`，
value 必须是 `Y` 或 `N`；
提供正确值的 **alternative input**；
缺乏证据并阻断 readiness 的 **unknown**；附书面理由的 **not applicable**。

<!-- calibration-runtime-boundary: unknown-machine-blocked,confirmations-candidate-bound -->
通俗地说：只要存在 Unknown、过期、不完整或 STOP 证据，工具就会自动停止。
Reviewer 与 Owner 的 phase record 都必须写明已准备 Candidate 的精确 revision 和
SHA-256 digest。

当前实现边界：Session 会保留并机器阻断每一项 Unknown；确认前先准备一个 canonical
Candidate。回答或证据发生变化后，Candidate 和两个 phase record 都会失效；只有两项
记录都匹配当前 Candidate identity 才允许激活。这些 phase record 只把决定绑定到内容，
不会验证人员身份，也不会单独证明角色分离。

```text
从刚同步的默认分支创建 configure_ai_cockpit，并依次引导十个 Calibration 阶段。
每阶段输出：日常语言问题、检查的工程文件、观察证据、推断、Unknown、建议回答
类型/值、Candidate 将修改的文件、PASS/STOP、必须审核的人。回答只允许 `yes_no`、
alternative_input、unknown、附理由的 not_applicable。不得编造质量命令或把缺证据
写成 N/A。每阶段等待我回答。第十阶段后展示完整 Candidate 和 inventory；
activation 前分别等待 Reviewer 与 Owner 确认。不得 commit、push、PR、merge、
release 或 closure。
```

每次暂停的成功标志是你能理解证据/建议，且没有 blocking Unknown；否则回答
“Unknown—停止”，向表中指定的工程/platform owner 索取证据。

<!-- calibration-stage: repository-role -->
1. **仓库角色：** 应用、库、monorepo、模板或其他；说明发布/部署责任。
<!-- calibration-stage: language-and-stack -->
2. **语言与 stack：** manifest、语言版本、构建工具及 preset 选择理由。
<!-- calibration-stage: source-boundaries -->
3. **源码边界：** 维护中的生产源码；排除 vendor、generated、cache、build。
<!-- calibration-stage: test-boundaries -->
4. **测试边界：** 区分 unit、integration、UI/device、fixture 与测试生成物。
<!-- calibration-stage: generated-artifacts -->
5. **生成物：** 路径、生成器、禁止直接编辑或必须重新生成的规则。
<!-- calibration-stage: critical-paths -->
6. **关键路径：** 安全、发布、migration、支付、身份、签名、部署及其 reviewer。
<!-- calibration-stage: quality-commands -->
7. **质量命令：** 只能来自仓库/CI 证据；记录前提和预期，不得编造命令。
<!-- calibration-stage: review-requirements -->
8. **审核要求：** owner、人工 reviewer、保护分支、required hosted checks，以及代理无权决定的动作。
<!-- calibration-stage: risks-and-unknowns -->
9. **风险与 Unknown：** 记录影响、负责人和恢复；不能把缺证据改写成 N/A。
<!-- calibration-stage: adoption-readiness -->
10. **采用准备：** 所有 blocking 事实解决后，另行审核并批准 Project Profile。

逐阶段复制下面对应请求，看到结果后再选择回答：

<!-- calibration-review-table: copy-request,example,pass,stop -->
| 阶段 | 复制请求 | 证据示例与日常含义 | PASS | STOP / 联系谁 |
| --- | --- | --- | --- | --- |
| 1 仓库角色 | “用 release/deploy 文件证明这是应用、库、monorepo、模板或其他，并说明谁负责发布；先不要记录回答。” | release workflow 与 app manifest 可以支持“应用”建议，但还不是最终批准。 | 角色和发布责任人都有证据。 | Unknown；联系仓库 owner。 |
| 2 语言/stack | “列出 manifest、语言版本、build/package tool，解释 preset 为何只是起点和备选项。” | `pom.xml` 暗示 Java/Maven，但不证明所需 JDK 已安装。 | 版本和 preset 适配有证据。 | 混合/特殊布局；联系 platform owner。 |
| 3 源码边界 | “分开列出维护源码与 vendor/generated/cache/build，并解释每个包含/排除。” | `src/main/` 可能是维护源码；只有工程证据确认后，`build/` 才能判定为输出。 | 每条路径有 owner 和理由。 | 可能误排维护代码；联系 module owner。 |
| 4 测试边界 | “区分 unit、integration、UI/device、fixture、测试生成物和所需环境。” | `src/test` 与 `src/androidTest` 是不同证据，不能互相替代。 | 类型/环境清楚。 | owner/环境 Unknown；联系 test/platform owner。 |
| 5 生成物 | “列出生成路径、生成器、source of truth、再生成方法和直接编辑规则。” | 已知 schema 与 generator 时，生成 client 不是 source of truth。 | generator 与 drift 规则有证据。 | 不知如何生成；联系 build owner。 |
| 6 关键路径 | “列出安全、发布、migration、支付、身份、签名、部署及工程特殊高风险路径和 reviewer。” | 即使测试通过，signing workflow 仍可能要求 release owner。 | 每类有人工 reviewer。 | ownership 缺失；联系 security/release owner。 |
| 7 质量命令 | “只从 repo/CI 复制精确命令，逐项说明前提、用途、成功输出和失败处理。” | CI 中的命令只证明该环境使用过此语法，不证明本机 SDK 已安装。 | 每条命令有证据和预期。 | 需要编造或缺前提；联系 build/CI owner。 |
| 8 审核要求 | “显示 CODEOWNERS、branch protection、required hosted checks 和 agent 无权批准的动作。” | CODEOWNERS 提示 reviewer；provider 设置才证明是否强制。 | 人员和 required checks 明确。 | provider 证据不可见；联系 repo admin。 |
| 9 风险/Unknown | “列出所有未决事实、后果、owner、恢复，不得把 Unknown 改成 N/A。” | required device test 缺少 device 时，仍是 blocking Unknown。 | 没有隐藏 blocking Unknown。 | 任一 blocking Unknown；联系表中 owner。 |
| 10 准备状态 | “显示十项回答、proposed configuration、inventory、checks、残余边界以及预定 Reviewer/Owner。先持久化第 10 阶段回答并执行 full self-check；此时不要创建 confirmation phase record，也不要激活。” | 完整 proposed configuration 是可审核证据，不等于批准。 | 第 10 阶段回答已持久化，full self-check 通过，未来 Reviewer 与 Owner 已识别。 | 证据缺失/stale/被拒；退回对应阶段。 |

### 校准完成记录清单

此表是给人看的审核视图。简单说，Session 只保存你的回答、回答类型、理由和阶段
运行状态；Work Item 保存支持证据、proposed change、负责人和 PASS/STOP。持久化
JSON Calibration Session 只对其 schema 实际保存
的回答类型、回答值、理由、阶段状态、events 与 checks 构成权威记录；它不保存清单
中的其他列。其他列只能记录到 schema 支持的 Work Item review、acceptance 或
verification 证据，并同时显示两个位置。若没有合法 schema 字段，必须 STOP 并报告
持久化缺口；不得发明 Summary key 或手工编辑本文档。代理在 review 输出中显示一行
填写副本；只有持久化 Session 确认已记录回答后，才把该行标为完成。只是提出问题
不代表完成。事实或负责人缺失时填写 `unknown` 并选择 STOP。

<!-- calibration-session-persistence-boundary: structured-checklist-evidence,candidate-bound -->

复制下面提示词，你不需要寻找或编辑治理文件：

```text
找到 active configure_ai_cockpit Work Item 及持久化 Calibration Session。使用
下面十行清单作为审核格式。当前阶段只显示一行通俗填写草案：观察证据、回答
type/value/reason、proposed Candidate change、预定 Owner/Reviewer，以及带理由与
重试步骤的 PASS/STOP。先显示准确 Session record 并等待我决定。我决定后，通过
已安装 Calibration Session 接口的 `answer` 保存回答，通过 `record-evidence`
保存其余各列。显示 Session 路径和只读 review 输出，证明 schema 已支持整行记录。
字段缺失、决定为 STOP 或回答为 Unknown 时必须 STOP。不要让我手工编辑 JSON；
不得编造证据、prepare/activate Candidate、commit、push、创建或合并 PR、release
或关闭 Work Item。
```

<!-- calibration-completion-checklist: state,evidence,answer,candidate,owner-reviewer,pass-stop -->
| 显示用阶段标签与检查项 | 完成状态 | 记录观察证据 | 记录回答类型/值 | 记录 Candidate 变化 | 记录 Owner / Reviewer | 记录判定 |
| --- | --- | --- | --- | --- | --- | --- |
| 1. repository-role — 仓库角色与发布责任 | [ ] | 记录检查过的 release/deploy 文件及观察到的角色：___ | 记录 `yes_no`、`alternative_input`、`unknown` 或附理由的 `not_applicable`：___ | 记录 Candidate 角色字段，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 2. language-and-stack — 语言、版本、工具与 preset 适配 | [ ] | 记录 manifest、版本文件及 build/package 证据：___ | 记录回答类型及准确 stack/version 值：___ | 记录 Candidate stack 字段，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 3. source-boundaries — 维护路径与排除路径 | [ ] | 记录检查过的 source、vendor、generated、cache、output 路径：___ | 记录回答类型及准确 include/exclude 值：___ | 记录 Candidate source-boundary diff，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 4. test-boundaries — 测试类型、fixture 与环境 | [ ] | 记录 unit/integration/UI/device/fixture 证据及所需环境：___ | 记录回答类型及准确 test-boundary 值：___ | 记录 Candidate test-boundary diff，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 5. generated-artifacts — 生成器与再生成规则 | [ ] | 记录 generated 路径、source of truth、generator 与再生成证据：___ | 记录回答类型及准确 generator/editing 规则：___ | 记录 Candidate generated-artifact diff，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 6. critical-paths — 高风险路径与人工审核 | [ ] | 记录 security/release/migration/signing/deploy 路径及证据：___ | 记录回答类型及准确 critical-path 值：___ | 记录 Candidate critical-path diff，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 7. quality-commands — 有证据的精确命令与前提 | [ ] | 记录 repo/CI 来源、精确命令、前提及预期结果：___ | 记录回答类型及准确的有证据命令集：___ | 记录 Candidate quality-command diff，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 8. review-requirements — Owner、保护与 hosted checks | [ ] | 记录 CODEOWNERS/provider/CI 证据及不可见的 provider 事实：___ | 记录回答类型及准确审核要求：___ | 记录 Candidate review-policy diff，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 9. risks-and-unknowns — 后果、负责人及恢复 | [ ] | 记录每项风险/Unknown、后果、owner 与恢复证据：___ | 记录回答类型；不得把缺少证据改成 N/A：___ | 记录 Candidate risk/Unknown diff，或写明 `no change` 与理由：___ | Owner：___；Reviewer：___ | 记录 `PASS`—理由；或 `STOP`—缺失证据、Owner 和重试步骤：___ |
| 10. adoption-readiness — Proposed configuration、inventory、checks 与未来决定 | [ ] | 记录最新 proposed-configuration/inventory/check 证据及残余边界：___ | 记录最终回答类型/值，但不要激活：___ | 记录 proposed Candidate change 与 configuration 标识：___ | 预定 Owner：___；预定 Reviewer：___；此时不要确认 | 只有回答已持久化且 full self-check 通过后才记录 `PASS`，否则记录 `STOP`；phase record 仅在下一独立步骤创建：___ |

确认前必须闭合脚手架审核留下的每项 CI 缺口：

<!-- calibration-ci-gap-boundary: plan,approval,implementation,verification -->
```text
读取已关闭 adoption Work Item 的 CI 缺口清单。逐项显示工程证据、owner、准确
Candidate diff 或有证据的 no-change 理由、验证、所需 hosted 证据、回滚和
PASS/STOP。需要写入时，只针对这份准确 CI diff 询问一个 yes/no 并等待。批准后
只实施该 diff 并显示本地验证；后续 PR 必须提供同一 commit 的 hosted 证据。
任一 required CI 项仍为 Unknown、未实施或未验证时，不得确认或激活 Calibration。
```

### 单独审核并批准激活

十行全部勾选只表示 Candidate 可审核，不代表已经激活。Session 为每行保存完整的
七列结构化证据，但 `reviewer` 与 `owner` phase 名称仍不证明人员身份。先识别
Reviewer 与 Owner，确认人员/角色外部证据将保存到哪个 Work Item 审核位置，再让
代理依次执行 review、full self-check、Governance Simulation 与
`prepare-candidate`。然后复制下面提示词，分别取得并记录两项决定：

<!-- calibration-confirmation-boundary: phase-records,external-actor-identity -->
```text
不要激活。通过已安装 Calibration Session 接口，显示持久化 Session ID/路径、
prepared Candidate revision、SHA-256 digest、准确 configuration 与十行结构化
checklist evidence。由我先把这份准确审核材料交给已识别 Reviewer，再交回该人员的
明确决定与外部身份凭据；收到前必须等待。随后对已识别 Owner 单独重复。只有收到
本人决定后，才能用刚才显示的准确 revision/digest 记录对应 phase。显示两个
digest-bound phase record，以及 Work Item 中证明人员身份和角色分离的外部证据。
明确 Session 绑定的是决定与 Candidate 内容，不会验证人员身份。决定缺失、过期、
拒绝、digest 不一致或来自同一人时 STOP。
```

再复制下面的只读计划提示词：

<!-- calibration-activation: plan-before-approval -->
```text
先不要激活。显示持久化 Calibration Session ID/路径、prepared Candidate revision
与 SHA-256、准确 configuration、当前 Active configuration、所有结构化 checklist
blocker、full self-check 与 Governance Simulation 结果，以及 Reviewer/Owner
confirmation 中的 revision/digest。显示同一 rollback transaction 将替换的 Active
和 Session 路径、当前标识，以及 Active 失败、Active 替换后 Session 失败或 rollback
失败时的准确恢复行为。每项标为 Observed、Inferred 或 Unknown。最后只问一个
yes/no：证据是否完整，以及是否进入针对这个准确 Candidate identity 的独立激活
批准步骤。明确回答 yes 也不授权激活。不得修改文件、commit、push、创建或合并
PR、release 或关闭 Work Item。
```

PASS 表示两项确认记录都匹配 prepared Candidate revision/digest，configuration
包含十行回答与证据，且没有 Unknown、STOP、stale stage 或缺失字段。runtime 现已
机器执行这些条件；是否批准仍由人审核决定。否则 STOP，返回相应清单行。PASS 后
才复制下面独立的限定批准：

<!-- calibration-activation: bounded-approval -->
```text
我只批准刚刚审核的准确 Calibration Session ID、prepared Candidate revision、
SHA-256 digest 与 configuration 的本次激活。激活前立即重新计算 Candidate digest；
digest 有变化、confirmation 不匹配或仍有 checklist blocker 时 STOP。只能通过已
安装的 Calibration Session transaction 激活。显示激活前后 Active 与 Session
标识、两者持久化的同一 Candidate identity 与验证结果，然后停止。Active 或 Session
任一持久化失败时，核实两条路径都恢复到 transaction 开始前的准确字节或不存在
状态。rollback 失败时报告 STOP 与“consistency unproved”，联系仓库 owner，不得
用较弱证据重试。不得 commit、push、创建或合并 PR、release 或关闭 Work Item。
```

预期结果：prepared 且 digest-bound 的 Candidate 与完整 inventory，没有隐藏
Unknown。Active 与 Session 使用两文件 rollback transaction；这是恢复保证，不是
物理多文件原子性声明。两份记录带有同一 Candidate identity 才算成功。这不会验证
人员身份，也不等于企业合规或 runtime sandbox。

<!-- calibration-activation-atomicity: active-session-rollback-transaction,candidate-digest-bound -->

<!-- novice-stage: run-local-checks -->
## 10. 执行本地检查

readiness 顺序固定为先执行已安装 target `ai-cockpit-quality`，再执行
`check-ai-adoption-ready`。只复制下面这一份提示词：

<!-- public-quality-target: ai-cockpit-quality -->
<!-- readiness-target-order: ai-cockpit-quality,check-ai-adoption-ready -->
```text
先运行已安装 target ai-cockpit-quality，再运行 check-ai-adoption-ready。
如果 Make integration 已单独审核并安装，使用普通 make 入口；否则使用
Makefile.ai 入口。只执行 active Contract 声明的检查。先显示两条准确命令并用日常
语言解释，等待我批准本步骤；批准后再执行，实时显示进度，按实际结果记录
pass/fail/not-run，失败立即停止。不得削弱、跳过或改名 gate；不得 commit、push、
创建 PR、merge 或发布。
```

用途：先跑工程质量，再验证采用证据。成功：两项退出成功且 Summary 如实记录。
失败：保存输出并 STOP，在同一 Work Item 修正配置或工程根因，不得跳过。

<!-- novice-stage: complete-first-work-item -->
## 11. 完成 configuration Work Item

代理只完成 `configure_ai_cockpit`：更新 Summary，执行 `before_finish` checkpoint 与
通过已安装的 `ai-finish` target 并传入当前 task，归档 Contract/Summary，然后展示完整 diff 和检查证据。人工审核后才能批准 archive-evidence commit；批准 commit 不等于批准 push。
如果没有传入 active Contract/Summary，已安装的 `check-ai-status` target 可能显示
`Skipping status check (no active contract/summary provided)`；此时必须用
已安装的 `check-ai-status-consistency` target 验证确实不存在 active 状态。

复制：

```text
只 finish configure_ai_cockpit。把每条 Contract acceptance 与实现/测试证据并列，
执行 before_finish 与 ai-finish，再按 profile、guard、质量命令、CI、archive
evidence 用日常语言展示 diff。等待我决定是否 commit；不得 push 或创建 PR。
```

预期结果：只产生可审核的 configuration archive/diff。出现范围外文件、失败检查或
Unsupported claim 时 STOP，不批准 commit。

审核 diff 后另行复制：

```text
我批准一个本地 commit，只包含已审核的 configure_ai_cockpit archive bundle。
commit 后显示 commit ID 和干净工作区证据并停止。不得 push、PR、merge、删分支
或 closure。
```

PASS：只有一个已审核 configuration commit，工作区干净。STOP：出现未审核文件或
检查失败；联系仓库 owner。

<!-- novice-stage: review-pr-and-hosted-ci -->
## 12. 审核 PR 与托管 CI

另行批准 push 时复制：

```text
只 push configure_ai_cockpit 分支并向已证明的默认分支准备 PR。保留 source branch，
禁用 auto-merge/provider 自动删分支，显示 PR 链接、Head SHA、required hosted
jobs 后停止。不得 merge 或 closure。
```

PASS：base/Head SHA 正确，PR 链接和全部 required jobs 可见。STOP：push 被拒、
base/SHA 错误、required job 缺失或 skipped；联系仓库/CI owner。

PR 指向已发现的默认分支，且保留源分支给 lifecycle closure。确认文件、Contract scope、Summary claim、required Job、Head SHA 与托管日志。local success 不是 hosted success。

只有人工审核与 required hosted checks 都通过时，才由人手动 merge；不要启用自动 merge 或 provider 自动删分支。

在 GitHub 打开 configuration PR 的 **Files changed** 查看 diff，
**Conversation** 看 reviewer 决定，**Checks** 看 required Job 和日志。PR 显示的
Head SHA 必须与证据 commit 一致。复制：

```text
只读解释 configuration PR：把每个文件映射到 Contract scope/Summary，列出全部
required GitHub Job、最终状态和 Head SHA，失败/skip 不得隐藏，给出供人工 merge
判断的 PASS 或 STOP。不得 merge 或删除 branch。
```

<!-- novice-stage: merge-and-close -->
## 13. 合并并关闭 lifecycle

merge 后另行批准通过已安装的 `ai-close-work-item` target 关闭
`configure_ai_cockpit`。closure 必须验证归档证据与 PR 所属关系，fast-forward-only 同步 base，删除远程/本地 configuration 分支，确认工作区干净且本地 base 等于 remote base。任一步失败都不能称为 closed。

<!-- lifecycle-approval: configuration-closure-plan -->
**A. 只读审核：**

```text
人工已 merge configure_ai_cockpit PR。只读验证 PR/archive ownership、merged
commit、精确 closure 命令、对象 branch 和每项验证。不要修改，停止等待决定。
```

PASS：PR/archive/commit/branch/plan 全部一致。STOP：不一致；把证据交给仓库 owner。

<!-- lifecycle-approval: configuration-closure-execute -->
**B. 只批准 closure：**

```text
我只批准按已审核计划关闭 configure_ai_cockpit。执行 ai-close-work-item，逐项验证
远程/本地 configuration branch 删除、工作区干净、fast-forward-only 同步、本地
默认分支等于 remote，然后停止。失败时不得报告 closed；显示本地/远程分支实际状态
与剩余证据。若某分支已经不存在，依据已合并 PR Head SHA 与 base 证据提出恢复计划，
并联系仓库 owner。不得开始新 Work Item。
```


<!-- novice-stage: recover-from-a-stop -->
## 14. 停止后的恢复

| 原因 | 安全恢复 |
| --- | --- |
| 工作区不干净 | 识别并保留所有用户修改；先完成原工作或使用独立 worktree。 |
| 没有初始 commit | 让仓库 owner 创建并审核初始 commit。 |
| 缺少工具 | 联系第 1 步识别的 repository/build 管理员，取得已审核的安装方法，再重跑第 1 步只读调查。 |
| 默认 remote/分支未知 | 检查 provider 与 remote HEAD，不猜。 |
| 已有 active Work Item | 完成/关闭或明确 resume，不并行建立竞争项。 |
| managed 文件冲突 | 展示差异并保留采用方内容，修改计划。 |
| 校准 Unknown | 收集证据或指定负责人，不激活。 |
| local/hosted 失败 | 保留日志、找根因、更新证据并重跑同一检查。 |
| merge 后 closure 失败 | 不得报告 closed。检查本地/远程分支实际状态与 closure 证据；若分支已不存在，经 owner 批准后从已合并 PR Head SHA 恢复。 |

<!-- novice-stage: confirm-installation-success -->
## 15. 最终成功清单

- 选定的最高可验证 release 与 fetch base 已记录；
- adoption/configuration 各自使用独立 Work Item、分支和审核流程；
- 每个脚手架路径和冲突已解释；
- 十个校准阶段与所有 Unknown 已审核；
- 质量命令来自工程证据，并按实际结果记录；
- PR required jobs 对正确 Head SHA 通过；
- 人工完成审核和 merge；
- closure 删除两个工作分支并同步 base；
- Cockpit Status 与归档证据一致；
- 平台、安全和企业边界没有被隐藏。

任一项为否时，只说明当前停在哪一步，不得称安装成功。

## 参考

- [标准采用指南](standard-adoption-guide.zh-CN.md)
- [Calibration Session](../reference/calibration-session.md)
- [采用方配置](adopter-configuration.md)
- [安全与发布验证](security-release-verification.zh-CN.md)
- [文档架构](../reference/documentation-architecture.md)
- [Upgrade（英文权威版本）](../reference/upgrade.md)
