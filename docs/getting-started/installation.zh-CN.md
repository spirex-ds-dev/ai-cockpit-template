---
author: Ray
title: "安装 AI Cockpit"
description: "以交互式流程为默认入口的安装、审查、回滚与校准边界。"
audience:
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - interactive_installation_wizard
---

# 安装 AI Cockpit

<!-- public-quality-target: ai-cockpit-quality -->

面向人的默认路径是真正的交互式安装器。请在目标 Git 仓库中运行：

<!-- command-evidence: adopter_required -->
```bash
./install.sh --interactive
```

TTY 环境中不带参数执行也会打开同一向导。显式 installer 参数仍是稳定的自动化入口；
非 TTY 环境中不带参数会直接安全停止，不会等待输入。

## 向导展示什么

1. Target Repository
2. Readiness
3. Installation Mode
4. Governance Profile
5. Planned Changes
6. Conflict Review
7. Explicit Confirmation
8. Installation
9. Verification
10. Next Action

确认前，向导会显示目标路径、Git 与工具 readiness、New Adoption / Upgrade /
Dry Run、Lite / Standard / Strict、计划新增和修改数量、源码影响、安装分支及所有冲突。
界面默认选择 Standard。

Profile 选择只记录安装意图。安装器不会激活 Lite、Standard 或 Strict；工程校准仍是
安装后的独立 Work Item。

## 安全边界

在明确输入 `yes` 前，目标仓库保持只读。Dry Run、readiness 阻断、未解决冲突、空回答、
拒绝、EOF 或中断都不会调用写入事务。
如果 readiness 或冲突证据为 `Unknown`，必须停止并在安装前解决。

安装器不会 commit、push、创建 Pull Request、merge、删除成功安装分支、激活 Strict，
也不会把安装报告为校准完成。事务失败时，现有 Installer 会恢复原 branch 或 detached HEAD，
并回滚新建或替换的文件、managed section、Makefile 和 agent marker。重试前应检查报告中的
目标状态，不能根据普通失败消息自行推断恢复成功。

## 自动化与提示词辅助路径

确定性自动化请使用 `--dry-run`、`--upgrade`、`--create-adoption`、`--stack`、
`--update-makefile` 等显式参数。Prompt-first Agent 安装降为辅助路径：必须执行同一只读计划，
展示冲突与计划文件，并在调用 Installer 前等待明确确认。

## 安装之后

安装完成后，开始独立的工程校准 Work Item。
审查生成的 Work Item 和安装分支。Git 发布仍走正常的人类审查生命周期。校准必须作为
独立 Work Item 开始；安装本身不是生产就绪证据。

## 更多信息

- [严格安装与供应链验证](installation-security.zh-CN.md)
- [工程校准指南](calibration.zh-CN.md)
- [校准会话模型](../reference/calibration-session-model.zh-CN.md)
- [安装故障排除](../troubleshooting/installation.zh-CN.md)
- [交互式向导架构](../architecture/interactive-installation-wizard.md)
- [iOS](examples/ios.zh-CN.md)、[Android](examples/android.zh-CN.md)、[Java](examples/java.zh-CN.md) 示例
