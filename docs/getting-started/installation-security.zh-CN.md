---
author: Ray
title: "严格安装与供应链验证"
description: "面向 Release 负责人和安全负责人的 AI Cockpit 安装验证入口。"
---

# 严格安装与供应链验证

当你负责 Release 批准、私有镜像或供应链证据时使用本页；首次安装的简单路径不要求先阅读它。

请验证动态解析出的 Release、与 tag 绑定的元数据和源提交、installer 与 archive 资产，
以及它们的 SHA-256。不得静默改用旧 Release 或移动分支。任何例外都必须先由 Release
负责人审核，再重新验证证据。

完整证据规则、私有镜像边界和企业责任限制见
[安全与 Release 验证](security-release-verification.zh-CN.md)。
