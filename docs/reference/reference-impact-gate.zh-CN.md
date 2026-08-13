---
author: Ray
title: "Reference Impact Gate"
description: 在破坏性或兼容性变更之前，以证据判定引用影响。
audience:
  - adopter
  - maintainer
status: current
authority: derived
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - reference_impact_gate
keywords:
  - ai-cockpit
  - reference-impact
  - destructive-change
---
# Reference Impact Gate

Reference Impact Gate 不推测请求者的意图，而是检查可观察到的操作影响。它覆盖删除、重命名、移动、废弃、可见性或签名变更、配置或公共 API 变更以及 Maven 模块删除。搜索不到匹配项不能证明动态引用或外部 Consumer 不存在。

## 使用方式

将 version 1 记录放入 `.ai/evidence/reference-impact/`，然后执行：

```sh
make check-ai-reference-impact
```

`check-ai-pr` 会执行同一检查，结果写入 `target/reference-impact/`。存在影响目标却没有对应记录时，会以 `needs_human_confirmation` 停止并给出恢复条件，绝不会被当作空记录成功通过。普通文档等无影响路径走 `not_applicable` 快速路径。强制模式下，`block` 和 `needs_human_confirmation` 都返回非零退出码。机器事实源是 `.ai/schemas/reference_impact.schema.json`。

请求信任、授权绑定、安全证据和范围一致性分别记录，最终判定取最严格结果。“已经不用”“已批准”是待验证声明，不是安全证据。

## 判定与恢复

- `block`：仍有静态、测试、文档、配置、Workflow 或 Maven 构建引用，或实际 diff 与声明存在事实矛盾。应迁移引用并修正范围。
- `needs_human_confirmation`：影响证据不完整、请求要求绕过分析，或批准未被独立地绑定到目标。Gate 会停止并说明恢复所需的证据或授权；它不推断恶意意图，也不永久否定变更。
- `needs_human_confirmation`：动态引用、外部 Consumer、Monitoring 证据未知、为空或已过期；治理证据不完整；或正在删除公共 API / 配置 Key。补充有效的迁移及 Owner 证据后重试。
- `continue`：仓库内引用均已清除，并且仓库外及治理证据完整明确。

Python 使用 AST 名称分析，TypeScript 使用基础文本分析，其他语言标记为 `generic_analysis_only`。基础分析可能遗漏反射、生成代码、别名、动态加载、外部仓库与 Monitoring Consumer，也可能把不可执行的文本识别为引用。因此它不宣称完整语义分析。

对于 Maven `build_module`，检查器会保守地搜索父 POM 的 `<modules>`、POM 中的 artifact/dependency 文本，以及引用模块路径或 POM 的测试。这不能证明运行时、已发布或外部消费者不存在。

检查器不会猜测旧记录缺失的字段，也不会改写 Archive Evidence。路径必须是仓库相对路径；路径穿越和符号链接目标会被拒绝。
