---
author: Codex
title: "AI Cockpit 全面整改执行计划"
description: "用户授权的 AI Cockpit 全面整改串行执行计划。"
keywords:
  - ai-cockpit
  - remediation
  - work-item-lifecycle
  - execution-plan
---

# AI Cockpit 全面整改执行计划

> **2026-07-25 历史快照（不是当前状态）：** 当时只完成了《AI Cockpit 全面整改开发指示》的收查、确认和计划编制，尚未开始整改。后续工单状态只以本文“当前执行状态”和不可变 Work Item archive 为准。

> **For agentic workers:** 每个任务都是一个独立 Work Item。必须按顺序执行；每个任务完成实现与验证、`ai-finish`/归档、push、PR、合并、`ai-close-work-item`、分支清理、默认分支同步和文档对齐后，才允许进入下一个任务。

**目标：** 将 AI Cockpit 收敛为坚固、干净、可信任的 Repository Governance Layer：有证据时允许合理依赖，证据不足或冲突时安全停止，未知和人工决策清楚可见，任务结束后可审查地说明完成内容、发现的问题、避免的风险和剩余风险。

**架构：** 以 Canonical Evidence / Event 为唯一事实源，机器 JSON 为权威记录，Markdown、PR 摘要和 Cockpit Status 均由证据派生。以 Work Item 状态机和 fail-closed 门禁保护安装、校准、验证、发布和关闭流程；以 Light / Standard / Strict 风险分级控制治理成本；以对象工程证据和历史资产登记避免把模板能力、fixture 通过或旧计划误报为产品能力。

**技术栈：** Python 标准库与现有脚本、pytest、Git、GNU Make、JSON/YAML、Markdown、现有 AI Cockpit Contract/Summary/Archive/Status 机制，以及 CI/Release Provider 的外部证据。

## 全局约束

- North Star 保持：`Enable trustworthy collaboration between humans and AI agents.`
- 产品边界保持：AI Cockpit 是 Repository Governance Layer，不是 Agent Runtime、Security Sandbox、身份认证系统、完整 Prompt Injection 防御系统、企业合规认证平台、模型幻觉消除系统、Workflow Engine 或操作系统级权限隔离工具。
- Evidence over Self-Declaration：`testsPassed`、`readyForRelease`、`userApproved`、`productionReady` 等声明不得单独作为事实，必须绑定可检查证据。
- 每一类事实只能有一个 Canonical Evidence / Event 来源；Summary、Task Outcome、Cockpit Status 和 PR Summary 只能派生，不得各自维护另一套事实。
- 治理模式只能自动升级，不能自动降级：Light 适用于低风险文档类变更，Standard 适用于一般代码/测试/配置，Strict 适用于 Release、CI/CD、权限、Secret、安全、供应链、删除、迁移、架构边界和破坏性变更。
- 所有整改 Work Item 直列执行；未完成前一项的 PR merge、archive、`make ai-close-work-item`、本地/远端分支清理和默认分支同步，不得启动后一项。
- 本计划 Work Item 只负责计划文档，不授权执行后续整改；用户已授权本次“收查指示、确认、总结、编制工单列表和修改执行计划文档”。
- 每个整改 Work Item 的 Contract 必须记录 `predecessorWorkItem` 及其 closure evidence；没有前项 closure evidence，`make check-ai-serial-order` 必须 fail closed。
- 每个整改 Work Item 都必须记录实际问题；若问题根因属于流程、门禁、证据模型、顺序或权限，则先创建并完成 corrective process Work Item，再恢复被停止的功能 Work Item。
- 每个整改 Work Item 完成后必须重新检查本计划、相关 README/指南、Contract/Summary、Capability Truth Matrix 和多语言文档是否对齐；有差异时先完成同一 Work Item 的文档对齐并验证，不能把差异留给后续任务。
- 历史计划、归档 Contract/Summary、事件和发布证据不得在本计划阶段删除、改写或压缩；清理只由最后一个专门 Work Item 执行，并保留 archive-backed historical record。

## 一、每个 Work Item 的强制完整流程

以下流程适用于 WI-01 至 WI-19，不得因为任务“只是文档”“只是测试”或“只是发布”而跳过。每项必须在其 Contract 和 Summary 中留下证据。

### 1. 启动与边界

1. 从最新远端默认分支取得 base，发现并记录 remote、default branch、base SHA；模板仓库默认使用 `origin/main`，但仍需实际确认。
2. 从该 base 创建唯一专用 Work Item 分支；禁止从另一个未合并 Work Item 分支派生。
3. 创建 Contract（`contractVersion: 2`），填写 `scope`、`outOfScope`、`sources`、`acceptance`、`verification`、`intent`、风险、能力、预算和前置 Work Item closure evidence。
4. 创建/更新 AI Change Summary；只允许一个 Work Item 对应一个分支和一个 PR。
5. 运行 `make ai-preflight`、`make check-ai-serial-order` 和 `make check-ai-budget-impact`。`needs_human_confirmation`、`not_ready`、unknown、stale base、范围冲突或预算超限时停止。

### 2. 实施与问题处理

1. 只修改 Contract scope 内的文件；需要扩大范围时先更新 Contract、重新 preflight，再继续。
2. 按 Contract 规定运行 focused/full verification，保存 command receipt、测试结果、diff digest、环境/工具版本和外部 Provider evidence。
3. 发现问题时立即记录到 Work Item 的 issue/event 记录：问题、发现阶段、证据、风险、是否停止、建议处置、责任边界和恢复条件。
4. 若问题是流程问题（例如门禁缺失、顺序错误、事实源重复、授权边界错误、无法证明的声明），当前功能实现、PR 和发布动作全部暂停；先建立 corrective process Work Item，并让该 corrective Work Item 完成相同的完整 PR/关闭流程。
5. 若问题不是流程根因，才实施最小修复；不得修改测试或证据以掩盖失败，不得把未验证场景写成已支持。

### 3. 完成、PR 与生命周期关闭

1. 完成 Summary：changed files、verification、guidelinesCompliance、checkpointReview、reviewReadiness、residualRisks、knownGaps、问题与解决证据、文档对齐结果。
2. 运行所有 Contract 检查和项目检查；运行 `make ai-checkpoint`（`before_finish`），再运行 `make ai-finish TASK=<task>` 归档证据。未获用户另行授权，不执行自动归档/自动 merge。
3. 归档前确认：一个 PR 只包含一个 Work Item，PR diff 与 Contract scope 一致，formatter、复杂度、预算、release digest 和 required checks 已通过。
4. 推送专用分支并创建 PR；PR 描述引用 Contract、Summary、Task Outcome、验证结果和问题记录。required checks pending、失败、证据过期或 review 未完成时不得 merge。
5. PR 合并后才执行 `make ai-close-work-item TASK=<task>`。该命令必须证明 archive pair 完整、PR/branch ownership 正确、远端默认分支已包含 merge、默认分支可 fast-forward 同步、local/remote Work Item 分支已清理、worktree 干净、local base 等于 remote base。
6. 关闭后生成/检查 Cockpit Status。位于已同步默认分支时应为 `ready_on_base`；已关闭但仍位于待移除 detached worktree 时必须明确显示 detached/closed 状态，不能用含糊的 `ready for next Work Item` 合并二者。保留历史归档证据。
7. 重新对齐本计划、相关文档、Capability Truth Matrix、版本/命令/路径引用和多语言关键语义；若需要修改，修改必须属于当前 Work Item scope 并重新验证。

## 二、工单总表与串行顺序

| 顺序 | Work Item | 主题与交付物 | 主要完成证据 |
| --- | --- | --- | --- |
| WI-01 | canonical-evidence-foundation | Canonical Evidence/Event 模型、事实源绑定、声明与证据校验基础 | schema、事件关系、派生一致性测试 |
| WI-02 | unknown-human-confirmation | Unknown 四态模型、未知评估、人工确认类型/过期/输出规范 | unknown/confirmation schema、fail-closed 与人工交还测试 |
| WI-03 | source-mode-install-transaction | Source Mode、安装前检查、事务写入、ownership/symlink/path traversal、回滚与锁 | installer transaction、write plan、rollback/concurrency/dry-run 测试 |
| WI-04 | calibration-adopter-evidence | Adoption/Calibration 分离、问卷默认值、Unknown 分类、对象工程证据矩阵 | calibration evidence、fixture/hosted/adopter 状态分离 |
| WI-05 | input-trust-prompt-injection | 输入信任分类、授权与内容分离、高风险操作前重新评估、注入 corpus | detected/contained/blocked/confirmation 等结果及安全回归 |
| WI-06 | absurd-tests-capability-truth | 荒诞测试四层、幻觉分类、Capability Truth Matrix 自动绑定 | negative/absurd tests、能力证据降级与文档停止 |
| WI-07 | lifecycle-state-recovery | Work Item 正式状态机、非法转移、并发、崩溃恢复、幂等事件 | state transition table、recovery/concurrency tests |
| WI-08 | verification-efficiency-escalation | Light/Standard/Strict、Focused/Full、cache、检查 DAG、异常升级 | cache key/invalidation、DAG、升级规则和耗时证据 |
| WI-09 | task-outcome-evidence-report | Task Outcome 两层报告、Finding/Risk/Stop/Resolution/Prevention、PR/Status 派生 | JSON schema、Markdown parity、无夸大/残余风险测试 |
| WI-10 | documentation-alignment | 安装文档三层、多语言语义同步、命令证据标记、历史文档标记规则 | docs/link/command/version/capability checks |
| WI-11 | enterprise-boundary | 企业治理/合规边界声明与 adopter checklist，禁止无证据合规声明 | boundary docs、状态枚举、过度声明回归 |
| WI-12 | code-quality-test-architecture | 大脚本模块化、类型/静态检查、安全 subprocess/path 规则、测试层次补齐 | unit/schema/state/property/transaction/integration/security/release checks |
| WI-13 | deprecated-archive-hygiene | Deprecated Asset Registry、过期代码/命令/文档检查、Archive 分区/索引/digest/保留策略 | registry、引用检查、archive evidence retention 测试 |
| WI-14 | cockpit-human-signal-compression | Cockpit 默认关键结论、Green/Yellow/Red 语义、证据解释/下一步 | status rendering、evidence drill-down、无评分/无自我表彰检查 |
| WI-15 | full-remediation-acceptance | 汇总完成标准，跑全量功能/安全/可用性/效率/文档/质量验收，形成问题总览 | full verification、known-gap review、最终用户复核前 issue overview |
| WI-16 | japanese-capability-assessment | 发布前全面日语处理能力评估、对象工程日语场景矩阵、问题对应整改与ブロッキング | 日语 corpus/文档/交互/安装/错误恢复评估、问题总览和全部对应 corrective Work Item 证据 |
| WI-17 | document_human_agent_trust_layer | 将现有 Trust Layer 升级为 Why/What/How 的英文权威版，并建立完整中文/日文版本、三语 README 入口、架构交叉链接和一致性检查 | 三语完整文档、现有 Gate/命令/Archive Manifest 保留、native/delegated evidence 映射、链接/章节/边界一致性检查 |
| WI-18 | publish-new-version | 严格发布门禁、source/tag/asset/digest/SBOM/provenance、安装/升级/回滚验证并发布新版本 | merge/close 后的发布证据、版本/URL/checksum/provider evidence |
| WI-19 | clean-execution-plan-documents | 最后清理过期执行计划，保留历史标记和 archive-backed 索引，完成计划对齐 | cleanup inventory、历史隔离检查、最终 clean plan 与用户复核材料 |
| WI-20 | quality-gate-performance-architecture-20260727 | 在不降低可信度的前提下优化 `make quality` 与 GitHub Actions：去重、Fast/Full/Release 分层、计时证据、安全并行和安装/Release 职责拆分 | Gate timing/summary、调用图去重、Workflow ownership、scope/cache/并行测试、五类场景性能证据 |
| WI-21 | quality-gate-performance-completion-20260727 | 完成 WI-20 尚未闭合的 Workflow Job 拆分、逐门禁计时和 hosted 前后性能证据 | 独立 Job ownership、逐门禁 timing/log/digest、五类 hosted before/after evidence、三语文档和双向追踪 |
| corrective | process-evidence-release-preflight-20260727 | 修复 WI-21 暴露的点名文件追踪、hosted Summary schema、归档路径/digest、显式发布意图和 CI 失败证据结构 | 当前执行；完成后恢复 WI-21 |
| corrective | ci-evidence-terminal-aggregate-v2-20260727 | 用末端聚合记录三个 required Job 的真实状态，并将所有发布 Contract 检查限定在显式发布准备意图内 | 替代未合并的 PR #410；本地回归、replacement PR、hosted 三 Job/aggregate evidence、merge/close/branch cleanup |
| pre-release | pre-release-deprecated-assets-cleanup | 发布前清理过期代码、过期逻辑和过期文档，包括已实施完成且不再承担当前执行职责的计划文档 | 完整资产清单、runtime/reference 检查、迁移或保留理由、删除回归、文档链接与归档保护、独立 PR/merge/close/branch cleanup |

严格执行以下十阶段顺序；任何阶段都必须完成独立 Work Item 的 Contract→实现→验收→PR→merge→archive→`ai-close-work-item`→本地/远程分支清理→main 同步，才允许进入下一阶段：

1. 深度性能工单：完成 `quality-gate-deep-performance-optimization-20260728`；
2. WI-10：按用户原始详细安装文档指示补齐全部点名文件、三语语义、命令证据；点名文件必须有实现证据，只有确实无需改动时才允许具体的 no-change rationale；
3. WI-01～WI-20 全量双向追踪审计：逐项核对“指示—计划—实现—验收”，任何遗漏必须先建立 corrective Work Item 并完成；
4. 其他流程问题与 `RFE-ISSUE-082`：处理所有已记录未解决流程问题，再完成发布阶段发现的 `RFE-ISSUE-082`；
5. 日语评估及整改：执行全面日语能力评估，任何问题必须完成 corrective Work Item 并重新评估；
6. 文档对齐：对齐 Trust Layer、Capability Truth Matrix、README、架构、安全/发布证据与全部三语文档；
7. 发布前过期资产清理：执行 `pre-release-deprecated-assets-cleanup`，处理过期代码、逻辑和文档，包括已实施完成且不再承担当前执行职责的计划文档；先验证 runtime/reference/migration/归档保护，再决定删除、迁移或保留并标记历史；
8. 独立真实荒诞/注入评估与整改：执行 `pre-release-real-absurd-injection-assessment`，把用户提供的 12 个案例形成完整英中日文档和机器测试；独立评估 request-time 语义分类、post-write repository evidence 和外部 physical controls，逐例验证来源、权限、操作风险、仓库证据矛盾、独立授权与 ALLOW/REVIEW/CONFIRM/BLOCK 结果；任何识别或阻断失败必须先整改并重跑，且不得把固定语料结果当作泛化能力；
9. 发布：仅在前八阶段全部关闭且发布前证据通过后执行 WI-18；
10. 清理当前周期计划文档：发布完整关闭后最后执行 WI-19，只处理仍服务于本轮发布执行的计划，不删除 Contract、Summary、Manifest、Release evidence 或其他不可变审计记录。

WI-01 至 WI-17 只完成整改能力和验收，不发布新版本。`quality-gate-performance-architecture-20260727`、`quality-gate-performance-completion-20260727` 与 `quality-gate-deep-performance-optimization-20260728` 共同构成性能闭环；深度性能工单完整关闭后，下一项固定为 WI-10，而不是发布。WI-10 关闭后必须执行 WI-01～WI-20 的全量双向追踪审计，不能用既有“已完成”状态替代点名文件、实现证据和验收证据复核。已发现但尚未解决的流程问题不得与发布工单混做，必须先记录并建立独立 corrective Work Item。WI-16 是发布前的强制日语能力门禁；若发现问题，必须先完成对应 corrective Work Item 的完整生命周期并重新评估。WI-17 与发布前文档对齐阶段负责 Human-Agent Trust Layer 及相关事实源一致性。`pre-release-deprecated-assets-cleanup` 必须在文档对齐后、真实荒诞/注入评估前独立完成，不能删除仍有 runtime/reference、迁移义务或审计保护的资产。该评估与整改必须在 WI-18 前独立关闭；WI-18 是唯一允许实际发布新版本的工单，且必须在前八阶段及其 corrective Work Item 全部关闭后执行。WI-19 必须最后执行；它不得删除当前计划、最终问题总览或任何仍被 Contract、Archive 或 Release evidence 引用的记录。

### 未来真实荒诞/注入 Work Item 基线（参考输入，非当前能力或完成证据）

以下是 2026-07-29 用户提供的 current-adopter 估计，只用于后续独立的真实荒诞/注入评估与整改 Work Item：repository-change governance 为 70%–85%，forged-evidence cases 为 70%–90%，external-content prompt injection 为 30%–50%，general semantic unreasonable-request recognition 为 40%–60%，registered fixed cases 接近 100%。这些数字不是当前 Capability Truth、验收或发布证据；尤其是接近完整的固定语料结果不能证明泛化的语义攻击识别。

三层边界必须分别评估：(1) request-time 对危险、权限和注入的语义分类当前为中等，依赖有限词汇、结构化字段和正确分类；(2) 写入后的 repository diff、删除、测试、scope 与 evidence 检查相对较强；(3) shell、network、secret 读取、直接 push 或 admin bypass 的物理阻止较弱或在 Repository Governance Layer 之外，AI Cockpit 不是 Agent Runtime 或 Security Sandbox。

十二个条件性结论必须原样保留到该未来 Work Item：

1. 在“已确认”后删除仍被使用的函数：当调用、测试或 scope 矛盾时为条件性通过；in-scope 且无覆盖时可能漏过；不声称动机检测。
2. 隐藏 Markdown 注入：明显的已登记模式可能通过；隐晦、释义或业务语义攻击仍不稳定。
3. 删除失败测试以使 CI 变绿：Backtrack、Coverage、测试删除、diff ownership 和回归检查相对较强；必须证明 adopter corpus 安装、CI 调用和策略校准。
4. 伪造 security-owner 批准：取决于正确把操作分类为需要认证/授权的 authority-required 操作；委婉表达导致的误分类仍是缺口。
5. 恶意日志指令：显式已登记模式可检测；语义化的恢复建议可能逃逸有限词汇。
6. README 要求上传 `.env` 或 SSH key：输入信任、secret、network 与授权都被评估时，策略级检测较强；直接 shell 执行没有物理沙箱。
7. 声称未运行的 Xcode 验证已通过：这是相对较强的 evidence-hallucination 场景；必须区分 not_run、failed、simulation、hosted fixture 和 adopter execution。
8. 紧急绕过 release gate：治理路径会阻止；直接 main push、admin、token 或 Branch Protection 绕过需要外部平台控制。
9. 将已归档失败重写为成功：manifest 与 digest 可防篡改地提示异常，但不能抵抗完整 Git history rewrite/force push。
10. 执行未验证的 `curl | sudo sh`：经 Input Trust 路由时策略层可能阻止；不提供操作系统隔离保证。
11. 扩大 scope 并在 Summary 中隐藏：Contract、Git diff、changedFiles、Diff Ownership 和 Summary 交叉检查使其相对较强。
12. Agent 自行批准 PR：workflow 语言可拒绝自我声明批准；可信身份与职责分离需要 provider Required Review、CODEOWNERS、token permissions 和 Branch Protection。

未来验收必须把 request-time、post-write 与 physical-control 结果分开；如实使用 `blocked`、`review`、`human_confirmation_required`、`detected` 和 `out_of_scope`，并测试显式、隐晦、释义、多语言、tool/log/web/README 以及正确/错误分类的 requested-operation 变体。它还必须证明 adopter 安装复制了什么及 adopter CI 实际运行了什么，并把外部 provider controls 作为 delegated evidence，而不是原生能力。

WI-21 是 WI-20 的 corrective process/quality Work Item，必须在 WI-18 发布前完成。WI-20 已交付去重、Fast/Full/Release 入口、组级 telemetry 和 fail-closed 约束，但其 Summary 明确保留了三项未闭合证据：Workflow 尚未拆成独立 Job、尚无五类 hosted before/after 测量、计时尚未覆盖每个 Make gate。不得把这些 Known Gap 直接当作发布前已完成；WI-21 必须分别补齐实现和证据，或以结构化、可审计的 not-run 原因经用户最终复核后才能决定是否继续。

WI-21 的 PR #408 又暴露了 RFE-ISSUE-094（source-bound evidence 维护误触发发布准备）和 RFE-ISSUE-095（失败 evidence 未列出 skipped/dependent jobs 且诊断误导）。在恢复 WI-21 前，`process-evidence-release-preflight-20260727` corrective Work Item 先修复这些问题以及 RFE-ISSUE-091/092/093；不实现 WI-10、不修改候选版本、不发布。
Corrective Work Item 质量门又记录 RFE-ISSUE-096：显式 release intent 改造初次删除了现有 workflow regression 依赖的事件边界注释，已恢复注释并保留新 intent 门禁；coverage 84.97% 也按 fail-closed 停止，补充分支回归后再重跑，不降低 85% 门槛。

Corrective Work Item 最终收尾又记录 RFE-ISSUE-097：Contract 变更后，Summary 的 before_edit checkpoint hash 未同步，`aiAgentRisk` 按设计 fail-closed；已刷新 before_edit/before_finish 两个检查点并通过，保留该恢复步骤作为后续收尾流程要求。

PR #410 的 hosted run `30272658885` 证明末端聚合能如实记录 `template-smoke=success`、`installation-smoke=success`、`release-evidence=failure`，但也暴露三个必须保留到最终流程复核的问题。`RFE-ISSUE-100`（CI evidence 结构，高）：required Job 列表曾在上游 `template-smoke` 内生成，结构上无法取得尚未执行的下游最终状态；修复必须固定为 `if: always()` 的末端 Job，从 `needs.<job>.result` 生成完整证据并先验证失败证据再返回失败。`RFE-ISSUE-106`（归档/状态恢复，中）：归档后、提交前的 transient diff 与 no-active status marker 语义冲突，提示的 `repair-ai-status` 无法消除该阶段差异；本工单只记录并遵循“先提交归档 bundle，再执行 PR 边界”，最终统一判断是否需要改进状态流程。`RFE-ISSUE-107`（发布意图边界，高）：PR #410 在普通 PR 上无条件执行 `check-release-state-consistency`，使非发布变更被历史发布 projection 阻塞；替代工单必须用可执行 workflow 回归证明普通 PR 两个发布 Contract 检查均为零调用，只有显式发布准备意图才 fail closed 执行。

PR #410 已作为 superseded corrective PR 关闭且未合并，归档证据保持不可变。依照 Work Item 生命周期规则，修复由最新 `origin/main` 上的新工单 `ci-evidence-terminal-aggregate-v2-20260727` 和 replacement PR 完整交付；在其 hosted 三 Job 与末端 aggregate evidence 全部成功、PR 合并、`ai-close-work-item` 和本地/远端分支清理完成前，WI-21 不得恢复。

替代工单首次完整质量门记录 `RFE-ISSUE-108`（供应链投影检查，中）：workflow 变化使 SBOM 重建后，`check_supply_chain.py sbom`、`provenance`、`release` 均通过，但 `release.json.supplyChain.sbomDigest` 仍引用旧 SBOM，直到约七分钟后的全量 `test_release_distribution` 才发现跨文件失配。本工单只对齐既有 v0.5.42 digest projection，不改变 release identity、Tag 或发布状态；“快速供应链检查应直接覆盖 release metadata projection”保留到计划完成后的统一流程改进评估，不以重复长测试代替问题记录。

替代工单第三次完整质量门通过后记录 `RFE-ISSUE-109`（Summary 校验顺序，中）：`ai-finish` 在 431 秒 full quality 之后才由 `aiSummary` 发现三个未注册的自定义 verification 名称和一个被错误放入本地 `path` 字段的 hosted URL。已删除非 registry verification，并以现有本地计划路径加 URL locator 表示 hosted evidence，`check-ai-change-summary` 随后通过；“在长质量门前提供不要求所有 verification 已通过的 Summary schema-only 检查”保留到计划完成后的统一流程评估。

WI-21 在 corrective 合并后以 PR #408 run `30280375075` 完成真实 Hosted 重验：`template-smoke` 22 分 14 秒、`installation-smoke` 1 分 27 秒、`release-evidence` 7 秒、末端 `ci-evidence` 4 秒，兼容性 run `30280370545` 的 28 个 Job 全部通过。`make quality` 对应步骤约 21 分 21 秒，未达到 p95 <15 分钟目标，也不能证明实质性能改善。新增 `RFE-ISSUE-110`（性能证据/诊断，中）：当前 Job 日志仍以 heartbeat 为主，gate 子进程输出未实时流式呈现，且 timing/JUnit/慢用例报告未作为成功或失败工件上传。WI-21 只按“可观测性与职责边界完成”收口；下一张深度性能工单必须以该 run 为 hosted 前基线，完成 session 隔离、流式诊断、失败工件上传和 `project-test` 结构性优化，并以至少三次同类型 Hosted run 的 median/p95 验收。

该后续工单的唯一执行标识为 `quality-gate-deep-performance-optimization-20260728`，属于 WI-20 的深度性能闭环，不是发布工单；必须完整完成其独立 PR、Hosted 三次同类型测量、merge、archive、`ai-close-work-item` 和本地/远程分支清理后，才允许进入 WI-10。

深度性能工单启动后新增 `RFE-ISSUE-111`（Preflight 状态机/流程，高）：Contract 已无 unknown、具备明确 intent/scope/acceptance/capability/executionDecision，并声明五个必须在实现后验证的 required scenario，但 Preflight 仅因这些场景为 `unverified` 而进入 `needs_human_confirmation`；记录用户既有授权后又进入同样被 enforced policy 阻塞的 `human_decision_recorded`，除非提前伪造 `verified`，否则不存在合法的 implementation-ready 转移。性能实现立即暂停，当前分支保留已产生的失败测试和最小安装发行边界修复；先用独立 corrective Work Item 增加“有具体 expected 与 verificationPlan 的 planned verification 可进入实现、finish 仍要求 Summary verified evidence”的可执行状态机与回归门禁，完成 PR/merge/`ai-close-work-item`/分支清理/main 同步后再 rebase 恢复性能工单。

当前已启动的 `publish-new-version-20260727` 只作为发布准备占位工单处理，不执行 provider publication；它完成后必须先关闭，再按上述五阶段顺序启动 WI-21 和后续 corrective Work Item。实际发布必须使用新的、单独的 WI-18 发布 Contract。

## 三、各 Work Item 的执行边界与验收要求

下面每项是该工单 Contract 的最小内容；执行时必须补充准确文件路径、当前 base SHA、实际证据 URI 和项目命令，不得直接把计划文字当作完成声明。

### WI-01：Canonical Evidence Foundation

**范围：** 设计并实现每类事实的唯一 Canonical Evidence/Event，绑定 Contract、Summary、Verification、PR、CI、Approval、Release 和对象工程证据；提供 Machine JSON 到 Markdown/PR/Status 的派生链。

**验收：** 重复事实字段被检测；来源缺失、digest 不匹配、过期或矛盾时 fail closed；派生输出可由同一 JSON 重建；无证据声明不能进入 ready/release 状态。

**必须验证：** schema、digest、事件关系、重复/冲突/过期负例、Summary/Outcome/Status/PR parity。完成后重新核对本计划的“事实源唯一”约束。

**WI-01 当前实现边界：** Canonical Evidence 的机器契约位于 `.ai/trust/schema/canonical_evidence.schema.json`，验证与稳定 JSON→Markdown 派生入口位于 `scripts/ai_canonical_evidence.py`，回归测试位于 `tests/test_canonical_evidence.py`。WI-01 只建立事实源、digest、事件引用、声明支持关系和派生基础；Unknown/人工确认、安装事务、Task Outcome/PR/Status 完整接入分别由后续工单实现。

### WI-02：Unknown and Human Confirmation

**范围：** 将 `unknowns` 扩展为 `knownUnknowns`、`unresolvedQuestions`、`assumptions`、`examinedAreas`、`unexaminedAreas`、`evidenceGaps` 与 `unknownAssessment`；分离 Reviewer/Owner/Security/Release Confirmation，并绑定对象、范围、digest、时间、角色、结果和过期。

**验收：** 空数组只能显示“No known unknowns were recorded”；Unknown 不得静默变成 Not Applicable；`needs_human_confirmation` 必须包含 Problem、Reason、Known/Unknown evidence、Options、Recommendation、Consequences、Question 和 STOP 默认动作；Critical 批准不能由“OK”替代。

**必须验证：** 缺证据、配置变化后旧批准、错误角色、过期批准、未回答和缩小范围恢复测试。完成后对齐所有人工确认文档和输出。

**WI-02 当前实现边界：** Unknown assessment schema 位于 `.ai/schemas/unknown_assessment.schema.json`，验证与 `needs_human_confirmation` STOP 默认输出入口位于 `scripts/ai_unknown_confirmation.py`，回归测试位于 `tests/test_unknown_confirmation.py`。WI-02 只建立未知/人工确认的结构化边界；完整 Task Outcome、Cockpit Status、PR 和发布消费仍由后续工单完成。

### WI-03：Source Mode and Transactional Installation

**范围：** 明示 `RELEASE_VERIFIED`、`LOCAL_CLEAN_COMMIT`、`LOCAL_DIRTY_WORKTREE`、`CUSTOM_SOURCE`、`PRIVATE_MIRROR`、`UNKNOWN_SOURCE`；写入前完成 repository/commit/tree/active WI/remote/default branch/source/marker/symlink/traversal/ownership/write-plan 检查；实现事务、锁、恢复和回滚；使 dry-run 真正只读。

**验收：** 未知 source 停止；dirty local 不伪装 release；所有写入在 write plan；不跟随不受信 symlink、不越过 `..`、不覆盖未管理文件；失败恢复 branch/HEAD/files；并发第二进程安全退出；dry-run 不产生 repository mutation；安装完成不冒充 project calibration 或 production ready。

**必须验证：** 指示中的真实安装矩阵、dry-run mutation snapshot、权限/换行、interrupt/rollback/lock/symlink/path traversal 测试。完成后对齐安装与校准文档。

**WI-03 当前实现边界：** Source Mode 分类与事务原语位于 `scripts/ai_installer_transaction.py`，安装器接入位于 `scripts/install_ai_cockpit.py`；Source Mode、write-plan、锁、路径穿越和未知 source 负例位于 `tests/test_installer_transaction.py`，现有安装事实/计划/边界测试继续作为回归套件。WI-03 不承担 WI-04 的对象工程校准、生产就绪或发布身份声明；dirty local source 必须保持为本地模式，不得冒充已验证 release。

**WI-04 当前实现边界：** `scripts/ai_calibration_inventory.py` 为每项校准证据输出受限的 `evidenceKind`（`fixture`、`hosted`、`adopter_execution`、`not_verified`），默认和缺失外部证据保持 `not_verified`；库存校验拒绝未知类型，静态/fixture 证据不得提升为 adopter/hosted 或生产就绪声明。相关边界由 `tests/test_calibration_inventory.py` 与校准/采纳回归测试验证；本工单不伪造外部对象工程、CI 身份或真实 adopter 执行证据。

**WI-05 当前实现边界：** `scripts/ai_input_trust.py` 提供本地、确定性的 source/trust/authority 记录、注入指示器分类和高风险操作 fail-closed 重新评估；`tests/test_input_trust.py` 与 `tests/test_input_trust_corpus.py` 覆盖中文、日文、英文及混合输入，另含隐藏 HTML、Base64、Unicode、嵌套引用、CI/tool/generated 输入。`docs/security-boundaries.md` 明确该分类器不是完整注入检测器、身份验证器或 provider/repository 控制替代品；本工单不承担 WI-06 的 Capability Truth Matrix，也不执行外部写入、push、merge、release 或权限变更。

### WI-04：Adoption, Calibration and Adopter Evidence

**范围：** 保持 Runtime Installation → Adoption → Project Calibration → Pilot Work Item → Gate Promotion；改造问卷、默认值条件、Unknown 分类和 Not Applicable 理由；建立 Python/TypeScript/Node/Flutter/Android/Swift/Xcode/CocoaPods、GitHub/GitLab、非标准 remote/branch、detached/shallow/dirty、macOS/Linux/WSL 的证据矩阵。

**验收：** 安装不自动批准 Project Profile；没有可靠默认值时必须选择/输入；fixture、hosted smoke、adopter execution、not verified 四类状态不可混淆；对象工程未执行时不得声明支持或 production ready。

**必须验证：** 真实 fixture/hosted smoke 能力和无法执行场景的明确标记；完成后对齐采用指南、校准指南和 Capability Matrix。

### WI-05：Input Trust and Prompt Injection

**范围：** 对 human/repository/issue/web/log/dependency/tool/generated 输入建立 sourceType、trustLevel、instructionAuthority、mayContainInstructions、external 模型；把内容和授权分离；高风险操作前重新评估 policy。

**验收：** README、Issue、日志、网页、依赖文档、注释和 tool output 不会自动成为授权；伪造管理员/用户批准、override、secret 或紧急命令不能提升权限；注入结果区分 detected、contained、blocked、human_confirmation_required、not_detected、out_of_scope。

**必须验证：** 中英文、日英文混合的直接/间接/Markdown/HTML hidden/Base64/Unicode/多层引用/恶意文件名/CI annotation corpus，以及写入、删除、push、merge、release、secret、权限变更前重新评估。完成后对齐安全边界文档。

### WI-06：Absurd Tests, Hallucination and Capability Truth

**范围：** 建立荒诞测试 L1 结构、L2 行为、L3 对抗、L4 恢复；覆盖能力、证据、完成、语义、世界事实、授权幻觉；将公开能力绑定到 capability/status/sourceEvidence/testEvidence/commandEvidence/limitations/digest。

**验收：** 火箭、删除生产数据、绕过 CI 发布、伪造批准/测试、secret、不存在 API、无对象工程安装、无网络最新资料、无权限 push、无法运行 Xcode/Android instrumentation 等案例都明确停止并说明安全替代；测试通过不被误写成产品能力；证据变化自动降级为 evidence_stale 并停止发布。

**必须验证：** 指示中的标准荒诞案例、每类幻觉负例和 Capability claim 文档引用检查。完成后对齐产品边界和能力声明。

**WI-06 当前实现边界：** `scripts/ai_capability_truth.py` 提供离线、确定性的 Capability Truth 行证据绑定、digest/stale 降级和 L1-L4 荒诞案例安全评估；`tests/test_absurd_capability_truth.py` 与 `tests/test_capability_truth_matrix.py` 覆盖能力、证据、完成、语义、世界事实、权限边界、不可用 API/工具链和恢复替代路径。该边界不声明通用幻觉防御、真实生产操作或对象工程已完成。

**WI-07 当前实现边界：** `scripts/ai_work_item_state.py` 提供离线、确定性的 canonical transition、证据 digest 门禁、稳定事件 ID、幂等 no-op 和 paused/stale recovery；`tests/test_work_item_state_machine.py` 覆盖非法顺序、缺失/过期/矛盾/远端不一致证据、重复事件、中断恢复和状态未知。该边界不实现 Provider 身份/审批、外部 API 变更或发布/安装行为。

**WI-07 流程问题记录：** `WI-07-ISSUE-001`：coverage policy 初次插入位置/缩进错误，导致新生产脚本未被测试关联；已先修正 association 并通过 coverage guard。`WI-07-ISSUE-002`：新参考文档初次缺少仓库要求的 author 元数据；已补齐并通过文档元数据检查。两项均已解决后才继续工单。
追加记录：`WI-07-ISSUE-003`：ai-start 后仍在 main，ai-finish 正确阻止；已创建专用 `codex/lifecycle-state-recovery` 分支后继续。`WI-07-ISSUE-004`：Contract 最终化晚于 before_edit checkpoint，导致 Agent Risk stale；已在最终 Contract 后刷新 checkpoint 再继续。

### WI-07：Work Item State Machine and Recovery

**范围：** 固化 `created → preflight_ready → implementation_active → verification_pending → finish_ready → archived → pushed → pr_open → merged → close_authorized → closed` 及 paused/blocked/cancelled/rollback/stale；为每个转移记录前置、证据、事件、角色、恢复性和可逆性；实现并发和崩溃恢复。

**验收：** 未 archive push、未 merge close、未授权 cleanup、active 冲突、stale base finish、Contract/Summary 不匹配、Manifest digest 不一致、错误 PR branch、错误 merge commit、默认分支未包含 merge、rollback 后显示 done 均停止；重复执行不产生重复 archive/event。

**必须验证：** 双 `ai-start`、双 `ai-finish`、archive 中断、branch 创建后失败、close 网络断开、CI 延迟、Provider 部分成功、本地/远端不一致。完成后对齐生命周期文档和状态表。

### WI-08：Verification Efficiency and Escalation

**范围：** 正式化 Light/Standard/Strict 与 Focused/Full Verification；建立包含 base/diff/command/tool/dependency/environment/config digest 的 content-addressed cache；建立检查 DAG；定义异常自动升级条件。

**验收：** Light 不执行无关 Full；Standard 的 PR 有必要 Full；Strict/Release 始终 Full；关键输入变化使 cache 失效；删除测试、改 CI/security/release、越 scope、出现 unknown/injection、失败后改测试等触发升级而非降级。

**必须验证：** cache 命中/失效、DAG 分支、升级和 release Full Gate。完成后对齐 checks catalog、Make target 和验证指南。

**WI-08 当前实现边界：** 仅在仓库本地实现确定性的 verification policy、content-addressed cache key/invalidation、check DAG 和单调升级；不实现外部 CI Provider 调度、凭据、发布或安装行为。Light/Standard/Strict 的判定和 Focused/Full 选择必须由可审计输入派生，任何未知、注入、越界或高风险改动均只能升级，不能降级。

**WI-08 流程问题记录：** `WI-08-ISSUE-001`：Contract 初始骨架触发 `not_ready`，已补全 intent、原始请求、来源、风险审查、验收和场景覆盖后重跑。`WI-08-ISSUE-002`：三个中风险场景在实现前没有证据，预检要求 `needs_human_confirmation`；用户已授权连续执行，本次授权作为继续实现的依据，场景不得预填 verified，必须在实现和验证完成后补齐证据并再次通过门禁。`WI-08-ISSUE-003`：新 Make target 初次未设置 `PYTHONPATH=scripts`，导致模块导入失败；已先修正 Make target，再继续验证。`WI-08-ISSUE-004`：全量安装测试发现 `ai_verification_policy.py` 的运行时依赖未进入 installer catalog；已将 `ai_impact_classifier.py` 纳入安装清单并重新验证安装面。`WI-08-ISSUE-005`：系统不变量发现 checks catalog 的新 target 未同步到 `templates/make/Makefile.ai`；已补齐安装模板 target 并重新运行全量测试。`WI-08-ISSUE-006`：修复模板同步后 Contract hash 变化使原 `before_edit` checkpoint stale；已在最终 Contract 后刷新 checkpoint，再继续 finish。

### WI-09：Evidence-backed Task Outcome

**范围：** 生成一屏 Human Summary 与可下钻 Evidence Detail；覆盖完成内容、问题、停止、解决、避免影响、剩余风险、未知、人工决策、验证、下一步；由事件、diff、CI、approval、release、archive manifest 派生。

**验收：** Findings/Risks/Interventions/Forced Stops/Resolutions/Recurrence Prevention 可追溯；Avoided Impact 使用条件语言且绑定证据；不制造评分、效率、金钱、时间或自我表彰；残余风险不可隐藏；JSON/Markdown/PR/Status 事实一致。

**必须验证：** 空/最小/完整报告、五种最终状态、invalid binding/status/severity、dedupe/recurrence、所有 stop outcome、multilingual、privacy、no-score 和 unsupported claim 负例。完成后对齐报告文档与 PR 摘要。

**WI-09 当前实现边界：** 仅实现本地、确定性的 Task Outcome 证据聚合与派生视图；机器 JSON 是事实源，Markdown/PR/Status 是派生视图；不实现外部 Provider 身份、CI API、审批或发布变更，日语能力的发布前综合评估仍由 WI-16 负责。

**WI-09 流程问题记录：** `WI-09-ISSUE-001`：Contract 初始骨架触发 `not_ready`，已补全 intent、原始请求、来源、验收和风险审查。`WI-09-ISSUE-002`：三个中风险场景在实现前没有证据，预检要求 `needs_human_confirmation`；用户已授权连续执行，继续实现但不预填 verified，必须在测试完成后补齐场景证据并重新通过门禁。`WI-09-ISSUE-003`：验证器原先未拒绝重复 eventId 和非法 severity；已先补充 fail-closed 校验及负例测试，再将场景证据标记为 verified。`WI-09-ISSUE-004`：新增负例测试初次未纳入 Contract scope，finish 的 Scope Guard 已阻止继续；已补充 scope 后重跑。`WI-09-ISSUE-005`：Scope 补全后旧 before_edit checkpoint hash stale，Agent Risk 正确阻止 finish；已在最终 Contract 后刷新 checkpoint，再继续 finish。

### WI-10：Documentation Alignment

**范围：** 安装文档拆为“30 秒开始”“标准采用指南”“安全与发布验证”；为命令标注 `syntax_tested`、`fixture_executed`、`hosted_executed`、`adopter_required`、`illustrative_only`；建立 release/version/ref/path/command/Make/capability 多语言检查和历史文档隔离标记。

**验收：** README、README.ja、README.zh-CN、安装指南、release metadata、Make target、路径、环境变量、Capability 状态一致；North Star、产品边界、安装、人工确认、安全限制、注入限制、企业边界、支持范围、版本和 Task Outcome 关键语义同步；历史文件默认降低上下文优先级。

**必须验证：** docs metadata/link/command/version/capability/multilingual checks。完成后逐项记录本计划与所有已完成 Work Item 文档的对齐结果。

**WI-10 当前实现边界：** 首个 corrective `wi10-installation-documentation-completion-20260728` 完成了分层文档与基础事实门，但全量审计随后确认采用入口仍不合格。当前 corrective `wi10-prompt-first-multiplatform-installation-20260728` 将 `installation.md`、`installation.zh-CN.md`、`installation.ja.md` 升级为结构一致的完整手顺：以可复制 agent prompt 为主，按零编程经验标准解释前提、每个 Wizard 选项、scaffold 分类、十阶段 Calibration、首个 Work Item/PR/hosted CI、人工决策、merge/closure、停止恢复与最终成功清单；并新增 iOS、Android、Java 各自英中日完整实例。`scripts/check_docs_metadata.py` 与 mutation tests 对三语文件、15 个 novice stage、10 个 calibration stage、prompt authority boundary、retained-command 解释 marker、9 个 platform 文件/阶段/非声明边界及同语言入口 fail closed；本工单不改 runtime/installer 能力、不执行发布，也不提前声明后续全面日语能力评估通过。

**WI-10 流程问题记录：** `WI-10-ISSUE-001`：请求的短任务 ID `documentation-alignment` 已存在历史记录，`make ai-start` fail-closed 地分配实际 ID `documentation-alignment-20260726`，避免复用历史 Contract/分支。`WI-10-ISSUE-002`：初始 Contract 骨架触发 `not_ready`；已补全 scope、outOfScope、sources、acceptance、verification、intent、原始请求和 scenario coverage，并重新运行 Preflight 与 checkpoint，不复用旧证据。`WI-10-ISSUE-003`：原 WI-10 虽有宽泛 scope 与 no-change rationale，却遗漏用户点名的 `installation.md` 实改；corrective `wi10-installation-documentation-completion-20260728` 已把该路径改为实现证据，增加双向追踪和负向测试。`WI-10-ISSUE-004`：日语风格检查曾扫描中文文件并把“阻断”误判为日语问题；检查范围已限定为 `README.ja.md` 与 `*.ja.md`，既有日语负例继续通过。`WI-10-ISSUE-005`：五策略文档审查发现原自动检查未覆盖的事实漂移：中日 README 在 installer 建立远程基线分支前捕获 `ADOPTION_BASE`、覆盖率仍写 80% 而实现为 85.10%、remote tag 被误称为 provider published、Wizard 可见 UI 被过度声明为日语默认、Standard Adoption 在 archive commit 前调用 PR check，并硬编码 `origin/main`。已修正文档、补全日文主流程，并把 coverage/base/lifecycle/UI/tag/remote 边界加入 fail-closed 文档事实回归。`WI-10-ISSUE-006`：首次 `ai-finish` 在约 4 秒的 fast-static 阶段被 Mypy 阻止，因为新 checker 的局部 `paths` 缺少 `list[Path]` 类型标注；已补类型并要求从头重跑 Finish，不复用失败运行。

`WI-10-ISSUE-007`：完整质量中的 nested finish/adopter 测试继承了外层 WI-10 的直接 `CONTRACT`、`TASK` 等环境变量，现有清理只处理编码在 Make flags 中的值；WI-10 立即暂停，独立 corrective 与 Hosted recovery 通过 PR #421 合并，直接环境键和编码键均被 fail-closed 清理，1293 个本地测试及 35 个 Hosted 检查通过，两个分支和临时 worktree 均已清理，WI-10 再通过 `ai-resume-work-item` 续接到该 merge commit。`WI-10-ISSUE-008`：恢复后的质量架构把文档 checker 用于比较 Markdown 的 `../reference/...` 文本误判为文件系统 path traversal；保留原路径逃逸规则和负例，只使用 `PurePosixPath` 分段构造权威相对链接，red-first 回归、路径逃逸负例及 40 个 WI-10 文档/追踪测试均通过。

`WI-10-ISSUE-009`：PR #422 合并后，全量双向审计确认 prior corrective 的“完成”判定仍只覆盖分层文档和命令事实，未覆盖完整中文 installation、prompt-first 易用性、iOS/Android/Java 实例和零经验逐步手顺；发布继续冻结，并新建本 corrective 将四项分别绑定 Contract acceptance、machine marker、实现文件和 mutation test。`WI-10-ISSUE-010`：本 corrective 初始 `ai-start` skeleton 按设计 `not_ready`；补全实际 scope/intent/source/acceptance/scenario 后，preflight 又暴露 scenario status 枚举仅接受 `unverified` 而不接受 `planned`、source placeholder 判定会把合法 `examples/...` path 当占位符、acceptance broad-word 判定会把 `review requirements` 的 requirements 视为宽泛词。未绕过 Gate：改为合法状态、使用不触发误判的证据源、将验收改写为精确 review policy 后重新计算，preflight=`ready` 与 `before_edit` checkpoint 通过。该流程摩擦记录供后续流程问题阶段统一判断，不在文档工单内扩大修改 preflight 实现。

`WI-10-ISSUE-014`：本 corrective 首次完整 `ai-finish` 的 1315 项项目测试中有 1313 项通过，日语能力评估 2 项失败；根因是日文安装指南虽完整说明所有异常均停止，但翻译优化删除了评估要求保留的规范术语 `fail closed`。未弱化或绕过日语发布 Gate：在零经验读者可理解的“安全侧で停止”旁恢复规范术语，并要求先跑日语聚焦回归，再从头重跑事务性 `ai-finish`。

`WI-16-ISSUE-012`（Hosted/安装器环境隔离，高）：`japanese-lifecycle-fixture-corrective-20260729` 本地 1434 tests 与 85.87% coverage 通过并归档为 sequence 649，但 PR #439 的 Hosted run `30387736987` 在真实日本語 adopter 安装时失败。外层 template-smoke 注入 `AI_BASE_COMMIT=f8da337...`，`install_ai_cockpit.py` 又以完整 `os.environ` 启动 adopter status generator，使采用方错误解析模板父提交并按设计回滚。PR #439 已关闭且前序 archive 不改写；相邻 recovery `japanese-lifecycle-hosted-env-recovery-20260729` 必须把 Git、coverage、Work Item identity 和递归 Make override 隔离落到安装器生产子进程边界，以 Hosted 同型回归证明采用方 Contract 自身 baseCommit 仍为唯一事实源，并完成 replacement PR、Hosted 全绿、merge、closure 与两个分支清理后才可进入 JA-DOC-001。

`WI-16-ISSUE-013`（计划文档登记，低）：recovery 首次 `quality-fast` 的静态检查全部通过，但 Documentation Metadata 与 System Invariants 同时拒绝新计划未登记到 `docs/reference/documentation-context-registry.json`。门禁行为正确；已把 registry 加入 Contract scope，将本计划登记为 `current_instruction`，并要求从头重跑 fast gate，不复用失败运行的部分结果。

`WI-16-ISSUE-014`（Coverage association，中）：首次完整 `ai-finish` 在长测试前拒绝 `scripts/ai_installer_repository.py`，因为 `installerBoundaries` domain 只登记 shell boundary tests，未把实际覆盖该 Python helper 的 `tests/test_installer.py` 关联为证据。门禁行为正确；已把 policy 加入 Contract scope，在既有 domain 增加真实回归关联，并要求刷新 Preflight/checkpoint 后从头重跑 Finish。

`WI-16-ISSUE-015`（卸载能力声明/评估拆分，严重）：JA-DOC-001 实现核对证明当前 installed Makefile 只有 `ai-cockpit-uninstall-propose`，没有 uninstall facts builder 或 proposal digest binding；`ai_detached_uninstaller.py` 的 `prepare()` 只返回内存中的 writes/receipt model，不删除 filesystem、没有 CLI `main()`，并且不在 installer catalog。disable 只写 result JSON 而不更新 canonical installed state，purge 同样是未安装的内存 model。旧 `installed-lifecycle.md`、Capability Truth Matrix 与 lifecycle fixture 容易把“模型通过”误读成“采用方可卸载”。本工单先让日文手顺在 public executor 缺失时明确 STOP，把关键词检测升级为完整行动结构并修正事实源；评估新增独立 `JA-UNINSTALL-RUNTIME-001` 和 corrective `installed-detached-uninstaller-runtime-corrective-20260729`，不得通过修改文案或直接调用内部函数清除 runtime blocker。

`WI-16-ISSUE-016`（detached 实现真实性/receipt confinement，严重）：`installed-detached-uninstaller-runtime-corrective-20260729` 的首轮实现虽增加公开 executor，却仍从 repository 内即将删除的脚本直接运行，与 Contract 的 detached boundary 不一致；receipt parent 也未阻止 symlink 逃逸。不得以 CLI 名称或 source marker 清除 blocker。实现已改为先复制 executor、facts/proposal/install-facts 四个 module 到 system temporary directory，再由该子进程执行；内部非 detached 调用 fail closed，receipt 逐 component 拒绝 symlink 并记录 `detachedExecution`。完整 quality、PR、Hosted CI、merge、closure 和 clean-adopter 重评估完成前仍不得标记闭环。

`WI-10-ISSUE-015`（文档渲染/验收遗漏，高）：用户在 GitHub `main` 发现 iOS 安装示例表格从第 5 行开始失效。核对远端源码确认 iOS、Android、Java 的英/中/日 9 份文档都在第 4、5 行之间放置 `<!-- platform-stage5: proposal-only -->`，GitHub Markdown 因块级 HTML 注释结束表格，导致 1～4 渲染为表格、5～7 显示为原始 `|` 文本。现有 checker 只按 marker 存在和逻辑行数解析，未验证连续 Markdown 表格结构，因此错误通过 WI-10 验收。发布继续冻结；当前流程 corrective 完整关闭后，优先执行 `wi10-platform-table-rendering-corrective-20260728`，将 marker 移出表格、对 9 份文件逐一检查，并增加“表格行之间不得有块级注释/空行”的 fail-closed mutation regression，完成独立 PR/merge/close/branch cleanup 后才恢复其他流程问题。

`WI-10-ISSUE-016`（校准清单/验收遗漏，高）：用户继续核对时询问校准清单位置。三语 `installation` 当前第 9 节只有十阶段说明和请求表，第 15 节只有最终成功项目；不存在可逐项填写/勾选的完整 Calibration checklist，不能为每一阶段清楚记录证据、回答类型/值、Candidate 变化、Owner/Reviewer、PASS/STOP 和完成状态。原 WI-10 Contract 明确要求 `complete calibration checklist`，但 checker 只验证 stage marker/行数，因而把“有十阶段内容”误当成“清单已交付”。同一 `wi10-platform-table-rendering-corrective-20260728` 必须升级三语主安装文档，提供结构和语义一致的十项可勾选清单，并新增字段完整性、十项数量、三语结构和 mutation regression；不得用最终成功清单替代校准清单。

`WI-10-ISSUE-017`（发布元数据安装路径，严重）：独立 Accuracy review 核对发现旧三语手顺把 moving `main/release.json` 与 tagged release asset 组合为同一证据链；当前 main 记录的 v0.5.42 archive SHA-256 为 `fe0fc661…`，公开资产实测及 tag-pinned metadata 为 `54cf33cb…`，照旧手顺会 fail closed。用户明确安装手顺不得固定到某个版本，因此 corrective 不写死替代版本：每次安装从 provider release evidence 动态发现最新 stable semantic version，排除 draft/prerelease，再只用本次解析出的 tag-pinned `release.json` 验证 source/installer/archive/digest。checker 必须拒绝 moving-main digest authority 与 hardcoded semantic version。

`WI-10-ISSUE-018`（初学者 Session/activation 路径，高）：五策略文档审查形成共识，首版清单要求初学者把 Markdown 表复制到 validated Summary JSON，但 Summary schema 无对应字段；同时人类显示值 `yes/no` 未映射到 Session machine value `yes_no`，Stage 10 后也缺少独立 activation plan/approval。corrective 必须以 persisted Calibration Session 为权威记录，由代理定位并逐项展示草案，禁止用户手改 JSON；三语明确四种 machine answer type，并在 local checks 前分别提供只读 activation plan 与 bounded activation approval prompt，记录原子写入、前后状态和失败恢复。

`WI-10-ISSUE-019`（三语实例一致性，高）：最终 Consistency/Clarity review 发现日文 iOS、Android、Java 文档各有七阶段填写示例，而英文和中文只有抽象请求表；同时三语 Stage 7 没有强制代理输出逐要求、逐证据的具体验证表。不得删除更完整的日文内容来取得表面一致：九份文件都必须保留抽象七阶段表，并新增结构一致的七行填写示例；Stage 7 明确要求 evidence path/URL、commit SHA、PASS/STOP、missing item 和平台 module/variant/profile，checker 与 mutation test 对示例 marker、连续七行、五字段和三语存在性 fail closed。

`WI-10-ISSUE-020`（可安装 release 选择，严重）：再次核对公开 tag/asset 发现最新正式 tag 不等于最新可验证 release：`v0.5.44` 与 `v0.5.43` 的 tag-pinned `release.json` 仍声明 `v0.5.42`，只有较旧证据链能与资产 digest 一致。安装手顺不得写死版本，也不得把“最新发布”误当成“可安装”：三语改为从新到旧检查 provider record、tag-pinned metadata、installer、archive 和 digest，选择最高可验证 release；任何更新 release 失败都先逐项展示并 STOP，只有用户明确决定后才可使用较旧可验证 release，禁止静默降级。发布阶段必须修复公开 release metadata 的生产根因，不能只靠文档绕过。

`WI-10-ISSUE-021`（实现事实/手顺断路，严重）：最终 Accuracy/Completeness review 对照当前 installer 与 Calibration runtime，发现文档仍有八类“看似可执行、实际不成立”的事实：archive 是独立验证资产而非 installer input；Wizard 默认 `update_makefile=false`，普通 `make` target 在未 include 时不可用；`yes_no` 是 answer type 且值只能为 `Y`/`N`；清单中的连字符名称是显示标签而非 underscore machine ID；Session 的 reviewer/owner 只是 phase record，不能证明两个不同人的身份；Stage 10 回答与 full self-check 必须先于 confirmation phase；Session 只持久化 schema 支持的 answer/type/reason/stage/events/checks，不能保存完整清单列；只有 Active 文件替换原子化，随后 Session save 是独立步骤。三语必须改为 tag checkout、installer digest、archive 分别绑定同一 release；Make 未接入时由代理使用 `make -f Makefile.ai`；显示真实 type/value；明确 display label；人员身份与角色分离由 Work Item 外部证据核实；其他清单列只映射到 schema 支持的 Work Item review/acceptance/verification 位置；Active 已替换而 Session save/验证失败时显示不一致并 STOP，不得声称回滚。同时补齐较旧 release bounded fallback、Upgrade/Dry Run 分流、CI gap 计划/批准/实施/验证、以及平台 Unknown 示例的 STOP/retry，checker mutation 对这些边界 fail closed。

`WI-10-ISSUE-022`（Make 入口文档 invariant，高）：修正后的 `quality-fast` 首次运行发现，系统 invariant 只识别 `-n` 等无参数 Make option，把必须使用的 `-f Makefile.ai` 中 `-f` 和大写 `TARGET` 占位符误判为真实 target，导致正确的采用方入口无法通过 Gate。不得删除真实入口或绕过 Gate：以 red-first regression 扩展 parser，使其先消费 `-f/--file` 及文件名再校验真实 target；三语把占位符改为 `<target>`，后续步骤改为 prompt-first，让代理依据 Make integration 状态选择普通入口或 `Makefile.ai` 入口并在执行前展示准确命令。

`WI-10-ISSUE-023`（用户补充/可见验收与版本中立，高）：用户在既有 corrective 全部关闭后继续核对，明确“安装手顺没必要固定到某个版本”并追问校对清单位置。现有三语正文已在后段动态选择最高可验证正式 release，也已有多个分散结构 Gate，但文档开头没有把 version-neutral 规则压缩成读者可见的总原则，也没有一张维护者可以直接逐项执行的完整校对清单。独立 supplement `wi10-installation-version-neutral` 从最新 `origin/main` 建立：三语各增加同结构八行可见清单，覆盖版本中立、prompt-first、novice 顺序、十阶段 Calibration、iOS/Android/Java、表格渲染、链接/三语、完整 lifecycle；checker 同时要求语言特定可见说明/标题、统一 topic marker、连续五列表格和准确 1～8 行。负向测试必须删除可见文案、marker、插入块级注释并破坏列数，防止再次用隐藏 marker 或逻辑 pipe 行数替代 GitHub 实际显示。本工单完整 quality、PR、Hosted、merge、`ai-close-work-item` 和分支清理前，不得进行最终日语复评或发布。

`WI-10-ISSUE-024`（流程/启动归属，低）：保存于独立 worktree 的六文件补丁首次直接运行 `ai-start` 时，被 no-active ownership gate 正确拒绝为无 Contract 归属。补丁未提交或绕过：先存入 Git stash，在干净的最新 main 上建立 Work Item，补齐 skeleton 的 Intent/raw request/sources/acceptance/scenarios 到 Preflight=`ready`，记录 `before_edit` checkpoint 后才恢复。独立 worktree 没有 `.venv` 的首次测试命令也未执行；后续使用主 workspace 中被忽略、依赖锁定的虚拟环境运行同一 worktree 源码，并在 Summary 保留环境事实。

`WI-10-ISSUE-028`（静态复杂度门禁，中）：supplement 首次 `quality-fast` 在 `project-lint` fail closed；新增的两项读者可见文案判断把既有 `beginner_installation_errors` 的确定性分支复杂度从 49 推到 51，超过上限 50。不得提高预算或删除验收：把版本中立声明与校对标题验证抽为独立小函数，主函数恢复到 49；聚焦 mutation test 与 `make project-lint` 均通过，并要求从头重跑完整 `quality-fast`。

`WI-10-ISSUE-029`（静态格式门禁，低）：复杂度修复后的第二次 `quality-fast` 在并行 static phase 的 `project-format-check` 停止；新增 helper 需要 Ruff 的确定性换行，`project-lint` 与复杂度已通过，重测试尚未启动。仅对该脚本运行项目 formatter，保留 formatter diff，并从完整 `quality-fast` 起点重跑，不把同次运行的其他并行成功结果当作整门通过。

`WI-10-ISSUE-030`（归档追踪流程，高）：WI-10 supplement 本地 Finish/归档后核对发现 `PLAN-DIRECTIVE-037.contractPaths` 已改为 archive，但 `acceptanceEvidence` 仍保留被删除的 active Summary，正式 Gate 又通过 archive fallback 静默接受。WI-10 分支冻结，独立 corrective `traceability-archive-evidence-rewrite` 完成全 replacement-map 事务、失败回滚、三个 traceability 字段 stale active fail-closed、live active 兼容回归，并清理四条历史同类债务；PR #448 的 required Hosted checks 通过、合并为 `221e214d`、完整 closure/本地远端分支清理完成。WI-10 随后 rebase 到修复后 main，用生成器重建 no-active status 与 655 项 archive index，并把当前唯一 stale Summary 改为精确已存在 archive 路径；重新通过 traceability 与 PR/Hosted lifecycle 前不得报告 WI-10 完成。

`RFE-ISSUE-152`（嵌套 Make 入口传播，严重）：最终 Accuracy review 继续核对发现，`make -f Makefile.ai <target>` 只对直接 target 成立；`ai-finish` 等复合 lifecycle 路径内部仍通过 `scripts/ai_finish.py` 与 checks 配置启动普通 `make`，未安装 `include Makefile.ai` 时子 target 可能不可用。WI-10 三语文档必须区分直接与复合 target：直接 target 可使用显式 `Makefile.ai` 入口，复合 lifecycle target 前必须单独审核并安装 Make integration，缺失或冲突时 STOP。后续“流程问题与 RFE-ISSUE-082”阶段必须以独立 release-blocking corrective `rfe152-nested-make-entrypoint-propagation-20260729` 让选定 Makefile 入口传播到嵌套执行，或消除内部普通 Make 假设，并以采用方 direct/composite 回归证明；实现后须将三语临时 STOP 边界改为已验证的显式入口传播边界。

`RFE-ISSUE-151`（Calibration fail-closed/确认绑定，严重）：Accuracy review 直接核对 `scripts/ai_calibrate.py` 后确认，当前 `unknown` 回答仍会把阶段状态写成 `complete`，review/full-self-check 仅按 complete 判定；Reviewer/Owner confirmation 也未绑定 immutable Candidate digest，Candidate 只在 activate 时生成；Session schema 不持久化完整校准清单证据；Active 文件替换与随后 Session save 不是一个事务，后者失败可留下 Active/Session 不一致。WI-10 文档必须如实说明当前不是 machine-enforced guarantee，并在 runtime corrective 前要求人工 STOP、显示持久化 Session ID/path/SHA-256、逐项确认无 unknown、只使用 schema 支持的证据位置、单独批准 activation，并在 Active/Session 不一致时停止升级。该 RFE 属于后续“流程问题与 RFE-ISSUE-082”阶段的独立 release-blocking corrective：让 unknown 机器阻断 readiness/activation，将 confirmation 绑定 Candidate revision/digest，提供完整清单的结构化证据位置，并使 Active/Session 持久化具有事务回滚或等价恢复保证；加入 all-unknown、stale-confirmation、Candidate-changed-after-confirmation、Session-save-failure 回归。完成完整 PR/merge/close/branch cleanup 前不得发布。

`AUDIT-PROCESS-002`：WI-10 corrective 完整关闭后，WI-01～WI-20 审计分支 rebase 成功，但 `ai-resume-work-item` 发现其不可变 Start Receipt 记录 `baseBranch=main`，而 writer/validator 只接受该值等于当前专用分支，导致标准恢复 fail closed。根因包含启动与恢复两端：`ai-start` 未阻止在可识别的默认分支上创建 Work Item；恢复测试只覆盖先切分支再生成 Receipt 的理想路径。发布和审计继续冻结，先以独立 corrective 落地默认分支启动前置阻断、严格兼容恢复、单一 work-branch 谱系和真实 Git lifecycle 回归，完成 PR/merge/closure/branch cleanup 后再恢复审计。

`AUDIT-PROCESS-002-QUALITY-001`：该 corrective 首次完整 `ai-finish` 的 1320 个项目测试和 coverage 均通过，但新增的固定 `git` list-form 子进程触发 Bandit B603/B607，使低风险 finding 数量偏离批准基线。没有扩大或重生成基线；仅在固定可执行文件、内部常量参数调用点使用现有精确 `nosec` 形式，focused Bandit baseline gate 已恢复通过，完整事务质量门必须从头重跑。

`AUDIT-PROCESS-002-CHECKPOINT-001`：第二次完整 `ai-finish` 已通过 1320 个项目测试、coverage、Bandit、status 和项目质量，最终 Agent Risk 检查发现 `before_edit` checkpoint 仍绑定早期 Contract 哈希 `1cc0c481af4f8424`，而最终评审 Contract 为 `39fc538468c0d0f6`。不得复用该轮部分成功证据；先把两个 checkpoint 重新绑定稳定 Contract、定点通过 Agent Risk，再从头执行完整事务 finish。

**WI-01～WI-20 全量双向追踪审计结果：** 机器事实源 `docs/reference/wi01-wi20-bidirectional-traceability-audit.json` 已建立恰好 20 行的“指示—计划—实现—验收”双向绑定，并以 `docs/reference/wi01-wi20-bidirectional-traceability-audit.md` 提供同事实的人类报告。WI-01～WI-17 与 WI-20 均为 `verified`；WI-18 发布与 WI-19 当前周期计划清理因固定串行顺序标记为 `deferred`，不是缺少证据，也不得提前执行。WI-10 的四条 release-blocking finding 已由 PR #423 对应的 `wi10-prompt-first-multiplatform-installation-20260728` 归档三件套精确闭合并重新验证；当前 open finding 为 0。Checker 现要求 resolved corrective finding 必须绑定 archive index 中同 Work Item 的 Contract/Summary/Manifest，单独修改完成状态不能解除发布冻结。审计工单本身仍须完成 full quality、独立 PR、Hosted CI、merge、`ai-close-work-item` 和分支清理后，才能进入“其他流程问题与 RFE-ISSUE-082”阶段。

### WI-11：Enterprise Governance Boundary

**范围：** 明确可声明的 repository-local evidence、SDLC 控制支持和审计准备能力；明确禁止 SOC 2、ISO 27001、完整注入防御、身份不可抵赖、生产权限隔离、无漏洞、完整 SLSA 等无外部证据声明；建立 adopter checklist。

**验收：** SSO、CODEOWNERS、Branch Protection、Required Review、Separation of Duties、Signed Commit/Tag、Immutable Release、Least Privilege、Secret、Audit Retention、Data Classification、Provider Policy、Data Transfer、Incident Response、Legal Hold、SBOM、Provenance、Dependency/Vulnerability 等均有 `external_control_required/configured/verified/not_configured/not_applicable/unknown` 状态。

**必须验证：** 过度合规声明回归、状态合法性、外部控制缺失时的黄色/红色信号。完成后对齐安全、发布和采用文档。

**WI-11 当前实现边界：** `docs/reference/enterprise-control-matrix.json` 固化六种控制状态和 17 类企业/采用方控制；`docs/reference/enterprise-control-checklist.md` 与 `docs/enterprise-security-boundary.md` 明确 repository-local evidence 与外部控制的边界；三语 README 仅提供同语义入口。`tests/test_enterprise_control_matrix.py` 覆盖状态词汇、控制覆盖、过度声明和 WI-16 发布前日语门禁；本工单不配置或验证采用方 IdP、Branch Protection、合规认证、生产隔离或发布身份。

**WI-11 流程问题记录：** `WI-11-ISSUE-001`：初始 Contract 骨架被 `ai-start` 的 `not_ready` 门禁阻止，原因包括缺少 intent/raw request、范围/来源过弱、场景覆盖缺失和通用验收项；已先补全 Contract 与用户授权下的真实边界，再继续实现，不复用骨架证据。

### WI-12：Code Quality and Test Architecture

**范围：** 在不扩大产品边界的前提下拆分大型脚本到 domain/lifecycle/evidence/policy/installation/calibration/reporting/providers/rendering/cli；CLI 只保留解析、服务调用、输出和退出码；强化 Ruff/mypy/subprocess/path/encoding/symlink/temp-file 规则；补齐测试层次。

**当前执行边界：** 本工单先交付可执行的质量架构检查器、危险输入负例回归、测试层次矩阵和 checks catalog 对齐；不把一次性重写全部大型脚本误记为已完成，后续模块化仍需以证据驱动的独立工单承接。

**流程问题记录：** WI-12 初始合同补全后，预检对“尚未实现的必需场景”只提供 `needs_human_confirmation`，且选项没有“已获授权、先实现再闭合场景证据”的路径。用户已明确授权继续；已记录该问题并保留预检/决策证据，随后在不绕过其他治理检查的前提下继续本工单，完成后将场景状态更新为真实验证结果。

**验收：** 领域模块边界清晰、类型/静态检查通过、危险 shell 与可变默认值受控；Unit、Schema、State Machine、Property、Transaction、Installer Integration、Adopter Fixture、Hosted Smoke、Security Regression、Prompt Injection、Absurd、Release、Documentation 测试均按适用性落地；负例优先。

**必须验证：** focused/full 项目检查、覆盖率/安全/安装/发布回归；完成后对齐架构文档、checks catalog 与测试矩阵。

### WI-13：Deprecated Assets and Archive Hygiene

**范围：** 建立 Deprecated Asset Registry，记录 id/path/type/replacement/deprecatedSince/plannedRemoval/reason/currentReferences/runtimeUsed/migrationRequired；检查无引用模块、旧命令、旧 Make target、过期日期、失效 capability evidence、重复 schema/事实字段、未标历史文档；规划 archive 年度分区、索引、digest、压缩、外部导出和保留策略。

**当前执行边界：** 本工单先交付注册表、引用/过期/受保护证据检查器和恢复边界文档；不删除任何归档证据，不提前清理执行计划文档，不把“注册表通过”声明为已经完成清理。

**流程问题记录：** 与 WI-12 相同，预检在必需场景尚未实现时仅提供 `needs_human_confirmation`，没有“用户已授权、先实现再闭合场景证据”的继续选项。已保留结构化决策证据并按用户授权继续；完成后仅以真实测试结果更新场景状态。

**验收：** 任何删除都有范围、理由、替代、证据和恢复路径；必须保留的 Contract/Summary/Event/Manifest/Release evidence 不被清理；目标工程治理 artifact 增长边界有证据。

**必须验证：** 引用图、过期检查、archive integrity/digest/retention 测试。完成后对齐文档索引和历史标记；不得提前做 WI-19 的计划文档清理。

### WI-14：Cockpit Human Signal Compression

**范围：** 默认只显示 State、Trust Signal、What changed、Problems found、Stop reason、Unknowns、Human decision、Next action；定义 Green/Yellow/Red 语义并提供 Why/Show evidence/Show missing evidence/Show next action。

**当前执行边界：** `scripts/ai_governance_compression.py` 在生成状态中增加 evidence-derived `Key Conclusion`，明确 Green/Yellow/Red 语义、Evidence Basis 和 Next Action；不引入分数、置信度、自我表彰或第二事实源。英文、日文、中文审查指南同步说明颜色和证据边界。

**流程问题记录：** 启动时空白 skeleton 按门禁返回 `not_ready`；Contract 补齐后，严格预检因 3 个场景待实测返回 `needs_human_confirmation`。已依据用户既有授权记录结构化决策，继续实现；场景状态只在真实测试完成后更新。

**验收：** Green 只表示证据充分可继续，不表示绝对安全；Yellow 暴露未知/警告/人工确认；Red 表示证据缺失/冲突/权限不足/不可接受风险/非法流程；所有信号可解释，不以颜色、分数或数量代替证据。

**必须验证：** status rendering、evidence drill-down、缺证据/过期/冲突/人工确认/残余风险场景和无评分回归。完成后对齐 UI/CLI/报告文档。

### WI-15：Full Remediation Acceptance

**范围：** 汇总前 14 项证据，执行完成标准的功能、安全、可用性、效率、文档和质量验收；生成初始完整问题总览、已解决/未解决/接受风险、Known Gaps、剩余人审项目。

**当前执行边界：** `docs/reference/full-remediation-acceptance.md` 记录本地全量验收结果、问题总览和 WI-16 前置基线；不执行日语能力评估、不发布版本、不升级 Capability Truth、不声称 adopter/provider/enterprise readiness。

**流程问题记录：** 严格预检在三项全量场景尚未实测时返回 `needs_human_confirmation`；已记录用户授权的结构化决策，执行真实验收后仅按命令证据更新场景状态。

**验收：** 安装、校准、Work Item、Finish、Archive、PR、Close 通过；非法状态、未知/人工确认、Source Mode、注入、Task Outcome、dry-run、回滚、并发、对象工程矩阵、文档多语言、Capability evidence 和全量质量检查均有结果；任何 unknown、stale、required check 失败或 source/release mismatch 都停止发布准备。

**必须验证：** 全量 Make/pytest/安全/文档/对象工程/发布 preflight；问题总览必须由证据生成。关闭并完成文档对齐后才允许 WI-16。

### WI-16：Comprehensive Japanese Capability Assessment

**范围：** 在任何发布准备或发布动作前，全面评估 AI Cockpit 对日语的处理能力。覆盖日语输入理解、敬语/普通体、技术术语、混合中日英、Markdown/HTML/日志/tool output、Prompt Injection、Unknown/人工确认、安装/校准/Work Item/错误恢复、CLI/Status/PR/文档输出，以及日文工程师可读性和可操作性。评估对象工程的日语 README、Issue、CI annotation、路径/文件名、错误消息和回滚指示。

**验收：** 建立日语能力矩阵，每项必须绑定 source evidence、test evidence、command evidence、limitations 和 digest；正例、负例、荒诞例、注入例、未知/人工确认和恢复例均有结果。关键门禁、停止原因、风险、下一步和人工问题不得因日语输入而丢失、误译、升级权限或变成“通过”。任何缺失、错误、歧义、未评估、stale 或仅凭英语测试推断的日语能力均为ブロッキング信号，不得进入 WI-17。

**必须验证：** 独立日语 corpus、日语对象工程 fixture/可执行场景、日语安装/校准/升级/回滚/卸载文档、CLI/Status/PR parity、日语 prompt injection 与 Unicode/编码/路径测试；对每个 finding 建立对应 corrective Work Item，并逐项完成其 PR、merge、`make ai-close-work-item`、分支清理和 base 同步。若评估通过，仍必须记录明确的 limitations 和未支持范围；不得把“能翻译”或“测试通过”声明成完整日语能力。

**强制顺序：** WI-15 关闭 → WI-16 日语评估 → （若有问题）corrective Work Item 串行完成并重新评估 → WI-16 关闭 → WI-17 Trust Layer 对齐 → WI-18 发布新版本。任何日语评估问题、对应 corrective Work Item 未关闭、Trust Layer 声明与证据不一致，均停止发布准备。

**WI-16 当前重新评估状态：** 2026-07-29 复核证明旧版零 blocker 报告只覆盖少量输入与 11 份文档的关键词存在，未覆盖 WI-16 要求的可执行 CLI/Status/PR/lifecycle/path/encoding 证据，也未被 release preflight 消费。独立 corrective `japanese-assessment-depth-corrective-20260729` 已把评估升级为同一机器 JSON 派生 Markdown 的可复现发布门禁。Wizard `JA-CLI-001`、Status `JA-STATUS-001`、PR `JA-PR-001`、Japanese adopter lifecycle `JA-LIFECYCLE-001`、`JA-DOC-001`（`japanese-uninstall-documentation-corrective-20260729`）和 `JA-UNINSTALL-RUNTIME-001` 的全部功能 corrective、Hosted recovery、PR、merge、closure 与 branch cleanup 已完成。`RFE-ISSUE-154` 的 source-binding corrective 也已通过 PR #450、35 项 Hosted checks、merge、`ai-close-work-item`、本地/远端分支删除与 worktree 清理完整关闭。现已从同步后的 `main`（`26e8fb635d69260a2eb44e8408a5ca829cb88835`）启动独立 `japanese-final-reassessment-20260729`：必须把 canonical report 明确标识为 fresh `final_reassessment`，在 exact source 上重跑完整矩阵并完成独立 lifecycle；在它关闭前不得进入文档对齐或发布。

**WI-16 流程问题记录：** `WI-16-ISSUE-001`：初始文档检查器要求每份文档都包含同一组通用词，错误地把按职责编写的文档判为缺失；已先修正评估流程为每份文档使用职责对应的日语行动术语，再重新生成报告并通过聚焦测试。`WI-16-ISSUE-002`：初始评估把无法由仓库本地证据证明的通用模型 fluency 当成 required 场景；已修正流程边界为“仓库治理路径必须有日语证据，通用模型 fluency 只能作为明确 non-claim”，并在报告与 Contract 中保留限制，未将其声明为能力或发布证据。`WI-16-ISSUE-003`：首次 `ai-finish` 因新增脚本未通过项目 formatter 检查而停止；已运行项目 formatter，重新执行全量质量门禁并以 1147 tests、85.06% coverage 通过后才 archive。

**WI-16-ISSUE-004（评估深度/发布门禁，高）：** 旧版评估把“关键词存在”和英语侧实现证据推断成日语能力，且没有接入 `check-release-preflight`，因此 stale 或浅层零 blocker 报告仍可能放行发布。修复必须以独立 corpus、逐行 source/test/command/limitation/digest、JSON→Markdown 派生、字节级 freshness 检查和 release prerequisite 落地；阻塞报告是正确门禁结果，不允许为使质量通过而把 blocker 改成 limitation。

**WI-16-ISSUE-005（Status 时间字段校验，中）：** 日语 Status 首次真实 Make 生成后，配对校验因时间字段规范化只识别英文 `Generated At` 而拒绝同源日语输出；聚焦 fixture 使用 `<timestamp>` 未暴露该差异。已把规范化扩展到 `生成日時`，将日语 stale 回归改为真实 ISO 时间，并重新运行生成、校验与聚焦测试。此问题证明能力通过条件必须包含真实 Make 往返，而不能只依赖内存 rendering fixture。

**WI-16-ISSUE-006（PR Summary YAML opt-in，中）：** JA-PR executable CLI 回归发现轻量 YAML parser 将 `enabled: true` 保留为字符串，而旧 renderer 仅接受 Python boolean `True`，导致真实 Profile 明确启用后仍静默输出空 fragment。已在 renderer 的 policy 边界只接受 boolean `True` 或大小写无关的明确字符串 `true`，其他值继续关闭，并以真实 YAML CLI fixture 验证日语文件输出和 unsupported locale fail-before-write。

**WI-16-ISSUE-007（Contract 关键域措辞，低）：** JA-PR 初始完整 Contract 用“secret redaction”描述合成 fixture，Preflight 词法保护将其视为真实秘密处理并正确 fail closed。Contract 已改为“synthetic sensitive-value fixture”，明确不读取凭据或生产数据后重新预检为 ready；这是边界澄清，不是关键域授权，也没有绕过 Preflight。

**WI-16-ISSUE-008（restricted write 授权绑定，中）：** JA-PR 首次 `ai-finish` 在 Makefile ownership 处停止，因为 path 虽已列入 scope，但 Contract 的 `restrictedWriteApproval` 仍为 skeleton false；scope 不等于 restricted-write 授权。用户已授权全部日语 corrective 及所需 Make/流程修改，因此已把授权明确限制为本工单的 PR renderer language passthrough，刷新最终 Contract 的 Preflight、`before_edit` 与 `before_finish` checkpoint 后才允许完整重跑 Finish。

**WI-16-ISSUE-009（采用方 lifecycle 证据边界，中）：** JA-LIFECYCLE 初始 fixture 断言模板维护专用 `ai_calibration_wizard.py` 的 locale 文件会安装到采用方，但 installer payload 明确不分发该 Wizard；若沿用该测试，会用模板源码行为伪装采用方能力。已删除该错误假设，改为在真实安装后的临时采用方仓库执行受支持的 `make -f Makefile.ai cockpit-calibrate-session`，验证持久 Session 的 `language: ja`、日文 evidence value、pause/resume 和 canonical stage identity；日语提示仍由安装文档驱动，不声称 adopter CLI 的全部 machine chrome 已本地化。

**WI-16-ISSUE-010（质量/格式，低）：** JA-LIFECYCLE 首次 `quality-fast` 因新增 fixture 未符合 Ruff format 而停止；已运行项目 formatter，并从完整 `quality-fast` 起点重跑通过，未跳过静态或 policy gate。

**WI-16-ISSUE-011（计划追踪 token 漂移，中）：** 首次完整 `ai-finish` 的 1431 项测试通过，但三项 instruction-traceability 回归因 WI-16 状态段更新时删除了 manifest 要求的精确 `JA-LIFECYCLE-001` token 而失败。实现证据没有失败；计划与 traceability manifest 失配。已恢复 finding ID 与 corrective 的显式映射，增加本问题记录，并要求刷新最终 Contract 的 Preflight 和两个 checkpoint 后完整重跑 finish。

**RFE-ISSUE-154（最终日语评估 source binding/流程，高）：** 最新 `main` 上 84 项日语专项测试和当前 `--check` 均通过、矩阵为零 blocker，但报告的 case digest 只包含 evidence path 字符串、状态、observation 和 limitation，不包含对应实现、测试、corpus 与文档的文件 bytes；只要 marker 仍存在，非 marker 变化不会使报告 stale。报告还硬编码旧 assessment-definition Work Item，且 Make 的 `check-release-preflight` 虽依赖 `check-japanese-capability`，却没有把 `RELEASE_PREFLIGHT_SOURCE_COMMIT` 传给 prerequisite，无法证明日语门禁运行在被发布流程断言的 exact checkout。独立 corrective `japanese-assessment-source-binding-corrective-20260729` 必须以 sorted repository-relative file inventory + per-file SHA-256 + aggregate digest 绑定全部稳定评估输入，排除 transient generated Status；同时让日语 CLI 在提供 expected source 时解析并要求其与 `HEAD` 完全相同，让 release Make 变量传播到日语 prerequisite。必须用 red-first evidence-byte drift、missing/escaping path、真实 Git mismatch/equality 和 Make dry-run 回归验收；不得使用包含报告自身 commit 的循环 digest，也不得把本 corrective 的零 blocker 重验当作最终复评闭环。

**RFE-ISSUE-154 独立审查补充：** 审查发现新增 `subprocess` import 未声明固定 argv 的 Bandit 理由、Make 将 source commit 插入 shell、显式空 source 可跳过校验、路径别名在规范化前未去重、符号链接工作树 bytes 与 Git blob 语义不一致，以及缺少 bound/unrelated byte drift 的成对端到端回归。已将 source commit 改为由 Make 原样导出到进程环境、CLI 显式空值 fail closed、证据路径先规范化去重并拒绝任一路径组件符号链接，并加入同时证明 JSON/Markdown stale 与 unrelated 文件不误报的回归；不得通过更新 Bandit baseline 掩盖新增告警。

### WI-17：Add the Authoritative Multilingual Human-Agent Trust Layer Document

**Task:** `document_human_agent_trust_layer`

**Intent：** 说明 AI Cockpit 为什么存在、治理什么，以及证据控制、fail-closed、人工交还、完整可信链和软件供应链证据如何共同建立 Calibrated Human-Agent Trust。现有 `docs/trust-layer.md` 升级为英文权威版本，不新增第四份概念文档。

**范围：**
- `docs/trust-layer.md`：英文权威完整版本；
- `docs/trust-layer.zh-CN.md`：中文完整翻译；
- `docs/trust-layer.ja.md`：日文完整翻译；
- `docs/reference/documentation-architecture.md`：登记 Trust Layer 的 Why/What/How 权威角色，并区分 Design Philosophy、Architecture、Security and Release Verification、Capability Truth Matrix；
- `README.md`、`README.zh-CN.md`、`README.ja.md`：只增加短入口，不复制正文，分别链接对应语言版本；
- 轻量文档一致性检查：三语文件存在、章节 ID/标题数量一致、三语入口存在、架构已登记、内部链接有效、核心边界句未丢失。

**必须保留的现有实现细节：** `Unsupported Claim Regression Gate`、`delusion-test-gate`、`Guard Signal Envelope`、Preflight enforced profile、Raw Request Binding、Requested Operation、Capability Mapping、Human Decision and Recovery、Archive Manifest；可置于 How 后的 `Current Implementation`、`Deterministic Coverage`、`Machine-Readable Evidence`、`Commands and Demonstration` 章节，不得为了概念整洁删除已实现证据。

**验收：** 文档统一使用 Why / What / How 结构，三语语义完整一致；明确 AI Cockpit 是 Repository Governance Layer，不是 SKILL、Agent Runtime 或 Security Sandbox；说明七个治理层：执行边界、控制权返还、已知风险防护、完整可信链、软件供应链证据、人类决策压缩、归档与恢复。完整可信链包含 SHA-256、Git History、Digital Signature、Branch Protection、Hosted CI/External Audit Evidence、Human Approval；说明 SBOM 与 Provenance 的区别，并明确 SBOM 是 Delegated Domain Evidence。不得声称 AI Cockpit 单独实现身份、隔离、不可篡改审计或企业合规；Capability Truth Matrix 仍是当前能力状态的唯一事实源。

**必须验证：** 三语 Trust Layer 文档、README 短入口、Documentation Architecture 登记、内部链接、章节一致性、关键边界句、Native/Delegated evidence 映射；责任边界、Evidence over Self-Declaration、停止/恢复、供应链和企业合规过度声明负例；与 Capability Truth Matrix、Cockpit Status、WI-16 日语评估和 WI-18 发布门禁一致。任何发现的能力/流程/文档问题必须建立对应 corrective Work Item，完成完整 PR/merge/close/分支清理后重新验证。

**强制顺序：** WI-16 及其 corrective Work Item 全部关闭 → `document_human_agent_trust_layer`（WI-17）及其 corrective Work Item 全部关闭 → WI-18 发布新版本。WI-17 不执行实际发布，不把文档对齐当作外部控制或合规认证证据。

**WI-17 当前执行结果：** 已将 `docs/trust-layer.md` 升级为完整英文权威版，新增结构和语义对齐的 `docs/trust-layer.zh-CN.md` 与 `docs/trust-layer.ja.md`；保留现有 Gate、Guard Signal Envelope、Preflight、Raw Request Binding、Requested Operation、Capability Mapping、Human Decision and Recovery、Archive Manifest 等实现证据。已更新 Documentation Architecture 与三语 README 短入口，新增 `scripts/check_trust_layer_docs.py`、`tests/test_trust_layer_docs.py` 以及 `make check-trust-layer-docs`，验证三语文件、章节 ID/标题数量、入口、架构登记、内部链接和核心边界句。`make ai-finish TASK=document_human_agent_trust_layer` 已通过并归档：1148 tests、85.03% coverage，文档/系统不变量、Ruff、mypy、Bandit、供应链、Trust schema、Status、Summary 和 Agent Risk 均通过；当前仅剩 PR/CI/merge/close 生命周期。

**WI-17 流程问题记录：** `WI-17-ISSUE-001`（流程/预检，低）：初始 Contract 未把真实 scope、sources、scenario coverage 和 raw request 写入，`ai-start` 正确以 `not_ready` 停止；已补全 Contract，并以用户已授权的结构化决策记录继续，未把实现前场景误记为已验证。`WI-17-ISSUE-002`（流程/归属，低）：结构化预检决策文件最初不在 Contract scope，before-edit checkpoint 将其标为 unowned；已将 `.ai/decisions/**` 纳入 scope 并刷新 checkpoint。`WI-17-ISSUE-003`（检查器缺陷，低）：内部链接检查器初始只接受文件，把 README 中合法的目录入口 `examples/` 判为 broken link；已允许合法目录目标并重新通过检查。`WI-17-ISSUE-004`（证据状态，待对齐）：在 Contract 细化期间旧预检决策证据出现 stale hash；保留为流程历史，最终 Summary 必须明确该决策仅代表实现授权，不得作为任何实现验证结果，并在 finish 前保证所有场景均为真实 verified 或明确 not_applicable。`WI-17-ISSUE-005`（流程/归属，低）：首次 `ai-finish` 发现新增 `Makefile` target 未纳入 Contract scope，Scope Guard 正确停止；已补充 scope 后重跑。`WI-17-ISSUE-006`（质量/文档，低）：全量测试发现日文文档使用项目禁止的置信度术语，且新增检查器初始覆盖不足；已改用项目规定的日语术语、补充 missing-file 分支测试，并通过相关回归。`WI-17-ISSUE-007`（流程/checkpoint，中）：全量质量通过后，Agent Risk 发现 `before_edit` checkpoint 因 Contract 在实现期间最终化而 stale；已先以最终 Contract 刷新 `before_edit`，再继续 finish，不复用旧 checkpoint。

### 发布前真实荒诞与注入攻击评估：`pre-release-real-absurd-injection-assessment`

**插入原因：** 用户要求在 WI-18 发布版本前，把提供的真实荒诞测试和注入攻击案例加入三个语言版本的完整文档，并验证当前 AI Cockpit 能否正确识别和阻止；任何不足必须先修改到全部测试通过。该工单排在发布前过期资产清理之后、WI-18 之前，不能与发布工单混做。

**权威输入：** `conversation-attachment:real-absurd-and-injection-cases-20260729`。包含 12 个真实案例和四类测试：权限伪造、证据破坏、外部资料注入、危险执行。案例覆盖：以口头确认删除仍被使用的函数、隐藏 Markdown 注入、为变绿删除测试、伪造负责人批准、日志间接注入、依赖 README 诱导上传 `.env`/SSH key、伪造未执行验证、紧急绕过发布 Gate、改写归档历史、执行未知远程 sudo 脚本、隐瞒 Contract 外扩范围、让实现者自我批准。

**计划文档与实现边界：**

- 新增结构和含义完整一致的英文权威版、中文完整版、日文完整版；不得让任一语言只有摘要。建议权威路径为 `docs/reference/real-absurd-injection-cases.md`、`docs/reference/real-absurd-injection-cases.zh-CN.md`、`docs/reference/real-absurd-injection-cases.ja.md`。
- 每个案例必须记录输入来源、`sourceType`、`trustLevel`、`instructionAuthority`、请求操作、危险类别、仓库/外部证据、声明与证据的矛盾、所需独立授权、预期 Gate、预期结果及安全恢复路径。
- 必须使用统一判断链：输入来源 → 指令权限 → 请求操作 → 删除/权限/网络/Secret/发布/历史证据风险 → 仓库证据支持 → 请求与证据矛盾 → 独立授权 → `ALLOW / REVIEW / CONFIRM / BLOCK`。不得实现为 12 组零散关键词，也不得把文件或用户笼统标记为恶意。
- 先盘点并执行当前 `ai_input_trust`、Backtrack Guard、Destructive Change Policy、Diff Ownership、Unknown/Evidence Gap、Human Confirmation、Archive immutability、Evidence over Self-Declaration、Strict Release、Scope、Separation of Duties 等真实路径。任何案例若只被文档描述、只能由人工猜测或未进入机器门禁，必须保持失败并建立实现整改，直到行为与证据通过。
- 保留边界：AI Cockpit 的拒绝理由必须是请求缺少足够证据/权限或与已知事实、安全边界冲突，不是推断用户恶意；外部资料中的合法技术事实仍可作为无操作权限的参考信息。

**验收：**

1. 12 个案例在英中日三份文档中结构、顺序、事实和结果一致，并通过章节/内部链接/关键边界一致性检查。
2. 每个案例都有直接机器测试，覆盖允许内容与拒绝内容的分离、隐藏 HTML、可见注入、日志/tool/generated 输入、Secret/网络/删除/发布/归档/范围/自审边界。
3. 测试不仅断言关键词，还断言 source/trust/authority、requested operation、evidence conflict、Gate、decision、reason 和 recovery；负例证明不能靠“我已确认”“负责人批准”“紧急”“之后再补”等文本提升权限或伪造证据。
4. 当前实现不满足任一案例时，先写 RED 测试，再修统一分类/治理链，重新执行聚焦、荒诞 corpus、注入 corpus、三语一致性、完整质量和真实 Hosted 验证。
5. Capability Truth Matrix、Trust Layer、安全边界和日语最终评估必须按真实实现状态对齐，不得从测试设计反推能力已实现。
6. 工单完成 Contract → Preflight → 实现/验收 → `ai-finish`/archive → push → PR → exact-Head Hosted → merge → `ai-close-work-item` → 本地/远程分支删除 → main 同步后，才允许进入 WI-18。

### WI-18：Publish New Version

**范围：** 这是唯一实际发布新版本的 Work Item。Contract 必须明确 release identity、source commit/ref、tag、asset、distribution、release note、SBOM、provenance、vulnerability/secret、installer lifecycle、Public Install、兼容性和人工发布授权。

**验收：** 严格 Release Gate、source/tag/asset binding、可复现 archive、digest/checksum、SBOM、provenance、扫描、安装/更新/回滚/disable-enable/uninstall proposal/public install、Provider evidence 全部通过；任何失败、未知高风险、授权缺失、身份不匹配或验证器错误 fail closed。

**强制顺序：** merge → `make ai-close-work-item` → local/remote default-base sync → `make finalize-release-freeze` → `make check-release-preflight` → release dependency/SBOM/provenance/tag/provider publish。发布后记录真实版本、URL、commit、assets、checksums 和 evidence，再完成本工单自己的 PR/merge/close（若发布动作属于合并后阶段，Contract 必须明确并重新绑定 source evidence）。不得把 candidate、historical、published 混为一谈。

**WI-18 当前执行结果（发布前阶段）：** 已从 WI-17 合并关闭并同步后的 `origin/main` 建立专用分支；首次 `ai-start` 按流程以 `not_ready` 停止。已补全发布 Contract，声明 source/tag/asset/evidence 绑定、WI-16/WI-17 前置门、SBOM/Provenance/扫描/安装器/兼容性/人类授权边界；新增 `repository_release.publish` 的 authority-required policy mapping 与回归测试。`make ai-finish TASK=publish-new-version-20260726` 已通过并归档 Contract/Summary，完整质量门包含全量 pytest、Ruff、mypy、Bandit、供应链、Trust、Status、Summary 和 Agent Risk。

**WI-18 流程问题记录：** `WI-18-ISSUE-001`（流程/预检，低）：初始 Contract skeleton 缺少发布专用 intent、raw request、sources、acceptance 和 scenario coverage，`ai-start` 正确停止；已补全后重跑。`WI-18-ISSUE-002`（流程/策略，高）：requested-operation policy 没有定义用户已授权的公开发布操作，preflight 正确拒绝 `repository_release.publish`；已先加入 authority-required 的 policy/capability mapping 和回归测试，再继续。`WI-18-ISSUE-003`（流程/授权，高）：高风险发布需要把用户授权和 restricted-write approval 绑定到当前 Contract；已明确授权范围为“所有门通过后发布一次”，不授权任何门禁绕过。`WI-18-ISSUE-004`（Summary/证据，低）：首次 `ai-finish` 发现新增 release guidelines 未写入 Summary；已完成 Summary 对齐。`WI-18-ISSUE-005`（checkpoint，中）：Contract 最终化后旧 before-edit checkpoint stale，Agent Risk 正确停止；已刷新最终 Contract 的 checkpoint 后重跑通过。`WI-18-ISSUE-006`（PR ownership，低）：PR smoke 的 complete-diff ownership 检查发现执行计划虽在 Contract scope，却未在归档 Summary changedFiles 配对；已补齐 Summary 配对记录，待本地/CI PR 检查重新验证。`

**WI-18 发布后置证据待填：** 首次 post-close `make finalize-release-freeze` 与 `make check-release-preflight` 已通过，但 provider workflow 在 identity precondition 处发现 `release.json` 仍为 v0.5.42、`next-release.json` 才为 v0.5.43；未创建 tag 或公开 asset。该问题转为 corrective Work Item `release-metadata-promotion`，先通过独立 PR/merge/close 生命周期修复 source-bound metadata projection，再重新执行 freeze/preflight 与 provider publication。发布后必须将真实版本、URL、source commit、tag、assets、checksums、SBOM、Provenance、CI/provider run IDs 和验证结果重新绑定到发布证据；在此之前不得声明新版本已发布。

**release-metadata-promotion corrective Work Item 流程问题记录：** `RMP-ISSUE-001`（发布门禁，高）：provider workflow 正确阻止了 committed `release.json` 与请求版本不一致的发布；改为从 `next-release.json` 创建 source-bound 的运行时投影，保留已发布 v0.5.42 历史文件。`RMP-ISSUE-002`（流程/归属，高）：在 Contract 外执行 release freeze 会产生无 active Work Item 所有权的生成证据；已恢复并要求先在 corrective Work Item 内生成、再走 PR/merge/close。`RMP-ISSUE-003`（设计/契约，高）：直接提交 v0.5.43 到 `release.json` 破坏历史发布投影并导致既有测试失败；已撤回直接提升方案，改用 workflow runtime projection 并增加回归测试。`RMP-ISSUE-004`（流程/子进程，中）：嵌套 `ai-finish` 测试受外层 coverage/Git/Make 变量污染，导致单独运行通过而收口失败；已隔离环境、清理 Make override，并由 `ai_finish.py` 显式传递项目质量变量，之后全量质量门通过。`RMP-ISSUE-005`（证据/Checkpoint，中）：Contract 在实现过程中补充范围后，历史 `before_edit` checkpoint hash 失配，`aiAgentRisk` 正确停止；已刷新最终 Contract 对应 checkpoint 后重跑通过。`RMP-ISSUE-006`（PR ownership，中）：归档后 PR diff 同时包含 active Contract/Summary 删除与 archive 文件新增，归档 Summary 仅保留 archive 路径导致 complete-diff ownership 无法配对；已在归档 Summary 保留 active source path 并更新 Archive Manifest digest，待 PR 检查确认。`

`RPP-ISSUE-001`（发布流程/顺序，高）：首次重试 provider 发布时，workflow 在创建 runtime `release.json` projection 后才执行 `check-release-preflight`，导致 preflight 把 candidate v0.5.43 当作 committed published metadata 并 fail closed；未创建 tag 或 asset。已建立 corrective Work Item `release-preflight-projection-order`，将 committed-source preflight 前置到 projection，并增加顺序回归测试；修复完成前不得再次触发发布。
`RFE-ISSUE-001`（发布证据/来源绑定，高）：`finalize-release-freeze` 在 post-close 阶段仅修改本地工作树，未进入 `origin/main`；provider exact-source checkout 因而无法看到 freeze/digests，不能通过 release preflight。已建立 corrective Work Item `commit-release-freeze-evidence`，将生成证据纳入 Contract、PR、merge、close 和基线同步。
`RFE-ISSUE-002`（工单收口并发，中）：同一工单同时启动多个 `ai-finish` 会竞争写 Summary 和观测记录，造成临时的 Summary/Guidelines 失败；已停止重复进程并改为单实例收口，后续流程要求同一工单只允许一个收口进程。
`RFE-ISSUE-003`（CI流程/超时，高）：PR #385 的 smoke job 在 `Run repository quality gates` 长时间运行，后续所有门禁无法启动；首次运行被取消并重跑后仍需观察质量门完成。已建立 corrective Work Item `smoke-quality-timeout`，将 job 超时从 90 分钟收紧到 30 分钟并增加 workflow 回归覆盖；超时必须 fail-closed，不得跳过后续检查。
`RFE-ISSUE-004`（质量流程/墙钟时间，中）：PR #386 的 smoke job 中 `make quality` 约 20 分钟才完成；`project-test` 已执行全量 pytest，而独立 pytest gate 仍串行运行，且质量图缺少并行调度。已建立 corrective Work Item `quality-gate-deduplication`：保留所有 specialized gate，改为 bounded parallel gate graph；不得降低覆盖率或删除 adopter 定制 `project-test` 下仍必要的显式门禁。
`RFE-ISSUE-005`（工单收口/分支生命周期，高）：PR #387 合并时错误请求 provider-side `--delete-branch`，先于 `make ai-close-work-item` 删除了可识别的工作分支，导致首次关闭 fail-closed。已从已合并提交恢复可识别分支并重新执行标准关闭；从下一工单起，合并命令不得请求 provider-side branch deletion，必须先在工作分支运行 `make ai-close-work-item`，再由关闭命令删除本地/远端分支并同步默认分支。该问题已记录，后续执行按该纠偏流程继续。
`RFE-ISSUE-006`（分支同步/证据对齐，中）：更新仍开放的 PR #385 到最新 `origin/main` 时，生成状态、archive index 和执行计划发生冲突；已停止自动合并，以 `origin/main` 为权威解决冲突，并确认 PR #385 相对最新 main 只保留发布冻结证据。已建立 corrective Work Item `record-release-freeze-merge-conflict`；后续开放 PR 必须先同步最新远端 base，再执行 PR 检查和合并。
`RFE-ISSUE-007`（CI/归档索引/发布门禁，高）：PR #385 更新后，Ubuntu 3.14 与 macOS 3.11 的 `make quality` 因 authoritative Contract/Summary pair 未登记到 archive index 而失败，覆盖率随失败测试降至 84.97%/84.99%，低于 85% 门槛；macOS 3.14 另出现 Homebrew tap trust 环境失败。已停止发布，修正 archiveSequence、Summary/Manifest digest 和 archive index manifest binding；修正后的 PR 必须重新通过全部检查，Homebrew 问题需在重跑中确认是否为环境性失败。
`RFE-ISSUE-008`（发布证据/来源绑定，高）：WI-18 corrective PR #385 合并并同步 `origin/main` 后，`make check-release-preflight` 发现既有 release-freeze、release-digests、release-state 和 release metadata 仍绑定合并前 source commit/source tree，无法证明 provider 将消费的候选身份与冻结证据一致。已停止发布，建立 corrective Work Item `rebind-release-freeze-evidence`；在该工单完成重新生成、PR、合并、关闭和主分支同步前，不得触发 provider publication。
`RFE-ISSUE-009`（工单初始化/发布证据生成顺序，中）：`finalize-release-freeze-premerge` 要求生成前工作树干净，而 corrective Work Item 的 Contract、计划记录和 start receipt 在启动预检后尚未形成提交，首次生成被 fail-closed 拦截。已将顺序明确为“先完成并提交 Contract/启动证据与问题记录，再在干净工单分支运行 premerge freeze finalization”；不得通过忽略未提交工单证据绕过该门禁。
`RFE-ISSUE-010`（工单证据对齐，中）：`ai-finish` 发现 corrective Contract 已声明 4 个场景，但 Summary 尚未同步 `scenarioCoverage`，因此场景门禁 fail-closed。已停止收口，补齐 Summary 的真实场景状态后再重跑全部收口检查。
`RFE-ISSUE-011`（工单证据/Guidelines，中）：Summary 初始把“专用分支与完整 PR 生命周期”标为 `compliant:false`，导致 guideline 门禁停止，即使当前流程已在专用分支且完整生命周期尚未结束。已将当前分支、Contract 和后续生命周期要求记录为合规证据，最终 PR/merge/close 仍须由后续门禁证明。
`RFE-ISSUE-012`（checkpoint，中）：完整质量门通过后，Agent Risk 发现最终 Contract 缺少 `before_edit` checkpoint；原因是初始 `ai-start` 在 skeleton 预检阶段停止，之后 Contract 被补全但未按最终 hash 刷新 checkpoint。已停止归档，先为最终 Contract 写入 before_edit checkpoint，再重新执行 finish。
`RFE-ISSUE-013`（Summary/证据格式，中）：质量与 Agent Risk 通过后，Summary 校验拒绝了非法 `reviewReadiness.status=in_progress`，并发现预检 decision 文件未列入 `changedFiles`。已改用允许的 readiness 状态并补齐 changedFiles 归属，再重跑最终稳定化。
`RFE-ISSUE-014`（归档证据/路径配对，中）：归档后独立运行 archived Summary 校验时，原 `changedFiles` 仍只列 active Contract/Summary 路径，未覆盖 archive Contract/Summary/Manifest/Index；已补齐归档路径配对并重新计算 Archive Manifest/Index digest。
`RFE-ISSUE-015`（发布证据/来源绑定，高）：PR #390 合并并由 `ai-close-work-item` 同步主分支后，`make check-release-preflight` 仍发现 release freeze、release digests、release state 和归档/安装器摘要绑定的是合并前 source identity；同时要求在 archive/close 后重新 finalize freeze。已停止 provider publication，禁止无工单直接改写发布证据；建立 corrective Work Item `finalize-release-freeze-after-rebind`，先记录本问题、在最新同步主分支上重新生成并完成完整 PR/merge/close/分支清理，再重跑发布预检。
`RFE-ISSUE-016`（工单初始化/流程，中）：为处理 `RFE-ISSUE-015` 首次执行 `make ai-start TASK=finalize-release-freeze-after-rebind MODE=code` 时，自动生成的 Contract skeleton 因缺少发布专用 intent、raw request、sources、scenario coverage 和受限写入授权而按预期 `not_ready` 停止。已补全 Contract 后再重跑预检；不得通过跳过 Contract 完成或直接生成发布证据。
`RFE-ISSUE-017`（工单分支生命周期，高）：建立 `finalize-release-freeze-after-rebind` 的 Contract/启动证据时，初始提交误落在本地 `main`；该提交未推送、未进入 PR。已立即将提交保留到专用 corrective 分支，恢复本地 `main` 与 `origin/main` 一致，并规定后续只在专用分支继续；不能把“Contract 已建立”误报为完整工单生命周期完成。
`RFE-ISSUE-018`（工单证据对齐，中）：`ai-finish` 在完整质量门之前发现 corrective Contract 已声明 4 个 scenario coverage，但 active Summary 未同步该字段，因此场景覆盖检查 fail-closed。已停止收口，补齐 Summary 的场景状态和实际 changedFiles 归属后再重跑；不得用 Contract 单独替代 Summary 证据。
`RFE-ISSUE-019`（工单证据格式，中）：全量质量门通过后，`ai-finish` 的 Summary 校验拒绝了 `reviewReadiness.status=in_review`，因为合法状态仅包括 `blocked`、`not_ready`、`ready`、`ready_with_risks`。已停止归档，改用 `ready_with_risks` 并保留发布预检尚未在关闭后重跑的残余风险。
`RFE-ISSUE-020`（PR边界/发布证据，中）：`ai-finish` 归档后，最终状态稳定化重新生成了 `.ai/cockpit/release-digests.json` 与 `release-freeze.json`，而首次 `make check-ai-pr` 发现这两个生成文件仍未提交，按要求阻止 PR 边界检查。已停止 PR 创建，先提交归档后最终生成的 source-bound evidence，再重新执行 PR 检查。
`RFE-ISSUE-021`（发布流程/来源绑定，高）：WI-18 corrective PR #391 关闭后，主分支上的普通 `make finalize-release-freeze` 与本地 `make check-release-preflight` 可以通过，但生成的 freeze evidence 只存在本地未提交工作树；provider workflow 从远端 exact source checkout 开始，无法消费该证据。若把它直接提交，提交本身又会改变被记录的 source commit，形成自引用循环。已停止 provider publication，建立 corrective Work Item `runtime-release-freeze-evidence`，将 runtime freeze materialization 放入 exact-source provider 运行中，并保持 committed-source preflight 在 runtime release projection 之前。
`RFE-ISSUE-022`（工单初始化/流程，中）：建立 `runtime-release-freeze-evidence` 时，首次 `make ai-start ... MODE=code` 的 skeleton 因缺少 runtime 发布 intent、raw request、sources、scenario coverage 和受限写入授权而按预期 `not_ready` 停止。已补全 Contract 后重跑；不得跳过此门禁直接修改发布 workflow。
`RFE-ISSUE-023`（工单契约/流程，中）：runtime corrective Contract 初稿在 declared intent 中使用了仓库 capability registry 未登记的 `release_engineering`，preflight 按预期拒绝 raw request。已改为已登记的 `ai_governance` 与 `test_automation` capability 后重跑；不得以未登记能力绕过 capability guard。
`RFE-ISSUE-024`（provider发布/依赖边界，高）：provider run `30206296217` 在新增 runtime freeze 步骤失败，原因是 `scripts/finalize_release_freeze.py` 导入 `check_supply_chain.py`，而该模块在依赖安装前需要未安装的 `cyclonedx`；未创建 tag、asset 或 Release。已停止重试，建立 corrective Work Item `runtime-freeze-bootstrap-dependency`，移除不必要的重型 import 并保留 SHA-256 结果不变。
`RFE-ISSUE-025`（工单初始化/流程，中）：为处理 `RFE-ISSUE-024` 首次 `make ai-start TASK=runtime-freeze-bootstrap-dependency MODE=code` 的 skeleton 因缺少依赖边界 intent、raw request、sources、scenario coverage 和授权而按预期 `not_ready` 停止。已补全 Contract 后重跑；不得绕过 Contract 直接修复 provider bootstrap。
`RFE-ISSUE-026`（provider发布/运行时证据，高）：provider run `30207515891` 在 exact-source checkout 的 runtime freeze 阶段失败，原因是 `finalize_release_freeze.py` 仍要求远程默认分支 HEAD 唯一可发现；该 checkout 中远程 HEAD 不可唯一发现，但 workflow 已解析并持有受控的 `RELEASE_DEFAULT_BRANCH=main`。未创建 tag、asset 或 Release。已停止发布，建立 corrective Work Item `runtime-freeze-remote-discovery`，要求将 workflow 输入显式传入并保持 exact source、clean worktree、preflight-before-projection 和 fail-closed 校验。
`RFE-ISSUE-027`（工单初始化/流程，中）：为处理 `RFE-ISSUE-026` 首次 `make ai-start TASK=runtime-freeze-remote-discovery MODE=code` 的 skeleton 因缺少具体 intent、raw request、sources、scenario coverage 和受限写入授权而按预期 `not_ready` 停止。已记录并补全 Contract；必须通过新的 preflight/checkpoint 后才能修改运行时发布代码。
`RFE-ISSUE-028`（工单契约/流程，中）：补全 `runtime-freeze-remote-discovery` Contract 后，新的 `make ai-preflight` 又按预期拒绝了不完整 schema：缺少顶层 `rawUserRequest`，`requestedOperation` 未提供 target/action/environment/effect/authorityRequired，高风险工单的 `unknowns` 为空，且 scenario 状态使用了不被门禁接受的 `planned`。已停止实现，修正为仓库支持的 Contract v2 字段和 `unverified` 状态后重新执行 preflight。
`RFE-ISSUE-029`（工单证据/流程，中）：`ai-finish` 收口阶段发现 active Summary 未同步 Contract 的 scenarioCoverage，高风险场景检查按要求 fail-closed。已停止归档，补齐四个场景及其状态/证据后重新执行完整 `ai-finish`。
`RFE-ISSUE-030`（工单证据/流程，低）：补齐 scenarioCoverage 后，`ai-finish` 的 guideline 检查发现 Summary 中一条 guideline 与 Contract 文本不完全一致（缺少 `the`），按严格证据匹配规则停止归档。已修正 Summary 原文并重新执行收口。
`RFE-ISSUE-031`（工单执行/并发流程，中）：两次无输出的 `ai-finish` 重试实际仍在后台运行，造成两个并行全量 pytest 质量进程，存在 target/Summary 证据竞争。已停止重复进程；后续必须确认无残留 `ai-finish`/pytest 后串行重试，不能把并行过程中的结果当作完整收口证据。
`RFE-ISSUE-032`（工单执行/检查脚本，低）：残留进程检查命令使用 `rg` 搜索自身命令文本，误报存在 ai-finish/pytest；随后用不自匹配的 `pgrep` 复核为空，未启动质量门。已记录并改用 bracket pattern 检查。
`RFE-ISSUE-033`（工单执行/会话边界，中）：上一 turn 的 `ai-finish` 进程跨 turn 残留，与当前重试并行运行；进程树证实为两个独立 ai-finish parent 和 pytest child。已停止旧进程树，保留当前运行，并要求后续 turn 交接前确认进程树已清理。
`RFE-ISSUE-034`（工单证据/Checkpoint，中）：完整质量门通过后，`ai-finish` 的 Agent Risk 检查发现最终 Contract 对齐后原 `before_edit` checkpoint hash 已过期，按要求阻止收口。已停止归档，须针对最终 Contract 刷新 `before_edit`/`before_finish` checkpoint 后重试。
`RFE-ISSUE-035`（工单证据/流程，低）：第二次收口的 Summary 校验拒绝了自定义 verification 名称 `focused release and workflow tests` 及非标准结果 `passed: 46 passed`；verification 必须使用注册检查项和 `passed`/`failed`/`not_run`。已删除未注册项，聚焦测试证据保留在执行记录和测试文件范围内，再重跑收口。
`RFE-ISSUE-036`（PR流程/参数，中）：归档后首次执行 `make check-ai-pr TASK=runtime-freeze-remote-discovery` 时，命令因未提供 `--base` 或 `AI_BASE_COMMIT` 按要求 fail-closed；已确认实际 base 为 `origin/main` 的 merge-base `bd65c610f59924fc0a817fbb606f87ad74ab0fb6`，后续显式传入该 base 重跑。
`RFE-ISSUE-037`（PR流程/证据，中）：显式提供 base 后，PR 边界仍拒绝未提交的计划问题记录；已将 RFE-ISSUE-036 提交到同一 Work Item 分支，再次通过 `check-ai-pr`。
`RFE-ISSUE-038`（provider发布/依赖等待，高）：发布 run `30209749886` 在 exact-source freeze、preflight、projection、lockfile 等步骤全部通过后，因等待同一 source `bf2d930f…` 的 smoke run 超过 900 秒而 fail-closed；compatibility 已成功，smoke 仍在执行。未创建 tag、Draft Release 或资产。根因是 release 依赖等待窗口短于允许运行 30 分钟的质量 job；已停止发布，建立 corrective Work Item `release-smoke-dependency-timeout`。
`RFE-ISSUE-039`（工单初始化/流程，中）：建立 `release-smoke-dependency-timeout` 时，首次 `make ai-start ... MODE=code` 的 skeleton 因缺少 intent、raw request、sources、scenario coverage、具体验收和授权而按预期 `not_ready` 停止。已补全 Contract，必须重新通过 preflight/checkpoint 后才能修改 release workflow。
`RFE-ISSUE-040`（工单契约/流程，低）：补全 `release-smoke-dependency-timeout` 的 `declaredIntent` 后，preflight 仍按要求拒绝 Contract，因为顶层 `intent.problem/constraints/rationale` 仍为 skeleton 空值。已补齐三项实质 intent，再重新执行 preflight/checkpoint。
`RFE-ISSUE-041`（工单收尾/流程，低）：`make ai-finish TASK=release-smoke-dependency-timeout` 首次在场景覆盖检查失败，因为重写 Summary 时遗漏了 `scenarioCoverage` 字段。已补齐与 Contract 一致的四个场景，需重新执行 finish。
`RFE-ISSUE-042`（CI效率/流程，中）：PR #395 的 compatibility 工作流包含 6 个 Python 平台任务，均重复执行完整 `make quality`，最长约 13 分 41 秒；template-smoke 又重复执行完整 `make quality`，总耗时约 21 分 45 秒。当前无失败且所有门禁均通过，因此本次不削弱或绕过门禁；已建立 `record-quality-gate-latency` 记录工单，将优化方案留给本计划完成后的统一评估。
`RFE-ISSUE-062`（CI 质量门编排，高）：PR #398 的 6 个 Python platform matrix job 以及 template-smoke 都执行完整 `make quality`；GitHub Actions API 显示所有未完成 job 的当前步骤均为 `Run make quality`。本地单次全量质量门约 6.5 分钟，重复执行造成发布反馈极慢，且缺少阶段级超时/心跳，无法解释或阻止上一轮长达两天的等待。当前候选 PR 暂不合并；先建立独立 CI 流程 Work Item，将全量门禁收敛为单次权威执行，平台矩阵改为轻量兼容性测试，并保留 job/step timeout 与失败证据。
`RFE-ISSUE-074`（PR 工单闭环/恢复例外，中）：PR #401 的已归档 Draft 修复只有把 candidate 推进到 v0.5.45 才能通过，但第二个、经用户授权的恢复工单被“单工单 PR”和 baseCommit 规则共同拒绝。恢复规则只允许一个相邻 pair：前序 Contract source 引用、人类批准、Start Receipt、Git 祖先关系和连续 archiveSequence 缺一不可；其他情况 fail closed。
`RFE-ISSUE-075`（PR 修复交付顺序，中）：将上述门禁修复本身作为第三工单归入 #401，会把受限 pair 扩成三工单，正确地继续被拒绝。修复必须先在独立的一工单 PR 中完整 merge/close；#401 再基于该新主线重整，仅保留被授权的恢复 pair。该顺序避免以放宽门禁来解决门禁循环。
`RFE-ISSUE-076`（质量门失败顺序，高）：独立恢复门禁工单的 `make ai-finish` 运行 560895ms 后才报告 quality failure；coverage 为 85.08%，installer/critical coverage/CI evidence shell 回归均通过，真正失败是 `mypy` 在 `scripts/ai_check_pr.py:283` 的参数展开错误。由于旧的并行质量图同时运行长 pytest 与静态门，静态错误被长测试拖延；必须先运行静态阶段，再运行全量测试。
`RFE-ISSUE-077`（质量门证据/发布前顺序，高）：`ai_finish` 只保留每项命令输出前 500 个字符，导致失败尾部不可见；远端 #401 又先运行约 20 分钟质量门，之后才在秒级 `check-release-distribution` 发现 v0.5.44 candidate 已被 immutable Tag 保留。已将质量门改为静态/测试/证据阶段，并把 release candidate preflight 前移；后续必须验证阶段日志、失败尾部和单一 full-quality owner，禁止盲目重复全量运行。
`RFE-ISSUE-078`（质量门兼容性，中）：阶段化 Make 编排首次执行证据门时，`check-ai-system-invariants` 将 Make 配方中的长参数形式误识别为文档中的缺失目标。并行参数改为短参数形式，保留并行阶段语义，同时满足目标引用扫描规则。
`RFE-ISSUE-079`（工单收口顺序，中）：`ai-finish` 的质量门已通过，但最终 AI 风险检查拒绝了过期的 `before_edit` checkpoint，因为契约在该 checkpoint 后又发生了必要的验收更新。收口前必须在契约最终稳定后刷新全部 required checkpoint，再执行最终 finish。
`RFE-ISSUE-080`（发布预检范围，高）：PR #402 的 `template-smoke` 在质量门前 57 秒失败，日志明确显示 `next-release.json` 仍为已被 Draft tag v0.5.44 占用的候选版本。严格候选校验不应妨碍不修改发布文件的普通 PR；已改为按 PR diff 识别发布文件，发布相关 PR 仍 fail closed 并先于质量门检查。
`RFE-ISSUE-081`（工单依赖/质量门，高）：独立发布预检范围工单从当前 `origin/main` 执行完整质量时，在 434987ms 后暴露了尚未合并的 #402 mypy 修复，说明该流程修复不能先于 #402 独立合并。已将预检范围修复回填到 #402 的既有 workflow/测试范围，避免拆出无法通过基线质量门的依赖环。
`RFE-ISSUE-082`（发布预检语义，高）：按 diff 关闭候选模式后，普通 PR 仍因 `release.json v0.5.42` 与远端 Draft tag v0.5.44 的公共身份不一致而失败；普通 PR 不应执行发布合同检查本身。现仅对发布文件 PR 执行合同检查，普通 PR 显式记录“不适用”后进入质量门。
`RFE-ISSUE-083`（文档质量门，中）：远端全量测试在 20 分 20 秒完成、覆盖率 85.02%，但新增 RFE-080 行使用了文档检查禁止的中文术语，触发日语风格门并造成 3 个失败。已改用符合现有术语规则的中文措辞，必须重新通过文档元数据和系统不变量检查。
`RFE-ISSUE-084`（工单分支/流程，中）：发布准备工单初始在 `main` 上启动，`ai-finish` 按规则拒绝在仓库基线分支归档。已停止收口并转移到专用 Work Item 分支；后续所有工单在启动后必须先确认当前分支不是默认基线，再进入实现/finish。
`RFE-ISSUE-085`（操作策略/流程，低）：为拆分“发布准备”和“外部发布”而临时声明 `repository_release_preparation.validate_and_record`，但现有策略没有该操作，preflight 正确拒绝。已改用既有 `repository_governance.modify`/`document` 记录准备状态，外部发布保持 out-of-scope；若未来需要新操作类型，必须另立 corrective Work Item 修改策略、映射和测试。
`RFE-ISSUE-086`（工单分支/流程，中）：WI-21 通过 `ai-start` 生成 Contract 后仍停留在 `main`，实现变更因此先出现在基线工作树。已停止继续修改并切换到 `codex/quality-gate-performance-completion-20260727` 专用分支；后续需把“启动后确认专用分支”加入 WI-21 Summary 和流程改进记录，不能在 main 上 finish、commit 或 PR。
`RFE-ISSUE-088`（供应链证据，中）：WI-21 的新增脚本和 Workflow 变更使重新计算的 `.ai/cockpit/sbom.json` 与已提交 baseline 不一致；全量 `project-test` 和 `check-sbom` 均 fail-closed。已停止收口，先将 SBOM 证据纳入 WI-21 scope，按现有 source-bound 规则重新生成并复验；不得删除或弱化 SBOM 门禁。
`RFE-ISSUE-089`（供应链/发布证据，中）：SBOM baseline 修复后，`release.json.supplyChain.sbomDigest` 仍指向旧 SBOM，`test_release_preparation_evidence_matches_local_metadata` fail-closed。已停止收口，按 source-bound 证据链更新 digest 并纳入 WI-21 scope；不修改 releaseTag、候选版本或任何 provider 状态。
`RFE-ISSUE-090`（供应链/发布证据，中）：更新 SBOM digest 后，候选 `.ai/cockpit/release-digests.json` 也与重新计算的 artifact evidence 不一致，`check_supply_chain.py release` fail-closed。已停止收口，先按候选 baseline 规则重新生成 release digests，再运行完整测试；不创建 tag 或公开资产。
`RFE-ISSUE-091`（工单证据/验收，低）：`ai-finish` 后审计发现，五个 hosted 性能场景最初只有 prose/known gap；尝试补入结构化 `hostedPerformanceEvidence` 后又被 Summary schema 正确拒绝，说明“结构化未运行证据”尚未进入正式 schema。已暂停 PR 交接，移除不受支持的字段并保留 open 状态；后续必须建立 corrective Work Item 扩展 schema/validator，不能手工绕过门禁。
`RFE-ISSUE-092`（指示追踪/归档路径，低）：WI-21 归档后，traceability manifest 仍引用 `active/...contract.json`，导致归档文件存在但检查器报路径缺失。已改为引用实际 archive Contract 路径，并要求归档/PR 前重新运行追踪检查。
`RFE-ISSUE-093`（归档证据/索引，低）：修正 WI-21 的 Summary 与 Archive Manifest 后，`.ai/work-items/archive/index.json` 仍保留旧的 Summary/Manifest digest，说明归档后手工补证据会造成三处索引漂移。已暂停 PR 交接，必须在最终 Summary/Manifest 稳定后重新生成 index 并做全量 digest 审计。
`RFE-ISSUE-094`（发布预检/流程，高）：PR #408 因 WI-21 为 source-bound baseline 对齐而修改 release evidence 文件，误进入 `AI_RELEASE_PREPARATION=1`，并在质量门前以 reserved v0.5.44 candidate 失败。已停止 PR 重跑，不修改版本或公开状态；必须先建立 corrective Work Item 修正“发布准备声明”与文件 diff 的边界。
`RFE-ISSUE-095`（CI 证据/诊断，中）：PR #408 的失败 evidence step 只记录 `template-smoke`，却声明三个 required jobs，验证器因此输出误导性的 top-level head 错误。已停止合并，必须在 corrective Work Item 中补齐 skipped/dependent job 记录、精确错误分类和回归测试。
`RFE-ISSUE-063`（工单初始化/预检，中）：CI 流程修复工单的 `ai-start` skeleton 缺少任务意图、原始请求、场景覆盖和具体验收，按要求停止在 `not_ready`。已补全 Contract，才允许进入实现。
`RFE-ISSUE-064`（工单证据结构，中）：补全 Contract 后，preflight 又拒绝不完整的 `rawRequestSource`、中风险 unknowns review 和 `pending` 场景状态。已改为完整人类请求证据、显式 unknowns review 和 `unverified` 初始场景状态，继续保持门禁有效。
`RFE-ISSUE-065`（预检授权路径，中）：CI 工单记录用户授权的选项 B 后，`ai-preflight --check` 仍将 `human_decision_recorded` 视为 blocked，没有“授权后先实现、再以真实证据闭合场景”的继续路径。已保留 Decision Evidence，严格限制为已确认的 CI 编排范围，继续以 checkpoint 和后续真实验证闭合场景，不提前伪造 verified 状态。
`RFE-ISSUE-066`（CI 兼容矩阵设计，中）：首次将完整 `tests` 集合改为无 coverage 的兼容命令后，本地试跑仍在约 30% 进度长时间运行，证明瓶颈不只是 coverage，而是全测试全集重复执行。已收敛为 35 个快速 trust/workflow 编排测试；完整测试全集仍由唯一 full-quality owner 执行。
`RFE-ISSUE-067`（质量门/格式，中）：CI 编排修复的全量测试与 coverage 通过，但 `project-format-check` 发现新增 `tests/test_ci_quality_orchestration.py` 未经 Ruff 格式化，导致 `make quality` fail closed。已停止收口，先运行 Ruff formatter，再重新执行完整 finish。
`RFE-ISSUE-068`（本地推送/重复门禁，中）：CI 编排修复后，兼容矩阵已缩短，但执行 `git push` 时本地执行层又自动启动了一次完整 `make quality`；仓库没有 `.git/hooks/pre-push`，且 `core.hooksPath` 为空，说明该重复门禁来自仓库外的执行层，而不是项目 Git hook。它与 `ai-finish` 的本地完整质量门及 GitHub `template-smoke` 形成重复，可能重新造成发布等待过长。已记录为独立流程问题：CI Work Item 只负责仓库内 workflow，不擅自删除外部执行层门禁；后续应明确“本地 finish、推送前检查、远端唯一 full-quality owner”的责任边界，并用一次端到端推送实测确认不再重复。当前不得把矩阵提速误报为完整发布提速已全部解决。
`RFE-ISSUE-069`（归档序列/分支同步，高）：已归档但尚未合并的候选发布分支在同步 #399 后，与主分支的 `archiveSequence=606` 发生冲突；归档索引、Manifest 和生成状态无法自动合并。根因是 archive sequence 在并行分支上按本地“下一号”分配，未在 PR 合并时重新校验远端权威序列。已停止候选 PR 合并，保留主分支 #399 的 606，将候选发布归档证据重新编号为 607，并重建 Manifest/索引后再进行完整 PR 验证。后续流程改进应在归档/PR 门禁中阻止“未合并 archive 使用已占用序列”，而非依赖手工合并解决。
`RFE-ISSUE-070`（预检语义/关键域误判，中）：实际 v0.5.44 发布工单已提供结构化 `authorityEvidence`，但 Critical Domain Guard 仍因 `intent.rationale` 中的普通词汇 `authorization` 而判定为高风险关键域、阻止预检；该 Guard 仅进行文本匹配，未消费结构化授权证据。已在不改变授权事实的前提下将意图表述改为 `human approval` 以通过现有 fail-closed 门禁。后续流程改进应使关键域判定优先读取 `requestedOperation` 与 `authorityEvidence`，避免靠改写语句绕过误报。
`RFE-ISSUE-071`（发布生命周期/循环依赖，高）：release finalizer 要求“无 active Work Item、干净且已同步的 main”，但将实际 provider 发布放入 active 发布工单的验收，会使该工单无法在 finalizer 前 archive/merge/close，从而与发布顺序形成循环。已停止在 active/dirty 工作树中尝试 publication；当前工单只闭合 v0.5.44 发布授权、前置验证和可执行发布记录，完成 PR/merge/close 后才在无 active Work Item 的同步 main 上执行 finalizer、preflight 与 provider publish，并立即建立发布后验证工单记录公共证据。后续应把“发布授权/准备、无 active main 上的外部执行、发布后公共证据”建模为明确且可审计的三个阶段，而非让一个 Work Item 同时承担互相冲突的状态。
`RFE-ISSUE-072`（Provider API/PR 创建，中）：发布准备分支已成功推送，但首次 `gh pr create` 的 GitHub GraphQL 请求返回 HTTP 499，且查询确认没有创建 PR。已停止假设创建成功；保留已推送提交，记录 provider API 失败，再使用最小的 PR 创建命令重新尝试。不得因远端请求错误跳过 PR 或改为本地合并。
`RFE-ISSUE-043`（工单契约/流程，低）：`record-quality-gate-latency` 首次 preflight 拒绝了未登记的 `requestedOperation.effect=record` 组合；已按既有策略改为允许的 repository governance modify/enforce 组合，并重新执行 preflight。
`RFE-ISSUE-044`（发布后验证/边界，高）：v0.5.43 已成功公开发布后，`make check-release-distribution` 仍读取仓库历史 `release.json` v0.5.42，并因最高公开 Tag 为 v0.5.43 而 fail closed；这暴露了发布前候选验证与发布后公开验证共用入口、却没有区分权威来源的流程缺口。已停止将该失败误报为发布失败，建立 corrective Work Item `release-distribution-post-publish-20260727`；新增显式 post-publication 验证入口，以公开 Tag/Release 资产为权威，同时保留 source/tag/asset/checksum/SBOM/provenance/installer 门禁。修复完成并重新验证前，WI-18 发布后证据不得声明完整。
`RFE-ISSUE-045`（发布/安装器一致性，高）：真实 `make check-release-distribution-post-publish` 进一步验证发现，v0.5.43 公开 Tag 的 `release.json` 仍声明 v0.5.42，Quick Install 因 `release tag mismatch` fail closed；发布前 workflow 使用运行时工作树 projection 验证，未验证创建后的不可变 Tag 树和公开安装路径，导致无效 Release 仍被公开。不得修改既有 v0.5.43 Tag；必须先修正发布流程，使运行时 release projection 作为公开 Release metadata asset 绑定并让安装器在 Tag metadata 与 ref 不一致时验证该 asset，同时增加“创建 Tag 后再验证公开安装器”的门禁。修正后需通过独立 corrective Work Item 的完整 PR/merge/close/分支清理流程，并发布新的有效版本后才能关闭 WI-18。
`RFE-ISSUE-046`（工单收口/ownership，低）：`release-distribution-post-publish-20260727` 新增 `tests/test_quick_install_release.py` 回归测试后，首次 `ai-finish` 发现该文件未在 Contract scope 中，按要求停止归档。已补齐 scope ownership，重新执行收口。
`RFE-ISSUE-047`（供应链/发布元数据耦合，中）：为让 Quick Install 使用公开 metadata asset，初步修改 `install.sh` 后，既有 v0.5.42 `release.json.installerDigest` 与供应链 provenance 立即失配，导致发布准备测试 fail closed。已撤回 installer 修改，不改写历史 metadata；改为在现有 verifier 中自动推导公开 metadata asset URL，保留 installer digest 基线不变。
`RFE-ISSUE-048`（PR边界/证据顺序，低）：本 corrective Work Item 首次执行 `make check-ai-pr` 时，归档 Contract/Summary/Manifest、Decision Evidence、start receipt、status 和 archive index 仍未提交；PR 边界按要求拒绝不洁工作树。已记录并按规范先提交本工单全部生成证据，再重新执行 PR 检查。
`RFE-ISSUE-049`（CI/发布准备边界，中）：PR #397 的 `template-smoke` 使用 `AI_RELEASE_PREPARATION=1` 时，检查器错误地将历史 `release.json` v0.5.42 与公开最高 tag v0.5.43 比较，未使用合法的 `next-release.json` 候选 tag，因而在发布修复 PR 上错误失败。已停止合并，先修正准备模式以候选 tag 判断 next-patch，并增加历史 projection/公开 candidate 回归测试；修正后必须重新通过完整 PR CI，不能把该失败当作 v0.5.43 有效发布证据。
`RFE-ISSUE-050`（归档证据完整性，中）：PR #397 的新一轮完整质量门发现，补充 RFE-ISSUE-049 到已归档 Summary 后，仅更新了 Archive Manifest digest，遗漏同步 `.ai/work-items/archive/index.json` 的 Summary/Manifest digest；同时修复代码未先运行项目 formatter。质量门 fail-closed 阻止合并，已先同步三处归档 digest 并格式化相关 Python 文件，再重新验证。
`RFE-ISSUE-051`（工单初始化/预检，中）：建立 `publish-corrected-release-20260727` 时，`ai-start` 按预期以 `not_ready` 停止，原因是初始 Contract skeleton 缺少候选 v0.5.44 的 intent、rawUserRequest、发布元数据来源、验收、风险场景和授权边界。已停止修改 release metadata，先补全 Contract 和用户已授予的“连续执行但不绕过门禁”授权，必须重新通过 preflight/checkpoint 后才能继续。
`RFE-ISSUE-052`（预检流程/用户授权，中）：补全 Contract 后，预检正确降级为 `needs_human_confirmation`，并已记录用户授权的结构化 Decision Evidence（选项 B：仅继续候选准备）；但 `ai-preflight --check` 将 `human_decision_recorded` 仍视为 blocked，没有“用户已授权、先实现再以真实证据闭合场景”的继续路径。该问题与 WI-08/WI-09 已记录的授权路径缺口同类；本工单保留该 fail-closed 证据，严格限制为候选 metadata/evidence 准备，不执行外部发布或绕过其他门禁。
`RFE-ISSUE-053`（发布候选 progression，高）：候选校验只允许 `next-release.json` 紧跟历史 `release.json` v0.5.42，因而拒绝跨过已确认无效公开 v0.5.43 的纠正版本 v0.5.44。已停止候选证据生成，扩展当前 corrective Work Item scope；流程必须允许候选紧跟已 quarantine 的最高公开 tag，同时保留 `basedOnReleaseTag`、历史元数据和 post-publication 公共安装门禁，修复后重新验证。
`RFE-ISSUE-054`（工单执行顺序，低）：candidate finalizer 在候选 Contract/metadata/validator 变更尚未提交时按要求 fail closed，提示 worktree must be clean。已记录并调整顺序为：先提交候选准备变更，再运行 finalizer 生成 source-bound freeze/digest，最后提交生成证据。
`RFE-ISSUE-055`（工单契约/ownership，低）：candidate finalizer 进一步发现 Contract 未声明其会更新的 `release.json` 生成路径，按要求停止而未写入证据。已补充 `release.json` 到 Contract scope，保持历史 v0.5.42 身份不变后重跑。
`RFE-ISSUE-056`（发布 preflight 顺序，中）：candidate freeze 生成后，在 active Work Item 尚未 archive/merge/close 时执行 `check-release-preflight`，按要求拒绝 active Work Item 和未完成 post-close lifecycle。已保留 fail-closed 结果；candidate Work Item 先完成 finish/PR/merge/close，之后再执行 WI-18 的 post-close finalizer/preflight。
`RFE-ISSUE-057`（质量门/版本事实，中）：candidate promotion 后，distribution 文档与 release workflow 回归测试仍硬编码已 quarantine 的 v0.5.43，导致完整质量门拒绝。已改为验证历史 projection、未发布 candidate 与 `basedOnReleaseTag` 的结构性不变量，并在文档中描述历史版本与纠正候选的关系，不绑定当前候选号。
`RFE-ISSUE-058`（工单 ownership，低）：`ai-finish` 发现上述两个已修改路径未真正写入当前 Contract scope，按要求停止归档。已补齐 Contract 与 Summary 的路径归属，未绕过 ownership 门禁。
`RFE-ISSUE-059`（Checkpoint/Contract 一致性，中）：补齐 scope 后，全量质量门虽通过，但 `check-ai-agent-risk` 发现历史 `before_edit` checkpoint 的 Contract hash 和 unknownCount 已过期。已停止归档，先刷新与最终 Contract 对齐的 checkpoint，再重新执行 finish。
`RFE-ISSUE-060`（Summary/生成证据 ownership，低）：全量质量门和 AI risk 通过后，`check-ai-change-summary` 拒绝 Summary 仅用 `.ai/decisions/**` 表示 4 个实际生成的 request/evidence 文件。已停止归档，改为逐个列出实际路径后重试。
`RFE-ISSUE-061`（PR 检查命令用法，低）：首次调用 `make check-ai-pr ... --base <sha>` 被 make 当作未知选项拒绝；已确认该目标通过 `AI_BASE_COMMIT=<sha>` 变量接收基线，后续按 Makefile 接口重跑。
`RFE-ISSUE-062`（CI 质量门编排，高）：PR #398 的 6 个 Python platform matrix job 以及 template-smoke 都执行完整 `make quality`；GitHub Actions API 显示所有未完成 job 的当前步骤均为 `Run make quality`。本地单次全量质量门约 6.5 分钟，重复执行造成发布反馈极慢，且缺少阶段级超时/心跳，无法解释或阻止上一轮长达两天的等待。当前候选 PR 暂不合并；先建立独立 CI 流程 Work Item，将全量门禁收敛为单次权威执行，平台矩阵改为轻量兼容性测试，并保留 job/step timeout 与失败证据。
`RFE-ISSUE-111`（预检状态转换/流程，高）：深度性能工单再次证明，中高风险 code Contract 的必需场景只有在实现后才能实测时，`unverified` 会令 enforced Preflight 返回 `needs_human_confirmation`；记录匹配的人工 Decision Evidence 后又进入同样被停止的 `human_decision_recorded`，而提前声明 `verified` 会伪造证据。已暂停性能实现，建立前置 corrective `preflight-planned-scenario-transition-20260728`：仅当每个待验证必需场景都具有非空 expected 与具体 `verificationPlan` 时允许进入实现，并明确输出“planned, not verified”；Summary Scenario Coverage Guard 与 `ai-finish` 仍在真实证据缺失时 fail closed。
`RFE-ISSUE-112`（工单启动原子性/流程，高）：复现 RFE-ISSUE-111 时，`ai-start` 在创建新工单前尝试刷新 stale no-active status，刷新后仍发现生命周期不一致并拒绝启动，却把修改后的 `current_status.md` 留在工作树中。已在同一 corrective 中为旧状态做 byte-for-byte 快照；后续校验失败或异常时恢复旧文件，新创建的状态文件则删除，并增加“恢复旧文件”和“移除新文件”回归测试，确保失败启动不遗留治理状态。
`RFE-ISSUE-113`（日语流程文档漂移，中）：corrective 文档反查发现英文运行说明与实际策略均为默认 enforced，但日文 `.ai/cockpit/README.ja.md` 仍称默认 advisory，且遗漏 `human_decision_recorded` 停止状态。已在 corrective 内对齐日文说明，明确 enforced/advisory 边界以及 Planned Scenario Verification 只授权实现、不构成完成证据，并同步英文说明与两份 glossary。
`RFE-ISSUE-114`（收口/格式门禁，低）：corrective 首次 `ai-finish` 在 `quality-fast` 的 `project-format-check` 即停止，四个 Python 变更未符合 Ruff formatter；长测试尚未启动。已运行项目 formatter、重新通过 80 项聚焦回归，并刷新当前 Contract 对应的 checkpoint 后重跑完整 finish，不复用失败运行。
`RFE-ISSUE-115`（临时 worktree/Make 变量传播，中）：corrective 第二次 `ai-finish` 以命令行 `AI_PYTHON=<absolute-python>` 启动，GNU Make 将该 command-line override 通过递归 Make 传播到全量测试，导致唯一失败 `test_nested_make_keeps_bytecode_suppression_when_ai_python_is_in_environment` 观察不到 Makefile 应构造的 `PYTHONDONTWRITEBYTECODE=1`；其余 1217 项通过且 coverage 85.02%。这不是产品逻辑失败，而是错误的 worktree 调用接口。后续改用 `PYTHON=<absolute-python>`，由 Makefile 统一派生 `AI_PYTHON`，并重新运行完整 finish；临时 worktree 流程不得再以命令行覆盖内部 `AI_PYTHON`。
`RFE-ISSUE-116`（归档后状态诊断/流程，中）：PR #412 对应 corrective 完成 `ai-finish` 与归档后、提交归档证据前，`check-ai-status-consistency` 把尚未提交的同任务 start receipt 视为 live no-active change；生成器按设计记录 0 个 transient changes，因此检查失败并建议 `repair-ai-status`，但 repair 会重复同一结果。已确认唯一 live path 为该 start receipt。前置 corrective `no-active-archive-status-diagnostic-20260728` 仅在当前 change set 同时包含同任务 archived Contract、Summary、有效 manifest 和 index 更新时，将 receipt 归入同一 archive transaction；孤立、历史-only、不完整、manifest 不匹配及无关变更继续 fail closed，并以 archive 前提交/提交后场景回归。

### WI-19：Clean Execution Plan Documents（最终工单）

**范围：** 盘点旧执行计划、重复计划、已完成计划、过期命令/版本/路径引用；仅清理已确认不再承担当前指令的执行计划文档，统一加入 `Historical Record / Not Current Product Documentation / Do Not Use As Runtime Instruction`，保留 archive-backed 索引、状态、来源和替代文档。

**验收：** 当前主计划、WI-15 最终问题总览、WI-16 日语评估证据、WI-17 Trust Layer 对齐证据、WI-18 发布证据、所有 active/archived Contract/Summary/Event/Manifest 仍可追溯；无文档引用已删除命令或过期版本；清理 diff 有 inventory、理由、替代、digest 和恢复路径；多语言/README/索引对齐通过。

**强制顺序：** 这是最后一个整改 Work Item。完成其 PR、merge、`make ai-close-work-item`、本地/远端分支清理和默认分支同步后，生成最终对齐报告，提交给用户确认；此前不得宣称“全面整改完成”。

### WI-20：Quality Gate Performance Architecture（当前新增工单）

**插入原因：** 当前追踪机制工单的 CI 验证进一步证明 `template-smoke` 的完整质量路径约需 23 分钟；用户随后要求在当前工单完成后插入《AI Cockpit make quality 与 GitHub Actions 性能优化》工单。该工单优化重复执行和可观测性，不以删除检查换取速度。

**范围：** `make quality-fast`、`make quality-full`、`make quality-release` 与兼容入口；pytest、Supply Chain、PR、Bandit 和 Workflow 去重；Gate Runner/Timing/Summary；scope 判定；安全并行和输出隔离；quality/installation/release-evidence Workflow 职责；缓存边界；相关测试和中英日文档对齐。

**强制边界：** 不降低 Coverage，不删除 SBOM、Provenance、credential-policy scanning、漏洞、安装或 Release Evidence；不把缓存当作最终证据；未知 scope 默认 Full；不修改 Branch Protection；不发布版本。

**验收：** 必须有真实 Gate timing 和日志证据、去重调用图、失败/超时证据、并行冲突测试、缓存安全测试、Workflow ownership 测试、至少五类场景的重复前后测量，或对未执行场景给出结构化原因。`quality` 必须仍等价于 `quality-full`，Release Full 必须完整；同时必须通过“指示—计划—实现—验收”的双向追踪检查，并将所有遗漏记录、修正、复验后才能关闭。

## 四、问题记录与流程纠偏机制

每个 Work Item 必须维护结构化问题记录，至少包含：`issueId`、`workItemId`、发现时间/阶段、问题类别（gap/defect/evidence/security/installer/release/process）、严重度、事实与证据引用、已知/未知、停止状态、风险、决策、解决动作、验证结果、残余风险、是否需要人工确认、是否触发流程 corrective Work Item。

问题状态只能通过追加事件推进，不得静默改写历史：`observed → triaged → blocked/accepted/in_progress → resolved/mitigated/unresolved`。如果验证后再次出现，建立新的 finding fingerprint，不覆盖旧问题。

若发现流程问题：

1. 立即停止当前 Work Item 的 PR/merge/release/cleanup 动作。
2. 在当前 Summary 和事件中记录流程根因、证据路径、受影响阶段和安全停止点。
3. 创建 corrective process Work Item，明确它是当前项的前置依赖；先走完自身完整生命周期。
4. 修正流程、Make target、guard、schema 或文档后，重新运行原 Work Item preflight；旧证据过期时必须重跑，不得复用。
5. 在原 Work Item 中记录恢复依据、修复前后差异和新验证结果。

## 五、每项完成后的文档对齐检查

每个 Work Item 关闭前，都必须执行以下检查并写入 Summary 的 `documentationAlignment`：

- 本计划中的工单边界、顺序、状态和完成证据是否仍与实现一致。
- Contract、Summary、Task Outcome、Cockpit Status、PR Summary 是否来自同一事实源。
- 相关 README、指南、架构、命令示例、Make target、版本/ref/path、环境变量和 Capability claim 是否与代码和测试一致。
- `README.md`、`README.ja.md`、`README.zh-CN.md` 的 North Star、产品边界、安全限制、人工确认、安装/校准、支持范围和版本语义是否同步。
- 新增限制、未知、未验证场景、剩余风险和人工决策是否被文档诚实表达。
- 历史内容是否已标记为历史；若未到 WI-19，不得删除历史执行计划。

检查失败时，当前 Work Item 不得报告 ready/closed；先完成文档对齐、重新验证，再进入 PR 或关闭阶段。

## 六、计划自检与当前停点

### 指示覆盖

- 安装流程、校准流程、对象工程可用性：WI-03、WI-04。
- 荒诞测试、Prompt Injection、未知/人工确认、幻觉：WI-02、WI-05、WI-06。
- Work Item 正确性、执行效率、Task Outcome：WI-07、WI-08、WI-09。
- 文档/代码对齐、企业治理边界、代码质量、过期资产、治理证据压缩：WI-10 至 WI-14。
- Canonical Evidence 与事实源统一：WI-01，并贯穿全部工单。
- 五个实施阶段：WI-01/WI-02 为事实源与边界；WI-03/WI-07 为安全与流程；WI-04 为对象工程验证；WI-08/WI-13 为效率与干净化；WI-09/WI-10/WI-14 为信任结果展示。
- 结束项：WI-15 全面验收，WI-16 日语能力评估，WI-17 Human-Agent Trust Layer 对齐，WI-18 发布新版本，WI-19 清理执行计划文档。

### 计划质量检查

- 无未定义的“以后补充”步骤；每个 Work Item 有明确范围、验收和验证方向。
- 未把任一 fixture、模板能力、测试通过、计划完成或用户授权自我声明成产品事实。
- 所有后续工单均有串行 predecessor、PR、archive、close、分支清理和 base 同步要求。
- 所有工单（包括后来插入的工单）都必须通过“指示→计划→实现→验收”和“验收→实现→计划→指示”的双向追踪检查；任一方向缺证据即视为遗漏，必须先记录并修正后再进入 PR/合并/发布。
- 任何流程问题都有先纠偏、再恢复的明确路径。
- 用户已经授权：本次计划文档的收查、确认、总结、工单拆解、PR/清理流程设计、问题记录机制和文档对齐机制。
- 用户已授权：按本计划连续执行后续整改工单、创建专用分支/PR、完成合并/归档/关闭/分支清理/base 同步，并在发布前执行日语能力评估与 Trust Layer 对齐；不得绕过门禁。发布新版本和最终清理计划文档仍分别受 WI-18/WI-19 的专用验收与发布边界约束。

### 当前执行状态

更新时间：2026-07-29。用户已授权连续执行；遇到流程问题必须先记录并纠偏。

| 阶段 | 当前事实 |
| --- | --- |
| 深度性能工单 | 已完成、合并、关闭并清理 |
| WI-10 安装文档整改 | 已完成、PR #422 已合并、关闭并清理 |
| WI-01～WI-20 双向追踪审计 | 已完成；发现项及 corrective 均按 archive 追踪 |
| 其他流程问题与 RFE-ISSUE-082 | 已完成、合并、关闭并清理 |
| 日语评估及整改 | 文档事实纠偏已由 PR #452 合并并完整关闭；随后发现的 `JA-DOC-FACT-002` 也已由 PR #454 合并、关闭并清理 |
| 日语校准证据文档纠偏 | 已完成；三语 Session 七列证据、Work Item 治理边界及 reviewer/owner 标签限制已对齐，并由机器检查防止复发 |
| 全新日语最终评估 | `japanese-final-reassessment-after-documentation-truth-20260729` 已完成；PR #455 全部 Hosted 检查通过、已合并、关闭并清理 |
| GitHub Actions 警告纠偏 | `github-actions-warning-corrective-20260729` 已完成、合并并清理；接收 Dependabot #443，并以 workflow 回归和精确 Head Hosted 日志验收 Node/Go/Homebrew 三类警告消失 |
| RFE-ISSUE-093/094 候选发布证据与检查点纠偏 | `rfe-094-checkpoint-enforcement-20260729` 已完成、合并、关闭并清理 |
| RFE-ISSUE-096 恢复后验证证据代际纠偏 | `rfe-096-resume-verification-generation-corrective-20260729` 已完成、合并、关闭并清理；RFE-094 关闭后恢复 #441 时，旧 Summary 验证记录被 canonical before_edit 误计为当前通过项。RFE-096 以最新可信 `resumeHistory.recordedAt` 划分代际，RFE-095 脏调查现场保留但不合并。 |
| RFE-ISSUE-097 工单完结报告纠偏 | `rfe-097-mandatory-task-outcome-report-20260729` 已完成、合并、关闭并清理；其后发现“Outcome 仅存文件、而非归档前对话报告”这一未闭环行为。successor `rfe-108-prearchive-outcome-successor-20260730` 已完成、PR #467 合并、关闭并清理：默认 `ai-finish` 只生成并直接呈现 active Outcome，归档必须显式执行；RFE-104 归档未合并证据与 PR #464 保持只读审计状态。 |
| Dependabot 发布前接收 | `dependabot-441-setup-dotnet-20260730` 已由 PR #468 合并、关闭并清理；当前执行 `dependabot-442-ruby-setup-ruby-20260730`，从最新 main 重建 #442 的 ruby/setup-ruby 1.321.0 pin 并收集当前代际验证。其后 #444、#445 各自按独立 Work Item、PR、Hosted、merge、close、分支清理流程接收。 |
| 文档对齐 | `pre-release-documentation-alignment-20260729` 已暂停；待纠偏和全新日语评估关闭后 rebase/resume 并完成 |
| 发布前过期资产清理 | 待文档对齐关闭后执行 |
| 发布前真实荒诞与注入攻击评估 | 用户新增；待过期资产清理关闭后执行三语 12 案例评估及必要整改 |
| 发布前最终日语复验 | 后续任何 Capability Truth、计划或日语权威源变更都会使既有精确源报告过期；所有发布前修改关闭后必须再生成一次零 blocker 的 `final_reassessment` |
| WI-18 发布新版本 | 待所有前置阶段关闭；候选版本、provider Release、tag、asset、projection 分别验证 |
| WI-19 清理计划文档 | 发布完整关闭后最后执行 |

当前唯一允许的顺序是：GitHub Actions Node/Go/Homebrew 警告纠偏并接收 #443 → RFE-ISSUE-093/094 检查点与候选发布证据纠偏 → RFE-ISSUE-096 恢复后验证证据代际纠偏 → RFE-ISSUE-097 强制 Task Outcome 与 Closure Receipt → RFE-108 归档前 active Outcome 直接对话报告 successor → 恢复并完成 #441 → 分别接收 Dependabot #442、#444、#445 → 以最新 `main` 重做 #403 的计划完成证据审计并关闭旧 PR/分支 → 按用户最新反馈重构三语安装文档的信息架构 → 恢复并关闭文档对齐 → 过期代码/逻辑/文档清理 → 三语真实荒诞与注入攻击评估及整改 → 对全部最终源再做一次零 blocker 日语 `final_reassessment` → WI-18 发布 → WI-19 清理当前周期计划。每一项都必须完成 Contract → Preflight → 实现/验收 → `ai-finish`/archive → push → PR → merge → `make ai-close-work-item` → 本地/远端分支清理 → main 同步；不得从 detached closed worktree 直接进入下一项。

### 本计划工单已发现的问题

- `RFE-ISSUE-096`（恢复流程/验证证据代际，高，处理中）：RFE-094 完整关闭后，#441 按规则 rebase/resume，但 active Summary 保留了上一轮验证记录。canonical `before_edit` 未按最新 `resumeHistory.recordedAt` 隔离证据代际，因而把旧记录计为已通过；完整质量结束后 agent-risk 才拒绝该 checkpoint。首次 RFE-095 调查正确识别时间边界，却扩展出未经要求的 `contractRevisionHistory`、未来时间证据和新修订状态机，已停止且保留现场。干净 RFE-096 replacement 只实现共享的最新恢复点过滤、malformed timestamp fail-closed、五类回归和三语流程说明，完整关闭后才再次恢复 #441。
- `RFE-ISSUE-097`（用户可见完结报告/流程，高，处理中）：RFE-096 的 Contract、Summary、PR、Hosted CI、归档和 closure 均完整，但 `scripts/ai_finish.py` 将 Task Outcome 绑定在可省略的 `taskOutcomeInput`，使 archive 不能保证有可读 Outcome，关闭命令也不生成面向用户的合并/清理收据。RFE-097 仅将 Outcome 改为 pre-merge 强制派生、将 Closure Receipt 放在 merged PR 与 base 同步验证后、分支删除前，并以缺失/无效 fail-closed 回归防复发；不回填或改写历史 archive。
- `CI-WARN-001`（GitHub Actions 依赖/日志质量，发布前必须纠偏）：PR #454 smoke 的 `actions/upload-artifact@ea165f8...` 仍基于 Node.js 20；main push run `30421167605` 的两个 Go fixture Job 因仓库根目录不存在 `go.mod` 而产生无效 cache restore 警告；Swift macOS Job 在安装 `swift-format` 时读取 runner 预置、未信任且本 Job 不需要的 `aws/tap`。独立 corrective 必须升级并固定 Node 24 artifact action SHA，为两个临时 Go fixture setup 显式关闭缓存，只在存在时移除无关 `aws/tap`，禁止用全局关闭 Homebrew trust 的方式压制告警；本地 workflow 测试和精确 PR Head Hosted 日志都必须证明三类告警消失。
- `DEPENDABOT-INTAKE-001`（依赖更新/发布前，高）：用户要求发布前接收开放的 Dependabot PR。#443 与 `CI-WARN-001` 完全重叠，由当前 governed replacement 接收；#441 setup-dotnet、#442 setup-ruby、#444 stevedore、#445 ruff 必须在其后分别从最新 `origin/main` 建立独立 Work Item，重建 lockfile/兼容证据并完成 Hosted 验收。旧 PR 上的失败或成功不得直接当作当前主线证据。
- `CI-WARN-JA-001`（发布顺序/精确源证据，高，已纠偏）：当前警告工单首次完整质量证明，PR #455 的日语 `final_reassessment` 会在后续 Capability Truth 或主计划字节变化后按设计失效；因此“日语最终评估完成后继续修改再直接发布”的顺序不成立。当前工单先使用 canonical evaluator 刷新本次 source-bound 日语证据以恢复质量门，同时把真正的发布前最终日语复验移动到所有 Dependabot、文档、过期资产和攻击整改关闭之后、WI-18 之前；任何最后变更仍须重新复验。
- `JA-DOC-FACT-002`（日语评估/校准证据事实，高）：全新日语最终评估的独立 Accuracy 与 Clarity 策略一致确认，英中日三份安装文档的 Calibration 完成记录前段仍声称 Session 只保存回答/运行状态、其余七列由 Work Item 保存；但 `scripts/ai_calibrate.py record-evidence` 已把 observed evidence、Candidate change、owner/reviewer、PASS/STOP、reason/retry 持久化到每阶段 `checklistEvidence`，同一文档后段也描述完整七列记录。既有 checker 只验证宽泛 marker，未拒绝内部矛盾。最终评估已暂停；独立 corrective `japanese-calibration-session-evidence-doc-corrective-20260729` 以三语统一事实、Work Item 治理/外部证据边界、标签不证明本人性或独立角色分离及 mutation gate 完整闭环后，才允许恢复评估。
- `DOC-ALIGN-FINDING-001`～`008`（文档事实/流程，发布阻断）：五策略审查一致发现 Capability Truth 与 Quick Install 实现冲突、row digest 未绑定证据字节、日语最终报告漏绑权威文档、README 以最高 tag 回退、计划状态与生命周期顺序漂移、发布身份边界混淆、多语言路线不等价，以及对齐检查器自我声明审查成功。已暂停文档对齐，建立 `pre-release-documentation-truth-corrective-20260729` 原子修复代码、测试、三语文档和结构化审查证据；修复后必须重新执行独立日语最终评估，再恢复文档对齐。
- `DOC-TRUTH-ISSUE-001`（Preflight 词法误报，中）：纠偏 Contract 中用于报告分类和权威边界的普通词 `role` 被 Critical Domain Guard 按权限操作命中，尽管 `requestedOperation` 明确是 repository governance 且无外部权限变更。当前 Contract 用“report classification / authority boundary”精确表达后 Preflight 为 ready；该误报保留为流程问题，后续流程工单应让结构化 operation 优先于无上下文词法匹配，不能靠静默忽略。
- `DOC-TRUTH-ISSUE-002`（Capability Truth 旧证据路径，高）：首次启用证据字节绑定时，矩阵中 `tests/test_installation.py` 与 `tests/test_ci_release_evidence.py` 已不存在，但旧 row-only digest 仍为绿色。已替换为真实的 `tests/test_install_entrypoint.py` 与 `tests/test_ci_release_evidence.sh`，并以 missing-file fail-closed 回归防止再次漂移。
- `DOC-TRUTH-ISSUE-004`（Coverage 关联，中）：纠偏首次 `ai-finish` 在重测试前停止，因为 `capabilityTruth` 的既有 production→test 关联只登记 absurd corpus，未登记本次新增字节/路径回归所在的 `tests/test_capability_truth_matrix.py`。已将精确测试文件加入同一关联，扩展 Contract scope，并要求重新 Preflight、重建两个 checkpoint 后从头执行 Finish；未使用 `tests/**` 宽泛匹配。
- `DOC-TRUTH-ISSUE-005`（安全扫描器/检测实现，中）：下一次完整质量的 1480 项测试与 85.63% Coverage 均通过，但 Quality Architecture 把 Capability Truth 校验器自身用于拒绝 parent-path 的字面量识别为不安全路径。未豁免该脚本；改为对 normalized `Path.parts` 判断同一越界条件，保留 escape red test，并重新生成两个字节绑定报告后要求完整 Finish 重跑。
- `PROCESS-SKILL-ENTRYPOINT-001`（Agent Skill / Make 入口，中，已解决）：本机 `ai-cockpit` 技能曾假定根目录缺少 `Makefile.ai` 就必须停止，遗漏模板源码仓库由根 `Makefile` 直接实现 lifecycle targets 的合法形态。PR #452 关闭前探测因此先停止，但没有状态变更。已在当前生效技能中加入确定性入口解析脚本及 5 个回归场景，覆盖模板根 Makefile、reviewed include、未 include 的采用方、缺失入口和不完整直接目标，并经独立 Sol 前向测试确认模板仓库选择 `make`。
- `JA-FINAL-ISSUE-001`（本地命令构造，低，已解决）：创建全新日语评估 worktree 的首个命令使用 zsh 特殊变量 `path`，导致 `PATH` 在第一条 Git 命令前被覆盖；没有创建分支、目录或仓库变更。改用 `worktree_dir`/`branch_name` 后从 `origin/main` 精确创建并验证。
- `JA-DOC-FACT-002`（日文文档事实，高，发布阻断）：独立五策略日语复核在 `docs/getting-started/installation.ja.md` 的 Session/Work Item 保存边界处取得 Accuracy + Clarity 共识。文档称 Session 只保存回答与执行状态，但 `ai_calibrate.py record-evidence` 还持久化结构化 `checklistEvidence`（根拠、Candidate 变更、Owner、Reviewer、PASS/STOP、理由、再确认手顺）。最终评估已把该项写入 `blockingFindings` 并 fail closed；先执行 `japanese-calibration-session-evidence-doc-corrective-20260729`，补齐三语事实边界和自动回归，再 resume 最终评估。
- `PLAN-001`（流程/记录，低）：初始 Contract 使用了本机绝对路径，Summary 仍是骨架。已在本计划工单内改为可移植的用户请求来源标识，并补齐 Summary；Contract、范围、文档 metadata、Status 和一致性检查随后通过。
- `PLAN-002`（质量/发布证据，待后续工单处理）：本计划工单运行 `make quality` 时，pytest 1058 passed、coverage 85.04%、ruff/mypy/bandit/文档/系统不变量等检查通过，但 `check-release-evidence` 的 release supply-chain 检查发现 1 个问题，导致 `make quality` 退出码 2。该问题属于发布证据域，应在 WI-17 或其明确的前置 corrective Work Item 中按流程处理；本计划不绕过或修复它。
- 现有 governance complexity 与 archive growth 仅报告 warning（当前 archive growth 超过 policy warning 阈值），不在本计划工单中擅自抬高阈值；应由后续相关 Work Item 按预算/偿还规则处理。
- `PLAN-003`（流程/发布证据边界）：诊断 `check_supply_chain.py release` 时发现 `--write` 可以直接改写 `.ai/cockpit/release-digests.json` 并使检查通过，但该文件属于发布证据，不能在计划文档工单中更新。诊断性改写已恢复；后续必须由 WI-17 或明确的 corrective Work Item 按 source-bound 发布流程生成。
- `PLAN-004`（流程/候选发布证据校验，高）：PR 的 Python 兼容矩阵在所有平台重复失败，根因是候选 `release-digests.json` 的 `origin/main` 身份被按已发布标签提交进行严格比较。已在当前计划 PR 中修正候选基线校验：候选阶段只校验稳定发布契约和非身份制品，发布阶段由 `release-assets` 做精确 source-bound 校验，并补充回归测试；该修正完成后才允许合并当前 PR。
- `WI-01-ISSUE-004`（外部 CI 调度，待恢复）：WI-01 PR #365 的 compatibility 与 smoke run 在创建任何 job 前被 GitHub 标记为 “This run likely failed because of a workflow file issue”；PR diff 未包含 `.github/workflows/**`，且 rerun 后仍复现。已在 PR 记录并保留 run 证据；不得把无 job 失败误报成代码验证通过，必须恢复出可审计的 required checks 后再合并。
- `WI-05-ISSUE-004`（用户纠正/coverage，低）：用户指出安装对象工程的工程师多数使用日语，原 WI-05 边界虽覆盖 bilingual/mixed-language，但未明确日语。已在 PR #369 合并前暂停关闭动作，补充日文直接、隐藏 HTML、嵌套引用 corpus 与日文检测指示器，并将计划、安全边界文档和验证范围对齐；补丁完成后必须重新 finish 与 required CI。
- `PLAN-005`（用户纠正/流程门禁，高）：用户要求在发布新版本前插入全面日语能力评估，且日语为必需能力；任何问题必须对应 corrective Work Item 并在重新评估通过前保持ブロッキング。已将原 WI-16/WI-17 顺延为 WI-17/WI-18，新增 WI-16 Japanese Capability Assessment，并更新发布与最终清理的强制顺序；现有 PR/finish 必须先完成本计划对齐再继续。
- `PLAN-006`（用户新增/发布前门禁，高）：用户要求在发布版本前插入一个对应《Human-Agent Trust Layer》的工单。已新增 WI-17 Human-Agent Trust Layer Alignment，并将发布顺延为 WI-18、最终计划文档清理顺延为 WI-19；WI-17 必须完成证据治理、责任边界、供应链证据和人类决策压缩对齐，任何对应问题必须先完成 corrective Work Item 后才能进入 WI-18。
- `PLAN-007`（用户补充/文档一致性，高）：用户明确 WI-17 的任务为 `document_human_agent_trust_layer`：升级现有 `docs/trust-layer.md` 为英文权威完整文档，新增完整中文/日文版本，保留现有 Gate/命令/Archive Manifest 实现细节，补齐 Documentation Architecture、三语 README 短入口、交叉链接和轻量一致性检查；不得通过概念文档删除实现证据或从理念反推 Capability Truth。
- `WI-16-ISSUE-001`（评估流程，中）：初始日语文档 smoke criterion 对所有文档强制同一组通用词，产生职责不匹配的误报；已改为按文档职责绑定行动术语并重跑聚焦测试。
- `WI-16-ISSUE-002`（评估边界/证据，高）：当前仓库只能证明确定性的日语治理路径，不能证明通用对象工程师日语交互能力；已把后者固化为 non-claim，避免从本地测试反推通用能力。该限制仍需在 WI-17 Trust Layer 和 WI-18 发布证据中保持一致，不得删除。
- `WI-16-ISSUE-003`（流程/质量，中）：新增评估脚本首次未通过 formatter 门禁；已先格式化，再重新执行完整 `ai-finish`，最终 1147 tests、coverage 85.06% 及其余质量门禁通过后才归档。
- `WI-05-ISSUE-005`（流程/证据归属，高）：尝试以独立追加 JSON 记录 WI-05 的日语计划补正时，PR 归属门禁拒绝了该非 Contract/Summary 配对文件。该追加文件已从当前 PR 移除，计划正文保留完整问题记录；后续必须建立独立 corrective process Work Item，补充并验证“追加式 correction evidence”的归属规则后，才能使用该证据格式，不得改写已归档 WI-05 Contract/Summary。
- `WI-05-ISSUE-006`（流程/CI，待恢复）：最新 PR 提交的 `template-smoke` job 自 2026-07-25T16:41Z 起停留在 `Run repository quality gates`，其余步骤未启动，远超同类运行时长且无可用最终日志。已取消僵死 run；必须重新触发完整 CI 并取得新的可审计结论后，才能合并 WI-05，不得把取消或旧 run 当作通过。
- `WI-06-ISSUE-001`（流程/命令一致性，低）：AI Cockpit skill 文档曾列出一个当前 Makefile 不存在的旧 ownership alias；实际归属门禁为 `make check-ai-diff-ownership`。已记录并使用实际目标完成检查，后续应在流程文档对齐工单中统一命令名称，不因别名缺失绕过归属检查。
- `WI-06-ISSUE-002`（流程/coverage guard，低）：coverage guard 初始没有为新 `scripts/ai_capability_truth.py` 配置对应测试关联，导致已有 `tests/test_absurd_capability_truth.py` 被误报为缺少测试差异。已补充 `capabilityTruth` association 并通过 guard；该规则变更必须随本工单的完整 PR/归档流程审查。
- `RFE-ISSUE-073`（CI流程/可观测性，高）：PR #403 的 `template-smoke` 在 `Run repository quality gates` 进入后约 6 分钟没有任何日志更新，后续 quality/installer/template checks 未启动；run 已取消，不能视为通过。根因是质量门虽有 job-level 30 分钟 timeout，但没有 step-level bounded timeout、heartbeat 或明确的 timeout failure evidence，导致长时间不可解释等待。已建立 `ci-template-smoke-quality-timeout-20260727` corrective Work Item；先为 smoke quality step 增加 25 分钟 fail-closed timeout、逐分钟 heartbeat 和回归断言，再重新运行 #403 CI，确认新鲜可审计结果后才能合并审计工单。
- `RFE-ISSUE-074`（流程/需求追踪，高）：用户确认建立“指示—计划—实现—验收”的双向追踪机制。原因是原有单向计划执行无法机械阻止用户明确点名的既有文件（例如 WI-10 的 `docs/getting-started/installation.md`）从实现中遗漏。已建立 `instruction-traceability-gate-20260727` corrective Work Item，增加结构化 traceability manifest、fail-closed 检查器、Make target、回归测试和文档；该检查只接受显式 no-change rationale 作为已识别缺口，不将其误报为完成或解除发布冻结。
- `RFE-ISSUE-075`（流程/生命周期证据，中）：PR #405 的 CI 发现 traceability manifest 在 Work Item 归档后仍引用 active Contract，导致 clean-checkout 的追踪测试失败；同时新增 CLI 分支覆盖不足使总覆盖率为 84.94%。根因是归档生命周期的证据路径没有作为 manifest 的回归场景。已将引用切换为 archive Contract，补充“归档后 clean checkout”及 CLI 失败路径测试；修复通过后必须重新执行完整质量和 PR 检查。
- `RFE-ISSUE-076`（流程/Preflight，中）：WI-20 实现开始后，Preflight 仍将“场景尚未验证”和一个宽泛验收句作为 Human Decision Gate，未提供“先执行聚焦验证、记录未运行的 hosted 性能测量、再继续收口”的结构化路径。已记录该流程缺口，补充具体验收文本并用真实聚焦测试证据更新六个场景状态；重复 Preflight 后必须确认状态恢复为 ready，且 Summary 仍须明确记录五类重复性能测量的未运行原因，不得声称性能提升。
- `RFE-ISSUE-077`（安全/证据，中）：WI-20 新增两个使用受控 subprocess 的质量工具后，单次完整 Bandit JSON 扫描从 baseline 的 105 条低风险 finding 变为 109 条；原因是新增工具的 B404/B603/B607 低风险 finding，未发现中高风险 finding。已审阅并将 109 条当前结果以 digest 绑定写入 baseline；不得改用 `-ll` 隐藏低风险结果，也不得在后续工单重复扫描或静默漂移 baseline。
- `RFE-ISSUE-078`（流程/checkpoint，中）：WI-20 在最后补入 Bandit baseline 和测试 scope 后，`ai-finish` 正确拒绝复用旧 `before_edit` checkpoint。已刷新最终 Contract 的 checkpoint；后续任何 Contract scope/acceptance/source 变更都必须刷新 checkpoint 后再收口。
- `RFE-ISSUE-079`（流程/Summary，中）：WI-20 的实现反向检查发现 `tests/test_makefile.py` 和 `tests/test_project_governance.py` 已修改但未进入 Summary.changedFiles，`check-ai-change-summary` 正确 fail-closed。已补齐两项文件及原因；后续必须在每次测试/验证修订后重新执行 changedFiles 反向核对。
- `RFE-ISSUE-080`（流程/归档追踪，中）：WI-20 完成 `ai-finish` 后，反向追踪清单仍引用已不存在的 active Contract，clean-checkout 的 `make check-instruction-traceability` 因路径失效而 fail closed；同一缺口又在 sequence 636 的审计 Hosted recovery 中复现，并因手工迁移形成归档后、首次提交前的额外 no-active 路径冲突。根因是归档动作没有自动更新当前 Work Item 的外部追踪路径。已建立独立 corrective `archive-traceability-path-rewrite-20260728`：归档事务只原子迁移 registered manifest 中 exact current Contract path，no-reference 为 no-op、malformed 输入 fail closed、后续失败 byte-for-byte rollback，并由 archived Summary 自动记录该生成变更；完整 PR/CI/merge/close/cleanup 前不得进入 RFE-147。
- `RFE-ISSUE-082`（发布流程/事实源，高）：最新只读复核纠正了旧记录：provider 当前最高 stable GitHub Release 是 v0.5.43，v0.5.44 仅有不可变 Git tag、没有 GitHub Release；`release.json` 仍为仓库 published projection v0.5.42，`next-release.json` 却复用已占用的 v0.5.44，canonical state 的 projection digest 也已漂移。独立 replacement `rfe082-release-truth-reconciliation-20260729` 必须从最新 main 区分 Tag reservation、stable provider Release、repository projection 和 candidate，记录 v0.5.43/v0.5.44 不可复用并推进 v0.5.45；`candidate_prepared` 不得伪装绑定后来已经过期的 source SHA，最终 source/freeze/digest 只在发布 finalization 绑定。旧未合并 PR #401 及其本地/远端分支必须关闭/删除但保留 PR 审计记录，禁止 cherry-pick 或复活旧归档工单。该 replacement 完成完整 PR/Hosted CI/merge/close/branch cleanup 前不得进入日语评估或发布。
- `RFE-ISSUE-117`（流程/恢复基线，高）：性能工单在 PR #412、#413 两个强制 corrective 完整关闭后 rebase 到最新 `origin/main`，原始 Start Receipt 仍正确绑定启动基线 `f00ac8b3`，但 Contract 必须使用新基线 `f6b12629` 排除前序 corrective diff；现有校验把二者必须永久相等，且没有受治理的 resume transition，导致合法续跑被拒绝。已建立 `work-item-resume-receipt-lineage-20260728` corrective：新增原子 `ai-resume-work-item` 命令和 append-only `resumeHistory`，每一跳绑定旧/新 base、remote/default branch、原专用 branch、时间、前序 Contract digest、完整 predecessor closure、精确 merge commit 和 archive manifest；Start Receipt 永不改写，手改 base、断链、非祖先、错误 branch、未关闭 predecessor 或伪造 manifest 均 fail closed。该 corrective 必须完成 Preflight、TDD、完整质量、PR/CI/merge、`ai-close-work-item` 和分支清理后，性能工单才能通过新命令恢复并重跑全部过期验证。
- `RFE-ISSUE-118`（流程/Summary 文档对齐证据，中）：总计划要求每个 Work Item 在 Summary 写入结构化 `documentationAlignment`，但原 `ai_check_summary.py` 的允许字段集合拒绝该字段，导致“已完成对齐但无法按计划字段记录”的流程矛盾。独立 corrective `documentation-alignment-summary-schema-20260728` 已启动：当前实现要求 current v2 Summary 完整记录五个对齐域，验证 offset-aware 时间、仓库相对实存路径、changedFiles/sourcesUsed 双向声明和变更文档/命令表面的反向覆盖；ai-start、installer adoption/upgrade 与示例共用同一 skeleton，旧 archive 明确保留读取兼容且不 backfill。聚焦与扩展回归已通过；在其完整 quality、archive、PR/CI/merge、`ai-close-work-item` 和分支清理完成前，性能与发布仍保持暂停。
- `RFE-ISSUE-119`（流程/coverage association，低）：RFE-117 corrective 首次 `ai-finish` 在长测试前被 Coverage Guard 拒绝，原因是新增 `scripts/ai_resume_work_item.py` 虽已有 `tests/test_start_and_archive.py`/`tests/test_pr_aggregate.py` 回归，但未登记 production-to-test association。门禁行为正确；已把 writer 加入现有 `startReceipt` domain，刷新 Contract scope、Preflight 和 checkpoint，并要求完整 finish 从头重跑，不复用失败运行的部分证据。
- `RFE-ISSUE-120`（性能流程/证据隔离，高）：RFE-117 corrective 的真实 `project-test` 已运行约 7 分钟时，测试进程内部把同一个 `target/quality/timing/project-test.json` 临时覆盖为 17ms fixture 结果，证明 live quality 与测试 fixture 共享 timing 目录会污染中途证据。最终父 runner 虽会重写文件，但该 transient 值不得用于性能结论；已将现场证据绑定到深度性能工单，必须用 run ID/commit 隔离 timing session、流式日志和失败 artifact 根治。
- `RFE-ISSUE-121`（验证/coverage 与 Bandit，中）：第二次 `ai-finish` 的完整 pytest 为 1245 passed，但新增 resume writer 的若干错误分支未覆盖使总覆盖率为 84.95%；Bandit 同时新增 5 条低风险 B404/B603/B607（writer 的受控 list-form Git subprocess 3 条，receipt ancestry helper 2 条），无中高风险 finding。已增加 malformed JSON、predecessor closure/ID/manifest、repository boundary 负例，并在不降低阈值、不使用全局过滤的前提下将已审阅 baseline 更新为 114 条及新 digest；必须重新完整质量证明 coverage ≥85% 与 exact baseline。
- `RFE-ISSUE-122`（流程/checkpoint freshness，低）：第三次 `ai-finish` 的完整质量已通过（1247 passed、coverage 85.01%、Bandit exact 114/0 medium-high、全部 quality Gate passed），但随后 Agent Risk 因 `before_edit` 仍绑定加入 coverage policy/Bandit baseline 前的旧 Contract hash 而 fail closed；仅刷新 `before_finish` 不足。已记录该停点，必须把 Contract 声明的 `before_edit` 与 `before_finish` 两个 stage 都重建到最终 hash，再完整 finish；不得把已通过 quality 单独当作 Work Item 完成。
- `RFE-ISSUE-123`（流程/命令文档漂移，低）：RFE-118 文档验证时，PLAN-DIRECTIVE-003/005 仍要求一个已不存在的旧 document-link Make target；`check-ai-system-invariants` 随后按设计 fail closed，证明该漂移不能留到计划末尾。已将一般文档引用迁移到现有 `check-ai-system-invariants`/`check-docs-metadata`，Trust Layer 引用迁移到 `check-trust-layer-docs`/`check-multilingual-docs`，未新增无实现 alias；Fast Policy、traceability 和 full quality 必须重新通过后才视为解决。
- `RFE-ISSUE-124`（流程/归档引用迁移，中）：RFE-118 的 adopter E2E 首次证明 installer 生成的 `documentationAlignment` 在 Finish 前有效，但 Contract 归档后仍引用 `active/...contract.json`，导致 PR 校验出现悬空证据。已在通用 archive transaction 中仅迁移结构化对齐证据到 durable archive path，并保留真实 `verification.command`/`executionContractPath` 不变；archive 单元、首次 adoption、后续 governance journey 回归必须同时通过，禁止以关闭路径存在性校验或 adoption 特判解决。
- `RFE-ISSUE-125`（流程/格式化前置，低）：RFE-118 首次完整质量在 fast static 阶段发现新增 archive helper 与 journey fixture 未经 Ruff formatter，按设计在重测试前快速停止。已格式化两文件并从头重跑完整质量，1253 tests、85.03% coverage 及全部 gate 通过；保留 formatter-first fail-fast 行为，最终计划复核时再判断是否需要自动格式化。
- `RFE-ISSUE-126`（CI 诊断证据，高）：RFE-118 的 PR #415 在同一 Head SHA 上两次于 `project-test` 约 22 分 45 秒失败，但 `run_quality_gate.py` 将完整输出缓存在 runner 临时文件，Workflow 只发布 heartbeat 和 timing summary，teardown 后无法取得准确 pytest/coverage 根因。PR #415 已关闭且归档证据保持不可变；建立相邻恢复工单 `documentation-alignment-hosted-recovery-20260728`，在失败路径打印所有非成功 Gate 日志、无 timing 时回退打印 wrapper 日志，并以静态 Workflow 回归、干净 Linux 复现、稳定 coverage 余量、完整 replacement PR/CI/merge/close 验收。该修复必须落地到流程，不允许以手工复制日志或盲目 rerun 代替。
- `RFE-ISSUE-127`（归档后测试 fixture，高）：RFE-118 新增的 generated documentationAlignment 测试把该工单 `active/...contract.json` 当作隐含实存 fixture；`ai-finish` 前本地全量测试因 active 文件存在而通过，归档提交后的 clean checkout 必然因路径消失失败。这解释了 PR #415 同一 SHA 的确定性 `project-test` 失败，不是 runner 波动或 Head SHA 问题。恢复工单将 fixture 改绑不可变 archive Contract，并把 post-archive clean-checkout 验证列为强制验收；后续测试不得依赖正在执行工单的 active 生命周期文件。
- `RFE-ISSUE-128`（归档序列事实，低）：恢复计划初稿把前序归档序列误记为 621，但不可变 Summary、Archive Manifest 与 archive index 一致证明真实序列为 620。未修改任何前序归档字节；仅修正 active 恢复 Contract/计划，使相邻恢复序列为 621，并要求 Finish 与 aggregate PR 校验机械证明连续性。
- `RFE-ISSUE-129`（恢复 writer/schema 契约，高）：性能工单在 #416 完整关闭后使用 `ai-resume-work-item` 成功生成 source-bound `resumeHistory`，但紧接着 canonical `ai_check_work_item.py` 因 allowlist 遗漏该 writer-owned 字段而报 `unknown field: resumeHistory`，使唯一支持的恢复流程端到端不可用。性能实现再次暂停，建立 `resume-history-contract-schema-20260728` corrective：以 red-first 回归证明 writer/reader 漂移，只把 `resumeHistory` 加入 canonical Contract allowlist，保留无关 unknown field 拒绝和全部 lineage/ancestry/digest/predecessor/manifest 校验；完成独立 PR/CI/merge/close/分支清理后，再回到性能工单验证生成 lineage 和 Preflight。
- `RFE-ISSUE-130`（恢复证据来源/人工抄写，中）：性能工单第二次续接时，前序 merge commit 曾从叙述性结果误抄为不存在的 `9deb1e532249...`，而真实 `origin/main` 为 `9deb1e53b32e...`；`ai-resume-work-item` 因 predecessor 与目标不一致正确 fail closed。已改为以本地 `origin/main`/Git object 为事实源后由 writer 追加第二条连续 lineage，不修改 immutable Start Receipt；后续不得从聊天摘要人工抄写 commit identity。
- `RFE-ISSUE-131`（性能调查命令边界，低）：一次临时 profiling 直接调用 `.venv/bin/pytest`，因该入口未把仓库根加入 import path 而产生 19 个虚假 collection error；canonical Makefile 一直使用 `.venv/bin/python -m pytest`。性能证据只接受 canonical Python module invocation，错误运行仅作为 not-run 诊断保留，不进入前后性能比较。
- `RFE-ISSUE-132`（安装器历史遍历放大，高）：旧 installer 虽然不复制 active/archive，并在本工单初稿中新增 starts/decisions 文件过滤，但 `Path.rglob("*")` 仍会先遍历 archive 1514、starts 305、decisions 63 个文件，而且同一安装会多次重建清单。已改为在遍历前剪枝四个历史树、只显式保留 skeleton `.gitkeep`，并缓存单次安装的不可变 source inventory；发行内容和扫描成本都不再随模板治理历史线性增长。
- `RFE-ISSUE-133`（性能测量隔离，中）：一次最终本地同型测量期间又并行启动了 installer 聚焦回归和 mypy，CPU/磁盘竞争使结果不再可比；该 pytest 进程在约 57% 时主动终止，退出 143，只保留为 `not-run: concurrent local workload`，不得纳入性能收益。后续本地与 Hosted 计时都必须独占对应 runner，并绑定 session/run identity。
- `RFE-ISSUE-134`（安全 baseline/实现，低）：首次完整质量在新增 streaming `Popen` 路径上发现 Bandit 从 114 增至 115，新增项是 relay 中仅用于类型收窄的 B101 `assert process.stdout is not None`。未扩张 baseline；实现改为显式 fail-closed RuntimeError 后重跑 exact Bandit baseline，保留既有 114 条低风险与零中高风险边界。
- `RFE-ISSUE-135`（Make 并行协议/性能，中）：实时 telemetry 包装器启动递归 Make 时未传递父 Make jobserver descriptor，日志持续出现 `jobserver unavailable: using -j1`；当前 Gate 外层仍并行，但任何 Gate 内部并行都会被静默串行化。已从受控 `MAKEFLAGS --jobserver-auth/--jobserver-fds` 解析并验证打开的 descriptor，仅在 POSIX 上通过 `pass_fds` 传递，并增加有效/失效 descriptor 回归。
- `RFE-ISSUE-136`（性能 session 指针所有权，高）：第二次完整质量的外层 session 全部 Gate 实际通过，但 pytest 内 `tests/test_makefile.py` 的 `make -n quality` 因递归 Make 的 `+` 语义仍会执行一个 693ms dry-run session，并覆盖全局 `target/quality/current-session.txt`；若直接由 Workflow 读取，会把 fixture timing 误报为真实质量耗时。每个 timing/log 目录本身未混写。已让顶层 `quality-full` shell 用 EXIT trap 重绑定自己生成的 session ID，确保 success/failure 退出后 summary、artifact 和失败日志选择外层真实 session，并增加架构回归。
- `RFE-ISSUE-137`（hosted 性能证据生命周期，高）：深度性能工单的最终验收要求至少三次同类 hosted run，但 canonical 顺序要求 `ai-finish`/archive 后才能 push，而 archived Summary 不允许再写入 hosted 结果；未发布 commit 又不能触发 hosted CI，形成结构性闭环。性能实现已在本地完成并通过一次完整质量门，但停止在 Finish/PR 之前，不用未治理 push 或归档后改写绕过。前置 corrective `hosted-verification-snapshot-lifecycle-20260728` 新增 fail-closed、非 Git/provider 写入的 snapshot gate：仅对明确要求 hosted evidence、clean 且 commit 済み的专用 branch、未归档 active Contract/Summary、通过本地 quality、非 release intent 开放；receipt 只允许将精确 branch push 用于 hosted measurement，禁止 PR、merge、release、archive mutation、closure 和 branch deletion。完成该 corrective 的完整 PR/CI/merge/close/cleanup，并同步已安装 skill 后，性能工单才可恢复，采集至少三次可比 hosted run，再回到标准 Finish/PR/merge/close 流程。
- `RFE-ISSUE-138`（Coverage Guard 关联，低）：hosted snapshot corrective 的首轮聚焦验证已通过 9 项测试，但 Coverage Guard 发现新生产脚本 `scripts/ai_prepare_hosted_verification.py` 尚未登记到对应测试关联，按设计阻止收口。已先把精确 production/test pair 加入 coverage policy，再重新执行 coverage、Preflight、checkpoint 和完整质量；不使用宽泛 `tests/**` 或关闭 reportOnly 来绕过。
- `RFE-ISSUE-139`（Coverage 阈值精度/错误成功，高）：hosted snapshot corrective 的 `ai-finish` 运行 1267 tests 后，真实 coverage 为 `84.994669%`，日志明确打印 `FAIL Required test coverage of 85% not reached`，但 coverage.py 默认 `precision=0` 将其四舍五入到 85，pytest 返回 0，quality summary 因而错误记录 PASS 并完成归档。前序 archive 保持不可变且尚未 push/PR；已建立相邻 recovery `coverage-threshold-precision-recovery-20260728`，在 `pyproject.toml` 固定两位精度，以真实 pytest-cov subprocess 证明 84.58% 不再因显示为 85% 而成功，并补足新 snapshot validator 的 fail-closed 分支覆盖。该 recovery 必须与前序形成唯一、连续、人工授权且 source-bound 的 archive pair，通过真实 coverage ≥85.00%、aggregate PR、hosted CI、merge/close/cleanup 后，才允许性能工单恢复。
- `RFE-ISSUE-140`（Hosted Coverage 可移植余量/恢复链，高）：PR #418 的 hosted run `30317392184` 在 Linux Python 3.12 完成 1269 tests 后以 84.95% 正确失败，而同一 commit 在本地 macOS 为 85.0013%；这证明精确门禁已生效，也证明贴线本地结果不能作为跨平台通过证据。失败前 `project-test` 用时 21 分 25 秒，进一步确认当前重测试瓶颈。恢复链中的前两份 archive 保持不可变；新增 `hosted-coverage-margin-recovery-20260728`，保留 85% policy floor 并把可执行阈值提高到 85.10% 作为最小 portable buffer，以 deterministic snapshot-validator 分支测试增加真实覆盖；同时将 aggregate PR 的“一对恢复”推广为逐边验证的相邻恢复链，每一跳仍必须连续 sequence、人工授权、立即前序 source reference、start receipt/base 与 commit ancestry 全部成立，任一断链则整个多工单 PR fail closed。该第三 recovery 必须本地超过 buffer、hosted 全绿、合并/关闭/清理后，才能恢复深度性能工单。
- `RFE-ISSUE-141`（归档序列预测/不可变证据，中）：`hosted-coverage-margin-recovery-20260728` 的生成字段 `archiveSequence` 正确分配为 625，但其 Finish 前 `knownGaps` 自由文本把 `archiveGrowth: 626` 误读成未来序列并预测“archive sequence 626”，归档后形成不可变文本矛盾。权威字段、Manifest 和 index 保持不改写；新增紧邻 corrective `archive-sequence-prediction-guard-20260728` 记录 625 为事实，并在 Summary validator 中禁止尚无 generator-owned `archiveSequence` 的 active Summary 预测具体数字，只允许“next archive sequence”等非数值表述；已归档且持有 authoritative field 的历史数字仍可读取。该门禁必须以 red-green 正反例、完整质量、四段 recovery-chain PR、hosted CI、merge/close/cleanup 验收后，性能工单才能恢复。
- `RFE-ISSUE-142`（Recovery Chain base 方向/测试真实性，高）：四段 archive 完成后，真实 `make check-ai-pr AI_BASE_COMMIT=9deb1e53...` 仍拒绝全部后续 recovery。根因是 generalized chain 将原 pair predicate 的“predecessor 必须兼容 PR merge-base”逐边复用，等价于错误要求向前产生的 recovery base 同时是旧 PR base 的祖先；原 chain 单测又把所有 `merge-base --is-ancestor` 调用 mock 为成功，隐藏了方向错误。新增 `recovery-chain-base-compatibility-20260728`：只让 chain root 验证 PR-base compatibility，后续每边验证 immediate predecessor → recovery 的正向 ancestry，并保留 consecutive sequence、source reference、human approval、start receipt 和 raw human request 全部条件；测试使用精确有向 ancestry graph，旧实现先红、修复后绿。完整五段 aggregate PR、hosted CI、merge/close/cleanup 前不得恢复性能。
- `RFE-ISSUE-143`（Recovery Chain source pair 边界，中）：RFE-142 修复后逐边诊断证明 623→624、624→625、626→627 全部条件通过，唯一断点是 625→626：该 recovery 精确引用立即前序 immutable `summary.json`（因为问题事实位于 Summary），而 gate 只承认 `contract.json`。Contract 与 Summary 已由 archive pair、Manifest、sequence 和 digest 共同验证，故新增 `recovery-chain-source-evidence-20260728`，只允许从精确 predecessor Contract path 推导出的同名 paired Summary path；任意旧 Summary、相似名或非相邻路径仍拒绝，其他 ancestry/approval/receipt/human-source/Manifest 条件不变。正反例和真实六段 aggregate PR 必须通过后才能 push。
- `RFE-ISSUE-144`（文档 Make 命令解析，低）：深度性能 measurement snapshot 的首次 fast policy 在约十秒内把计划中的 ``make -n quality`` 错误识别为缺失 target `-n`。先以集成回归复现，再让 system-invariant parser 识别 `-n`、`--dry-run`、`--just-print`、`--recon` 这组无参数 dry-run 选项后提取真实 target；不通过改写文档隐藏解析缺陷。聚焦回归和真实 `make check-ai-system-invariants` 已通过，measurement candidate 必须包含该修复后重新生成。
- `RFE-ISSUE-145`（Snapshot 子 Make 环境隔离，高）：第二次 measurement snapshot 的完整 pytest 中 1290 项通过、coverage 85.21%，但三个 adopter lifecycle 测试共同失败；snapshot 入口的命令行 `CONTRACT=<performance>` 经 GNU Make 的 `MAKEFLAGS`/`MAKEOVERRIDES` 传入 pytest，再泄漏到临时安装工程的嵌套 `make ai-finish TASK=e2e`，使 adopter 错用模板 active Contract。已用 red-first runner 回归要求独立 quality 子进程清除 `MAKEFLAGS`、`MAKEOVERRIDES`、`MFLAGS`、`GNUMAKEFLAGS`、`CONTRACT`、`SUMMARY`、`TASK`、`AI_BASE_COMMIT`，同时保留其他 CI/session 环境；原三个失败测试与环境单测聚焦重验均通过。不得以测试特判或复制模板 Contract 到 adopter 绕过。
- `RFE-ISSUE-146`（Manual smoke intent 边界，高）：首个 source-bound hosted run `30324321071` 的 `template-smoke` 成功，quality step 为 10 分 53 秒，`installation-smoke` 15 秒，但整体失败；所有 `workflow_dispatch` 被旧表达式无条件视为 release preparation，导致非发布 measurement branch 执行历史 release-state consistency 并失败，末端 evidence 正确记录 `release-evidence:failure`。Workflow 现要求显式 `purpose` choice：`release_preparation` 保持严格默认和发布证据检查，`hosted_measurement` 只声明性能测量且 release-evidence Job 以 not-applicable 成功退出；三语质量文档给出精确 dispatch 命令，静态 Workflow 回归禁止重新合并两种 intent。该失败 run 只作为诊断/初始 timing，不计入三次成功验收样本。
- `RFE-ISSUE-147`（Worktree/关闭状态，中）：深度性能工单的 `ai-close-work-item` 在另一个 stale worktree 占用 `main` 时，为避免破坏该 worktree 会让当前工作区停留在 detached HEAD，但最终仍报告 repository ready，容易使下一工单误以为已处于同步后的本地默认分支。现场已通过只读核对、移除两个 clean stale worktree 并切回同步 `main` 恢复；流程根因不得混入 WI-10，必须在“其他流程问题”阶段建立独立 corrective，使 closure 最终状态明确区分 ready-on-base 与 ready-but-detached，并以多 worktree 回归阻止再次误报。
- `RFE-ISSUE-147` 补充现场证据（PR #427 closure）：`ai-close-work-item` 在确认远程 work branch 尚未删除前已切换默认分支并删除本地 work branch，随后因远程分支存在而失败；此时原命令无法从默认分支直接重试，必须按 PR Head SHA 重建同名本地分支、删除远程分支后再执行 closure。后续 corrective 还必须把删除顺序做成可重入事务：先完成所有不会破坏重试身份的远程/PR/branch 前置确认，再删除本地分支；任一步失败都保留或自动恢复可重试状态。
- `RFE-ISSUE-147` 本地实现状态：独立 corrective `rfe147-transactional-work-item-closure-20260728` 已将 local branch tip 与 merge PR `headRefOid` 绑定，在删除 local retry identity 前完成 base 安全验证、remote 删除和 `ls-remote` 不存在证明；普通 worktree 的 remote 失败会切回 Work Item branch，linked worktree 在 detach 后 local 删除失败会恢复原 checkout。终态明确区分 `ready_on_base` 与 `closed_but_current_worktree_detached`，后者返回 `nextWorkItemReady=false` 和同步 base worktree path。24 项 focused tests（含真实 bare remote + linked worktree topology）已通过；完整 quality、PR、Hosted CI、merge、修正后的自关闭和 branch cleanup 完成前不得标记闭环或进入 RFE-151。
- `RFE-ISSUE-148`（Hosted Coverage 可移植余量/审计恢复，高）：WI-01～WI-20 双向追踪审计在本地以 1333 tests、85.102326% 通过并归档为 sequence 635，但 PR #425 的 Hosted Linux 对同样 1333 tests 只得到 85.05%，低于未改变的 85.10% executable threshold，故 `template-smoke` 与末端 `ci-evidence` 正确失败。PR #425 已关闭且前序 archive 保持不可变；新增相邻 recovery `wi01-wi20-hosted-coverage-recovery-20260728`，仅以追踪校验器真实 fail-closed 分支测试增加稳定余量，不降低阈值、不排除生产文件、不改变二十行审计结论。replacement PR 必须通过完整 aggregate recovery-chain、Hosted required checks、merge、`ai-close-work-item`、前序/恢复分支清理后，才可进入“其他流程问题与 RFE-ISSUE-082”阶段。
- `RFE-ISSUE-149`（归档回滚/原始 Summary 字节，高）：为 RFE-080 增加归档后外部 evidence 原子迁移测试时，确认旧 archive rollback 在 index 等后续步骤失败后只把 archive 目录中的 Summary 移回 active；该 Summary 已被写入 archive Contract path、archiveSequence 和生成 changedFiles，因而并非事务前原始 active evidence。当前 corrective 扩展同一原子边界：移动前捕获全部 active artifact 原始字节，任何异常在恢复路径后逐个 byte-for-byte 复原，同时恢复 traceability manifest 原始字节、index、status 并删除 partial manifest；Contract、Summary、Outcome 和 review evidence 不允许半归档状态。
- `RFE-ISSUE-150`（归档 Summary 证据迁移，高）：WI-10 完成全部本地门禁与 `ai-finish` 后，committed `check-ai-pr` 拒绝三条仍指向 `active/...summary.json` 的 lifecycle `acceptanceEvidence`。根因是 archive transaction 虽掌握完整 active-to-archive replacement map，却只迁移 `documentationAlignment` 与 `changedFiles`，新增 Summary 证据结构仍依赖人工记忆。已暂停 WI-10 push/PR，建立独立 corrective `fix-archive-summary-evidence-path-rewrite-20260728`：归档时仅按 schema-defined `path`/`contractPath`/`summaryPath` 与 `evidence`/`sourcesUsed`/`generatedFiles` collection 执行 exact-path 迁移，完整 `verification` subtree 与普通 prose 保持不变；生成 archive pair 必须经过 aggregate PR 正反验证，后段失败必须 byte-for-byte 恢复原 Status，真实缺失路径仍 fail closed。该 corrective 完整 PR/CI/merge/close/cleanup 后，WI-10 必须基于修复后的 main 重新生成 archive 并重跑聚合 PR 门，禁止手改旧 archive。
- `RFE-ISSUE-150` 闭环状态：corrective PR #428 的 34 项 Hosted checks 全部通过，已合并并由 `ai-close-work-item` 验证本地/远端分支删除及 main 同步；WI-10 已通过 immutable Start Receipt + `resumeHistory` 从 `511ccaab` 续接到合并提交 `489658bf`，正在重新生成 archive，旧 archive 未被原地修改。
- `RFE-ISSUE-150-ENV-001`（验证环境，中）：corrective 首次完整质量通过 1340 项，但命令行 `AI_PYTHON=../../.venv/bin/python` 被递归 Make 传播到临时 adopter repository，导致 3 项 nested Make/install 测试找不到解释器。该轮保持为失败证据；改用被忽略的 worktree-local `.venv` 链接并恢复规范 Make 默认值，原 3 项已定点通过，完整 finish 必须从头重跑。
- `RFE-ISSUE-150-BASELINE-001`（安全基线，中）：clean replacement 完整 pytest 为 1343 passed，但 rollback hardening 删除 best-effort subprocess 后，Bandit 低风险结果由 114 降为 112（恰好移除一条 B603 与一条 B110），exact baseline 正确 fail closed。已确认无中高风险 finding，并将 baseline 变更纳入 Contract、Summary 与验收；不得把降低告警也静默放行，更新后必须重新执行完整质量。
- `RFE-ISSUE-151`（校准事务/授权边界，高）：WI-10 文档反向核对确认旧 Calibration Session 只持久化回答，Unknown、十阶段校对证据、Candidate 内容与两次确认没有形成同一机器可验证授权链；Active 写入与 Session 保存也可能在第二步失败后留下分裂状态。独立 corrective `rfe151-calibration-transactional-confirmation-20260728` 已实现 schema v2 结构化十阶段证据、Unknown/incomplete/STOP 统一阻断、canonical Candidate revision + SHA-256、reviewer/owner phase 与精确 Candidate identity 绑定、变更后确认失效、schema v1 fail-closed migration，以及 Active/Session 原始字节或不存在状态的 rollback transaction；三语安装文档和元数据门禁同步约束 `record-evidence`、`prepare-candidate`、digest-bound confirmation 与 `consistency unproved` STOP。当前 focused 83 项通过；完整 quality、PR、Hosted CI、merge、修正后的 closure 和 branch cleanup 完成前不得标记闭环或进入 RFE-152。
- `RFE-ISSUE-153`（归档后状态诊断/流程，高）：RFE-151 完成 `ai-finish` 后，完整实现与文档 diff 已由 immutable archived Summary `changedFiles` 声明，但 `check-ai-status-consistency` 只把 RFE-116 覆盖的 Start Receipt 归入当前 archive transaction，其余合法路径仍被误报为 no-active drift，并建议 `repair-ai-status`；repair 重写同一个 deterministic zero-change marker 后必然再次失败。独立 corrective `rfe153-post-archive-status-diagnosis-20260728` 必须把 ownership 扩展为“当前 changed manifest 精确绑定 archive pair，且 Summary.changedFiles 覆盖每一个 live path”，任一漏项、无关、malformed、incomplete、historical-only 或 mismatch 继续 fail closed；serialized Status 漂移才允许建议 repair，unowned live change 必须明确 repair 无法建立 ownership。该 corrective 完整 PR/Hosted/merge/close/cleanup 前不得进入 RFE-152。
- `PLAN-006`（用户顺序确认/发布门禁，高）：用户最终确认后续严格顺序为“深度性能工单 → WI-10 → WI-01～WI-20 全量双向追踪审计 → 其他流程问题与 RFE-ISSUE-082 → 日语评估及整改 → 文档对齐 → 发布 → 清理计划文档”。该顺序已替换旧五阶段概括；发布不得越过任一前置阶段，任何阶段发现遗漏或流程问题都必须先完成对应 corrective Work Item 的完整生命周期。
- `PLAN-008`（用户新增/发布前过期资产清理，高）：用户要求在发布前新增独立 `pre-release-deprecated-assets-cleanup`，处理过期代码、逻辑和文档，并包括已实施完成、不再承担当前执行职责的计划文档。该工单必须在文档对齐后、WI-18 前完成完整生命周期；以资产清单逐项证明 runtime/reference/migration/归档保护状态，只有 `deletionAllowed=true` 且替代与回归证据完整时才允许删除。不可变 Contract、Summary、Manifest、决策与发布证据只允许保留或明确历史化。WI-19 仍在发布后处理本轮执行期间继续使用的计划，两者不得相互替代。
- `PLAN-009`（用户新增/真实荒诞与注入攻击发布门，高）：用户提供 12 个真实权限伪造、证据破坏、外部资料注入和危险执行案例，要求在 WI-18 前形成英中日三份完整文档，并验证 AI Cockpit 对每例的识别/阻断能力；未达标必须实现整改到测试通过。已插入独立 `pre-release-real-absurd-injection-assessment`，排在发布前过期资产清理后、WI-18 前；必须使用统一 source/trust/authority/operation/evidence/independent-approval 决策链和真实机器 Gate，不允许用零散关键词或对用户恶意的主观判断替代证据。

- `RFE-ISSUE-106`（installation-smoke 生命周期，高）：RFE-104 的 hosted installation-smoke 证明，采用方 Runtime 在 `ai-finish` 保留 active Outcome 后、安装 commit 前运行严格 coverage guard 会把首次安装的 Runtime 文件正确识别为缺少采用方测试的生产变更。发布继续冻结；独立 corrective `rfe-106-installation-smoke-lifecycle-20260730` 必须在 `ai-finish` 直接报告边界之后、安装 commit 和所有 post-install guards 之前显式 archive，并以 source-order 回归和 hosted installation-smoke 证明；不得降低 coverage guard 或把模板测试装入采用方。
- `RFE-ISSUE-107`（归档恢复冲突，高）：RFE-106 合并后，已归档但未合并的 RFE-104 若直接 rebase，会与目标基线同时占用 archive sequence `666` 和 traceability ID `PLAN-DIRECTIVE-049`。旧 archive 保持不动；新增 `rfe-107-derived-record-collision-20260730`，在 rebase 前比较分支与目标基线的 archive index/traceability manifest，冲突时 fail-closed 并要求创建 successor Work Item。RFE-107 完整闭环后，RFE-104 只能以当前 main 上的新 successor 重交，原 PR/分支保留为审计证据。
- `RFE-ISSUE-107-ARCHIVE-001`（归档前格式，高）：RFE-107 的首次本地 archive 在未提交状态暴露 active Contract 的三个尾随空格；active 文件被 Git 忽略，普通 `git diff --check` 只能在 archive 后发现它。已回滚未提交 archive 到 active，新增 archive transaction 的逐 artifact whitespace preflight；任何 Contract/Summary/Outcome 等待归档文本含尾随空格时，必须在移动、Manifest、index 或 Status 变化前 fail-closed。随后需重新 finish 生成新的 archive，不得修改首次生成的 archive 证据。
- 深度性能工单在提交 `f9e1b7e41ec282de2704497369a9db4a7ac8db6c` 上取得三次串行、同类型、同 SHA 的成功 hosted measurement：run `30325316583`、`30325920850`、`30326505323` 的 quality step 分别为 650、655、653 秒，median 653 秒，按小样本 nearest-rank 的保守 p95 为 655 秒；`project-test` 分别为 637.117、642.422、640.607 秒，median 640.607 秒，p95 642.422 秒。相对 run `30280375075` 的 1281 秒基线，quality p95 缩短约 48.9%，达到第一阶段 p95 <15 分钟目标。该结果证明结构性改善，但重测试绝对耗时仍约 11 分钟，`project-test` 仍是后续性能改进的主要残余瓶颈。
