---
author: Ray
title: "最初の Work Item"
description: AI Cockpit 導入後に最初の管理対象タスクを実行する日本語ガイド。
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
---

# 最初の Work Item

導入と Calibration が検証済みになったら、最初の管理対象タスクを開始します。各タスクは一つの Work Item、専用 branch、PR で構成し、対象プロジェクトで発見した remote default branch と base commit を Contract に記録します。

1. `make ai-start TASK=example_change TITLE="Example change" MODE=code` を実行する。
2. Contract の scope、outOfScope、sources、acceptance、verification を埋め、Unknown を解消する。
3. Preflight が `needs_human_confirmation` または `not_ready` なら停止し、人へ報告する。
4. 実装前に、Contract と Summary を指定した正式な checkpoint を実行する。

   ```sh
   make ai-prepare-implementation \
     CONTRACT=.ai/work-items/active/<task>.contract.json \
     SUMMARY=.ai/work-items/active/<task>.summary.json
   ```

5. `make ai-finish TASK=example_change ARCHIVE=true` を実行して証拠を archive し、commit、push、PR、merge の順に進める。
6. merge 後に `make ai-close-work-item TASK=example_change` を実行し、base 同期と branch cleanup を確認する。

Agent の説明は証拠ではありません。次は[Quality Gates](../operations/quality-gates.ja.md)を参照してください。
