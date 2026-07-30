---
author: Ray
title: "Human-Agent Trust Layer（人类—智能体信任层）"
description: AI Cockpit 为什么存在、治理什么，以及证据、故障安全控制、可信链、供应链证据和人类决策如何共同工作。
keywords: [ai-cockpit, trust-layer, human-agent-trust, evidence, human-decision]
---

# Human-Agent Trust Layer（人类—智能体信任层）

AI Cockpit 是 Repository Governance Layer（仓库治理层）。它使用可复核证据决定受治理的变更何时可以继续、何时必须把控制权交还人类、何时必须停止治理路径。它不是 SKILL、Agent Runtime 或 Security Sandbox。

三种语言版本都是完整等价版本。英文版本是措辞权威版本；中文和日文版本保留相同的结构、边界、实现证据和限制。

<!-- section-id: why -->
## 为什么存在（Why）

AI Cockpit 存在，是因为智能体可以给出貌似合理的解释，却没有给出足以信任仓库变更的证据。因此 Human-Agent Trust 是校准的，而不是绝对的：系统必须暴露已知信息、缺失信息、必须由谁决策，以及如何恢复。

核心规则是 Evidence over Self-Declaration（证据优先于自我声明）。AI Cockpit governs evidence; it does not replace evidence-producing tools（AI Cockpit 治理证据，不替代产生证据的工具）。聊天断言、智能体的信心或自称的批准，都不是独立授权。

Trust Layer 把仓库治理、故障安全控制、可信链、委托域证据和人类决策连接起来。它使安全的下一步清晰可见，但不声称本地仓库层能够证明组织、提供方、模型或生产环境的全部属性。

<!-- section-id: what -->
## 治理什么（What）

AI Cockpit 治理仓库本地的决策边界。它把人类请求绑定到 Work Item Contract，评估策略和范围，记录验证结果，为人类审查压缩结果，并归档重建决策所需的证据。

七个治理层是：

1. **执行边界** — 绑定请求的操作、范围、权限和允许的效果。
2. **控制权返还** — 证据缺失、过期、矛盾或风险高时停止，或请求人类决策。
3. **已知风险防护** — 拒绝仓库门禁覆盖的确定性注入、无依据声明、荒诞、绕过和不安全操作案例。
4. **完整可信链** — 在确实由相应系统产生时，连接 SHA-256、Git History、Digital Signature、Branch Protection、Hosted CI / External Audit Evidence 和 Human Approval。
5. **软件供应链证据** — 记录 SBOM、Provenance、发布身份、校验和、扫描与提供方证据，但不把委托证据假装成本地原生证明。
6. **人类决策压缩** — 展示状态、信任信号、变更、问题、停止原因、未知、人类决策、证据依据和下一步，不制造评分或置信度表演。
7. **归档与恢复** — 保留 Contract、Summary、事件、决策记录、发布证据和 Archive Manifest，使停止或完成的路径可审查、可恢复。

完整可信链是组合关系，而不是 AI Cockpit 的单一功能。SHA-256 绑定字节；Git History 绑定仓库祖先关系；Digital Signature 在外部签名系统提供时绑定签名者；Branch Protection 绑定托管仓库策略；Hosted CI / External Audit Evidence 绑定提供方或审计者结果；Human Approval 记录负责人的决策。缺失的环节仍然是缺失。

SBOM 与 Provenance 不同。SBOM 描述软件制品中的组件和依赖关系。Provenance 描述制品如何产生、来自哪个源代码、经过什么构建过程以及使用什么身份或环境。SBOM 是 Delegated Domain Evidence（委托域证据）：AI Cockpit 可以记录和治理它，但不会仅因文件存在就生成或独立验证该域事实。

AI Cockpit 不独立保证身份、运行时隔离、不可篡改审计日志、分支保护、数字签名、无漏洞或企业合规。AI Cockpit is not a Security Sandbox（AI Cockpit 不是安全沙箱）。企业控制仍由采用方以及相关提供方或审计者负责。

<!-- section-id: how -->
## 如何工作（How）

治理路径是：

```text
人类意图 → Raw Request Binding → Work Item Contract → Preflight
→ Requested Operation / Capability Mapping → 变更
→ 验证与外部证据 → Human Decision and Recovery
→ Task Outcome / Status → Archive Manifest
```

Raw Request Binding 保留建立工单的人类请求。Requested Operation 明确 target、action、environment、effect 和 authority 要求。Capability Mapping 从仓库策略派生所需能力；自我声明的能力列表不能授权未映射的操作。

Preflight 默认使用 enforced profile。只有 `ready` 报告可以继续。`not_ready`、`needs_human_confirmation`、`human_decision_recorded`、过期、矛盾或失败证据都会停止治理路径。人类决策解决的是流程问题；它不会把未验证的检查变成通过。恢复意味着补充或修正证据，并重新运行受影响的检查。

Human Decision and Recovery 必须说明发生了什么、为什么重要、可选方案、建议、证据和恢复条件。决策结果随 Work Item 归档；它永远不能替代测试、CI、安全、发布、身份或企业控制证据。

<!-- section-id: current-implementation -->
## 当前实现（Current Implementation）

当前仓库实现的是本地、确定性的 Trust Layer。以下实现细节属于权威内容，不能为了概念整洁而删除：

- **Unsupported Claim Regression Gate**（`make unsupported-claim-regression`）拒绝无依据的完成、批准、执行、文件和发布声明。
- **`delusion-test-gate`**（`make delusion-test-gate`）执行有限的已知场景回归词汇，包括荒诞、绕过、注入和未充分定义的工作案例。
- **Guard Signal Envelope** 携带 `signalId`、`state`、`confidence`、`evidence`、`policyReference`、`humanDecisionAllowed` 和 `safeAlternatives`，并兼容旧的 `name`、`value`、`sources` 字段。确定性 confidence 表示证据质量，不是权限。
- **Preflight enforced profile** 配置在 `.ai/guards/preflight_review_policy.yaml`；只有新计算的 `ready` 报告可以通过受治理的 start 和 finish。
- **Raw Request Binding**、**Requested Operation** 和 **Capability Mapping** 是适用的 Contract v2 code Work Item 边界。
- **Human Decision and Recovery** 持久化结构化请求和证据，然后要求重新执行 Preflight 与项目检查。
- **Archive Manifest** 在非自引用的归档记录中保存冻结 Contract 与 Summary 证据的 SHA-256 摘要。

这些是仓库本地实现事实，不证明通用语义风险分类、通用日语模型流利度、提供方身份、运行时隔离或企业 readiness。WI-16 日语评估仍限定于确定性的日语治理路径；其中的通用流利度 non-claim 是有意保留的。

<!-- section-id: deterministic-coverage -->
## 确定性覆盖（Deterministic Coverage）

门禁覆盖有限的、已知且可审查的案例：缺失或过期证据、无依据声明、非法 Work Item 状态、范围违规、原始请求与操作不匹配、选定的提示注入指示器、不安全的关键域效果，以及必须请求人类确认的场景。对能够识别的案例，它们采用 fail-closed。

[真实荒诞与注入案例评估](reference/real-absurd-injection-cases.zh-CN.md) 记录了 12 个具体负例及其当前结果。它区分当前被直接覆盖的 5 个输入信任案例，与仍需复核的 7 个仓库/生命周期证据缺口；它不推断请求者或文档具有恶意，也不把未绑定的门禁说成已防护。

它们不检测智能体的内部状态，不理解所有语言细节，不提供通用提示注入防御，也不证明外部控制已经配置。Capability Truth Matrix 是当前实现状态的唯一事实来源；本文档的理念不能把 planned、template-only、adopter-installed 或 externally required 能力升级为 implemented。

<!-- section-id: machine-readable-evidence -->
## 机器可读证据（Machine-Readable Evidence）

机器可读证据链包括 Contract v2、Guard Signal、Preflight 报告、测试与质量结果、Task Outcome、Cockpit Status、人类决策请求/证据、发布证据和 Archive Manifest。每条记录都有所属生命周期阶段，并应通过路径、命令、提交、摘要或提供方结果引用。

Native Governance Evidence 由本仓库自己的受治理命令和 schema 产生。Delegated Domain Evidence 由独立工具、托管提供方、采用方工程、审计者、签名服务、SBOM/Provenance 生成器或漏洞扫描器产生。AI Cockpit 可以要求、绑定、展示和归档委托证据；它不能静默制造委托事实。

<!-- section-id: commands-and-demonstration -->
## 命令与演示（Commands and Demonstration）

离线、面向失败的演示命令是：

```sh
./docs/examples/trust-layer-demo.sh
```

质量与生命周期路径包括：

```sh
make unsupported-claim-regression
make delusion-test-gate
make ai-preflight CONTRACT=.ai/work-items/active/<task>.contract.json
make ai-finish TASK=<task>
make ai-close-work-item TASK=<task>
```

只有记录了输出、输入提交、环境和所属 Work Item 时，命令才构成证据。演示是离线且无害的；它不模拟托管发布或企业控制。

<!-- section-id: boundaries-and-navigation -->
## 边界与导航（Boundaries and Navigation）

请按以下权威职责使用文档：

- [Design Philosophy](philosophy/design-philosophy.md) — North Star 与设计原则。
- [Architecture](architecture.md) — 组件、证据归属与数据流。
- [安全与发布验证](getting-started/security-release-verification.zh-CN.md) — 发布级外部证据要求。
- [Capability Truth Matrix](reference/capability-truth-matrix.md) — 当前实现状态的唯一事实来源。
- [Enterprise Control Checklist](reference/enterprise-control-checklist.md) — 采用方与外部控制责任。
- [Documentation Architecture](reference/documentation-architecture.md) — 权威角色地图（当前中文完整路线由本页及中文入口提供）。

README 是短入口；本文档是完整的 Trust Layer 权威说明。两者都不能替代产生证据的工具和外部控制。
