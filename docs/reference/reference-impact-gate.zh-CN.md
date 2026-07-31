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
keywords:
  - ai-cockpit
  - reference-impact
  - destructive-change
---
# Reference Impact Gate

Reference Impact Gate 在接受删除、重命名、移动、废弃、可见性或签名变更、配置删除及公共 API 删除之前，检查声明的影响记录。结果为 `continue`、`needs_human_confirmation` 或 `block`。搜索不到匹配项不能证明动态引用或外部 Consumer 不存在。

## 使用方式

将 version 1 记录放入 `.ai/evidence/reference-impact/`，然后执行：

```sh
make check-ai-reference-impact
```

`check-ai-pr` 会执行同一检查，结果写入 `target/reference-impact/`。强制模式下，`block` 和 `needs_human_confirmation` 都返回非零退出码。机器事实源是 `.ai/schemas/reference_impact.schema.json`。

## 判定与恢复

- `block`：仍有静态、测试、文档、配置或 Workflow 引用；请求包含绕过分析的表达；或把自我声明的批准当作破坏性变更授权。应迁移引用或移除无效请求。
- `needs_human_confirmation`：动态引用、外部 Consumer、Monitoring 证据未知、为空或已过期；治理证据不完整；或正在删除公共 API / 配置 Key。补充有效的迁移及 Owner 证据后重试。
- `continue`：仓库内引用均已清除，并且仓库外及治理证据完整明确。

Python 使用 AST 名称分析，TypeScript 使用基础文本分析，其他语言标记为 `generic_analysis_only`。基础分析可能遗漏反射、生成代码、别名、动态加载、外部仓库与 Monitoring Consumer，也可能把不可执行的文本识别为引用。因此它不宣称完整语义分析。

检查器不会猜测旧记录缺失的字段，也不会改写 Archive Evidence。路径必须是仓库相对路径；路径穿越和符号链接目标会被拒绝。
