---
author: Ray
title: "工程校准指南"
description: "通过 Work Item 以问答方式完成工程校准。"
---

# 工程校准指南

在 Runtime 安装后，通过一个 Work Item 执行校准。Agent 提问，工程负责人确认；
Unknown 在获得证据前保持阻断。

## 需要确认的问题

1. 此仓库承担什么角色？
2. 实际使用哪些语言和技术栈？
3. 生产源码和测试在哪里？
4. 哪些文件由生成器或供应商提供？
5. 哪些路径关键或风险高？
6. 哪些本地和托管质量命令是权威命令？
7. 谁审核修改和 Release？
8. 还存在哪些风险、例外和 Unknown？
9. 工程是否已准备好采用阻断性控制？
10. 升级或重大变更后必须重新确认什么？

Work Item 会把答案整理为可审核的提议；它不会自行启用策略、证明负责人身份，
也不会替代人工批准。平台示例请看 [iOS](examples/ios.zh-CN.md)、
[Android](examples/android.zh-CN.md) 或 [Java](examples/java.zh-CN.md)。
内部存储机制请看[校准内部模型](../reference/calibration-session-model.zh-CN.md)。
