---
author: Ray
title: "首个 Work Item"
description: "采用 AI Cockpit 后，从头到尾完成第一个有边界的治理任务。"
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
---

# 首个 Work Item

安装和校准验证成功后，使用这一页完成第一个治理任务。每个任务只有一个 Work Item、一个专用分支和一个 PR；
从目标项目发现的远程默认分支开始，并把 remote、branch、base commit 写入 Contract。

1. 运行 `make ai-start TASK=example_change TITLE="Example change" MODE=code`。
2. 编辑 Contract，填写 scope、outOfScope、sources、acceptance、verification，并解决 Unknown。
3. 若 Preflight 为 `needs_human_confirmation` 或 `not_ready`，停止并把结果交给人处理。
4. 实现前，指定 Contract 和 Summary，运行正式的实现前检查点：

   ```sh
   make ai-prepare-implementation \
     CONTRACT=.ai/work-items/active/<task>.contract.json \
     SUMMARY=.ai/work-items/active/<task>.summary.json
   ```

5. 运行 `make ai-finish TASK=example_change ARCHIVE=true` 归档证据，然后按提交、推送分支、创建 PR、合并 PR 的顺序执行。
6. 合并后运行 `make ai-close-work-item TASK=example_change`，确认基线同步且分支清理成功。

不要在 PR 前把分支合入本地 main，也不要把 Agent 的说明当作证据。接下来阅读[质量门](../operations/quality-gates.zh-CN.md)。
