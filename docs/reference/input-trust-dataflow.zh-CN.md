---
author: Ray
title: "输入信任数据流"
description: "用于间接注入处理的受限来源追踪与信任标签。"
---

# 输入信任数据流

仓库会在内容跨步骤流转时保留本地来源记录。该记录只分类内容；不认证身份、不验证 Provider 事件，也不授权外部操作。

`direct_user_instruction` 与 `repository_policy` 的初始标签是 `authority`；仓库文档为 `repository_content`；Issue、PR 评论、网页、构建日志和测试夹具为 `untrusted_content`；Agent 生成内容为 `generated_content`；工具输出为 `unknown_source`；`provider_verified_event` 为 `provider_verified`。

标签是来源事实而不是权限。Markdown 命令仍是 Content，Issue 的自称管理员不是身份认证，Agent 结论不能在后续阶段变成独立证据。工具输出明确分为 `raw_data`、`tool_interpretation` 与 `agent_interpretation`；跨步骤流转保留原始来源和信任标签。

高风险操作缺少完整来源链、使用不受信任/未知内容，或依赖生成结论时会被本地 `block`；恢复需要记录来源与每次转换并进入人工审查。该模型不声明 Provider 身份验证或外部执行能力。
