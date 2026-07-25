---
author: Ray
title: "Calibration Session"
description: "10 段階の校正 Session と安全な Candidate 有効化の日本語リファレンス。"
keywords:
  - ai-cockpit
  - calibration
  - recovery
---

# Calibration Session

`make cockpit-calibration-wizard` は `CalibrationSession` の表示・入力・ナビゲーションを担当する対話型アダプターです。状態遷移、証拠、stale、確認、activation の正本は `scripts/ai_calibrate.py` にあります。インストールだけでは校正完了になりません。

Session は次の 10 段階を順番に扱います。repository role、language and stack、source boundaries、test boundaries、generated artifacts、critical paths、quality commands、review requirements、risk and unknowns、adoption readiness。各回答は Y/N、入力、Unknown、N/A を使い、N/A には理由が必要です。

```sh
make cockpit-calibration-wizard
make cockpit-calibration-wizard ARGS="--summary"
```

Back、Pause、Resume、EOF、Ctrl+C は保存済み状態を壊さず、完了や activation を主張しません。上流回答の変更で下流証拠は stale になり、再検証が必要です。Unknown または stale は review と activation を阻止します。

Candidate は全 stage、self-check、simulation、Reviewer 確認、Owner 確認が成功した後だけ atomic に有効化されます。失敗時は fail closed となり、既存の Active configuration を保持します。これはリポジトリガバナンスの証拠であり、enterprise security、identity、sandbox、immutable audit、compliance の証明ではありません。
