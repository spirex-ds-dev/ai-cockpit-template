---
author: Ray
title: "标准采用指南"
description: "面向对象工程的安装、校准、工单、CI 与人工评审指南。"
keywords:
  - adoption
  - governance
  - verification
---

# 标准采用指南

<!-- semantic-domain: north-star -->
<!-- semantic-domain: product-boundary -->
AI Cockpit 是为校准 Human-Agent Trust 服务的 Repository Governance Layer。它治理可评审的仓库证据，不是 Agent Runtime、Workflow Engine 或 Security Sandbox。

本指南面向安装器已经生成 `adopt_ai_cockpit` 的对象工程。请先完成[安装指南](installation.md)中的前置条件和安装；安装器生成的 Contract 会记录下文使用的采用前 base commit。

<!-- doc-domain: adoption -->
<!-- semantic-domain: installation-flow -->
## Adoption

从已发布版本安装到对象工程，完成 `adopt_ai_cockpit`，评审 diff，并让该 Adoption Work Item 只使用一个 PR。安装只部署治理运行时，不等于项目适配完成。

<!-- command-evidence: adopter_required -->
```sh
make ai-finish TASK=adopt_ai_cockpit
# archive bundle commit 前必须停下并取得批准。
git add .
git commit -m "adopt AI Cockpit governance"
make check-ai-pr AI_BASE_COMMIT='<pre-adoption-commit>'
```

按以下顺序完成完整生命周期：

1. 本地执行 finish/archive，然后停下评审。
2. 取得明确批准，提交完整 archive bundle，再使用安装器记录的 base 执行 PR 检查。
3. push 前取得独立批准。
4. 创建 PR，不启用自动 merge，也不让平台自动删除源分支；由人执行 merge。
5. 取得关闭批准后执行：

<!-- command-evidence: adopter_required -->
```sh
make ai-close-work-item TASK=adopt_ai_cockpit
```

关闭步骤会验证 base 同步，并清理本地和远程 Work Item 分支。完整停止条件见[安装指南的 Adoption 阶段](installation.md#phase-3-adoption)。

<!-- doc-domain: calibration -->
## Calibration

使用独立的 `configure_ai_cockpit` Work Item 评审 Project Profile、Guard、质量命令、Coverage 与 CI 证据。Unknown 或 stale 证据会阻断 readiness。

<!-- command-evidence: adopter_required -->
```sh
make cockpit-doctor
make cockpit-calibrate
cp .ai/project_profile.proposed.yaml .ai/project_profile.yaml
${EDITOR:-vi} .ai/project_profile.yaml
make check-ai-project-profile
make check-ai-guard-calibration
make ai-cockpit-quality
make check-ai-adoption-ready
```

复制 proposed Profile 本身不代表批准。人工必须评审事实、解决全部 `blocking:` unknown、确认边界，并校准质量命令、Coverage、CI、CODEOWNERS 和 SECURITY.md，之后才能通过 readiness。

<!-- doc-domain: work-item -->
<!-- semantic-domain: task-outcome-fields -->
## Work Item 与 Task Outcome

每次变更使用一个 Contract（范围契约）、专用分支、Summary（交接记录）、PR、archive（归档证据）、merge、closure（关闭验证）和分支清理。Task Outcome 必须保留 finding、risk、停止原因、解决、防复发、verification、unknown、人工决定和残余风险，不得只报告成功。

<!-- doc-domain: ci -->
## CI

CI 获取完整 Git 历史，并要求公共项目质量入口和 `check-ai-pr`。模板 Hosted fixture 不证明对象工程自己的命令。

<!-- command-evidence: adopter_required -->
```sh
ADOPTER_REMOTE="${ADOPTER_REMOTE:?使用 Contract 记录的 remote}"
ADOPTER_DEFAULT_BRANCH="${ADOPTER_DEFAULT_BRANCH:?使用 Contract 记录的默认分支}"
make ai-cockpit-quality
make check-ai-pr AI_BASE_COMMIT="$(git merge-base HEAD "$ADOPTER_REMOTE/$ADOPTER_DEFAULT_BRANCH")"
```

<!-- doc-domain: human-approval -->
<!-- semantic-domain: human-confirmation -->
## 人工批准

对象工程必须在 commit、push、merge 和 `ai-close-work-item` 之前分别停止并取得人工决定，具体见[安装指南的 Adoption 阶段](installation.md#phase-3-adoption)。自动 merge 或平台侧自动删分支不得绕过 lifecycle closure。

<!-- doc-domain: target-project-adaptation -->
<!-- semantic-domain: supported-scope -->
## 对象工程适配

Preset 只是起点。必须按真实工程校准 module、variant、SDK/JDK、formatter、测试、构建插件、Coverage 路径、分支策略和 Hosted CI。`generic` 在事实明确前保持 fail closed。能力状态只来自 Capability Truth Matrix。
