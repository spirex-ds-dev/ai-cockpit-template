---
author: Ray
title: "安全与发布验证"
description: "安全、供应链、版本与发布决定的证据边界。"
keywords:
  - security
  - release
  - supply-chain
  - verification
---

# 安全与发布验证

当前能力状态只以[能力事实矩阵](../reference/capability-truth-matrix.md)为准；本页说明验证责任，不会把计划中或委托给外部系统的控制提升为已实现能力。

<!-- semantic-domain: security-limits -->
<!-- semantic-domain: prompt-injection-limits -->
安全证据必须绑定来源：每条记录都要标明其验证的准确 tag、source commit、产物和 digest，任何不一致都 fail closed。Prompt Injection 检测和输入信任控制可以降低已知仓库风险，但不证明 containment（执行约束）、可信身份、隔离或安全执行。

<!-- doc-domain: release-metadata -->
<!-- semantic-domain: release-version -->
## Release metadata

`release.json` 是公开发布事实的投影（published projection）；候选记录和历史记录不能替代它。Tag、source commit、installer、archive asset 和 checksum 必须一致。

该投影是仓库声明，不是平台 Release 已公开的独立证明。必须分开理解：

| 记录 | 能证明什么 | 不能证明什么 |
| --- | --- | --- |
| `release.json` | 仓库投影为已发布的版本 | 平台 Release 存在、稳定或 asset 可下载 |
| `next-release.json` | 预定的下一候选版本 | 已发布、已建 tag 或已可发布 |
| Git tag | 不可变源码引用存在 | 平台 Release 或 asset 已发布 |
| 平台 draft Release | 平台侧草稿记录存在 | 已稳定公开 |
| 平台 stable Release 与 asset | 平台公开了版本记录和指定 asset | 未经独立校验的 digest 或源码正确性 |
| Release freeze 证据 | 候选事实已冻结供审核 | 已发布或已完成发布后验证 |

### 采用方路径

只使用权威公开投影或另行验证的私有镜像。平台 stable Release、tag 固定 metadata、source、installer、archive asset 和 digest 任一不一致都必须停止；不得用最高 tag 代替。

对于选定的公开 tag，`release-digests.json` 是在 source commit 固定后生成的 release asset。Quick Install 会把该 asset 下载到一次性的 tag clone 中，再验证 tag、source commit 与 artifact digest，验证通过前不会写入对象工程。Tag tree 中的副本可能只是历史基线，不能作为后续 release 的权威。下载或验证失败时，不得替换文件或绕过失败：保留错误，针对准确 tag 验证公开 release asset；若不可变历史 release 有误，只能发布新的修正 tag。

### 维护者路径

先验证 candidate 和 freeze 证据。平台发布后，再单独验证 stable Release 与可下载 asset，之后才能改变公开投影。候选、发布、发布后验证是三个不同状态。

<!-- doc-domain: digest -->
## Digest

验证 installer 和可下载 archive 的 SHA-256。调用方补充断言（caller assertion）不能替代已发布 metadata。

<!-- doc-domain: provenance -->
## Provenance

Provenance 将产物绑定到来源/构建声明；它不同于 SBOM，必须由外部构建、签名或证明工具生成或验证。AI Cockpit 记录并校验这些委托证据，不会独立生成外部断言。

<!-- doc-domain: sbom -->
## SBOM

SBOM 列出软件组件，不证明产物如何构建、没有漏洞或已经满足企业合规。

<!-- doc-domain: trust-root -->
## Trust root

公开安装的信任链由带标签的 `release.json`、不可变 tag/source 身份、archive asset 和 digest 构成。缺失证据必须停止。

<!-- doc-domain: private-mirror -->
## Private mirror

私有镜像必须发布并独立保护等价的 metadata、tag/source 身份、asset 和 digest。AI Cockpit 不替镜像运营者背书。

<!-- doc-domain: local-source -->
## Local source

本地源码安装是有意的非公开路径；在对象工程 Work Item 中记录 source commit/path 边界，不得称为公开发布验证。

<!-- doc-domain: enterprise-boundary -->
<!-- semantic-domain: enterprise-compliance-boundary -->
## 企业边界

AI Cockpit 可以提供 repository-local SDLC 证据，但不能单独保证企业合规、可信身份、生产隔离、外部不可变审计或平台控制。

以下命令属于模板发布维护者。应在 release candidate checkout 中运行，并在 Hosted CI 中要求同样的检查；它们不是对象工程的安装步骤。

| 检查 | 验证的证据 |
| --- | --- |
| `check-release-distribution` | 公开 metadata、tag/source、installer、archive 与 digest 投影 |
| `check-sbom` | 机器可读组件清单及其来源绑定 |
| `check-provenance` | 产物与来源/构建声明的绑定 |
| `check-secret-scanning` | 仓库 secret scanning 证据 |
| `check-dependency-vulnerabilities` | 发布门可用的依赖漏洞证据 |

<!-- command-evidence: hosted_executed -->
```sh
make check-release-distribution
make check-sbom
make check-provenance
make check-secret-scanning
make check-dependency-vulnerabilities
```

所有检查必须针对同一准确候选来源成功。证据缺失、陈旧或冲突时，停止发布准备并保留失败证据，按照[故障排查](../reference/troubleshooting.md)恢复；不得改称对象工程验证或本地源码验证。输入和产物责任见[分发参考](../reference/distribution.md)。

[全面日语能力评估](../reference/japanese-capability-assessment.md)仍是独立的发布前强制阶段。其 digest 绑定准确文件字节；任一绑定文件变更都会使报告过期，只有全部纠偏后的 `final_reassessment` 才能满足发布门禁。本页不发布版本，也不把该评估标记为完成。
