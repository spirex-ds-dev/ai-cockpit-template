---
author: Codex
title: "Calibration Profiles"
description: 用于项目校准的 Lite、Standard、Strict 分级控制要求。
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - project_calibration_profile_proposal
keywords:
  - ai-cockpit
  - calibration
  - governance-profile
---

# Calibration Profiles

Calibration Profile 选择采用方需要提供证据的长期控制项。它不同于 Work Item
质量路由：前者描述仓库的长期治理边界，后者为单次变更选择检查。等级按
`lite < standard < strict` 累积。
该策略和 proposal 由模板提供，但不证明采用方已安装或在目标仓库中激活。

| 等级 | 本级新增的必需控制 |
| --- | --- |
| Lite | 源码、测试、生成物、受保护路径；质量命令；默认分支；项目 Owner；Reviewer；主要 Unknown |
| Standard | 文件归属、场景覆盖、破坏性变更、依赖、CI、公共 API、生命周期和委托证据策略 |
| Strict | Reviewer/Owner 分离、外部身份与发布证据、SBOM、provenance、签名标签、分支保护、审计保留、事故与例外策略 |

Lite 明确不强制供应链、发布证明、双人激活、企业审计和外部身份控制。Deferred
不代表这些控制已被证明没有必要，只表示当前校准等级不要求它们。

`.ai/project_profile.yaml` 的 `calibrationProfile` 记录 level、`selectedBy:
human`、时间、理由以及 required/deferred controls。控制列表必须与
`.ai/calibration/profiles.yaml` 完全一致；删减或额外添加都会失败关闭。生成的
proposal 使用 `pending_human`，不会冒充已经发生的人工选择。

```sh
make check-ai-calibration-profile
make check-ai-calibration-profile ARGS="--previous-level standard"
```

验证 transition 时，需要从已审查的 base evidence 传入 previous level；没有该输入时，
验证器不会声称已经检查仓库历史。升级按等级单调允许。降级必须记录原等级、新等级、原因、被关闭控制的精确列表、
风险接受人和有效路径范围。证据缺失或矛盾时会阻止；恢复方法是还原原等级，或补全
有边界的 transition evidence 后重试。

`selectedBy: human` 只记录授权类别，不验证外部身份，也不构成合规认证、发布证明
或委托工具已经执行的证据。
