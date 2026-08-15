---
author: Ray
title: "首次校准"
description: "安装后由人确认项目边界的最短 Work Item 路径。"
audience:
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# 首次校准

<!-- capability-claim: project_calibration_profile_proposal -->

校准是安装后的独立治理 Work Item。模板提供校准 proposal 能力，但这不证明采用项目已经安装或完成校准。它记录项目真实的 source、test、generated、protected、
quality、ownership、branch 和 Unknown 边界，不根据 stack 标签猜测这些边界。

这是模板提供的校准方案；它不证明采用方已安装。

1. 完成并关闭安装／采用 Work Item。
2. 从同步后的远程默认分支启动 `configure_ai_cockpit`。
3. 运行 `make cockpit-doctor`，审查其仓库证据。
4. 选择适比例的[校准配置](../reference/calibration-profiles.zh-CN.md)。
5. 解决所有阻断性 Unknown，并取得所需的人类确认。
6. 验证 Project Profile，运行选择的质量路径。

生成的 proposal 不是批准。详细字段见[校准指南](calibration.zh-CN.md)；完成后进入[首个 Work Item](first-work-item.zh-CN.md)。
