---
author: Ray
title: "注入边界"
description: "针对敌意或误导性指令的仓库级边界。"
audience:
  - adopter
  - security_reviewer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# 注入边界

<!-- capability-claim: repository_governance_layer -->

AI Cockpit 不是通用的提示词注入检测器。当指令与声明的范围、证据、权限、受保护路径、操作策略或必要的人类确认冲突时，
它可以拒绝或停止仓库操作。

不可信文本在绑定到可审查的证据和权限之前都只是数据。门禁通过只证明声明的输入和规则通过，并不证明所有恶意意图都已被检测。

认证、托管、网络和依赖扫描等实际安全控制由目标项目及外部工具负责。AI Cockpit 不是沙箱、身份提供方或运行时安全替代品。
具体案例见[Real Absurd Injection Cases](../reference/real-absurd-injection-cases.zh-CN.md)。
