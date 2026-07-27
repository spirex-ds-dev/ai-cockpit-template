---
author: Ray
title: "Quality Gate 運用"
description: AI Cockpit の Quality Gate、証拠、Work Item 追跡の運用説明。
keywords:
  - ai-cockpit
  - quality-gates
  - ci
  - evidence
---

# Quality Gate 運用

AI Cockpit は `make quality` の後方互換性を維持します。`make quality` は
`make quality-full` と同じです。短いローカルフィードバックには
`make quality-fast`、リリース準備には `make quality-release` を使います。

## 責任範囲

- `quality-fast` は format、lint、diff、schema、文書メタデータ、Project Profile、status policy を担当します。
- `quality-full` は完全なテスト、証拠、サプライチェーン、プロジェクト整合性を追加します。個別の Trust テストはデバッグ用の独立 target として残し、完全な pytest 後に再実行しません。
- `quality-release` はインストールとリリース証拠を追加します。Fast の結果やキャッシュ結果はリリース証拠の代わりになりません。
- Compatibility job は Python/platform matrix の検証だけを行い、完全な quality graph は実行しません。
- Hosted smoke は `template-smoke`（完全な quality の唯一の所有者）、`installation-smoke`、`release-evidence` の独立 Job に分かれます。後二者は quality 所有者に依存し、完全な graph を再実行しません。

## 証拠と fail-closed

`scripts/run_quality_gate.py` は各 Gate について、command、commit、所要時間、終了コード、timeout、cache 状態、出力 digest、失敗時の末尾を含む JSON timing と log を記録します。`scripts/summarize_quality_gates.py` は wall time、Gate 合計時間、parallel efficiency、最長 Gate、失敗末尾、skip、最終判定を JSON と Markdown に出力します。timing 証拠がない場合は fail-closed とし、cache hit を最終証拠にはしません。

Hosted の前後 timing は推測ではなく証拠です。WI-20 の baseline または hosted run を取得できない場合は、構造化した `not-run` 理由、run ID、制限を記録し、改善を主張してはいけません。

`scripts/determine_quality_scope.py` は変更 path から Fast、Full、Release を決定します。未知または混在する範囲は Full になります。並列実行は `.ai/quality/gates.yaml` で出力の競合がない場合に限ります。

## トレーサビリティ

すべての Work Item は PR、merge、archive、branch cleanup の前に「指示 → 計画 → 実装 → 受入」の双方向追跡を検証しなければなりません。実装証拠のない受入項目、または計画された受入項目のない実装指示は漏れとして記録し、修正してから進めます。

完全な流れは Contract、実装、検証と Summary、PR、merge、`make ai-close-work-item`、最後に local/remote branch cleanup です。本書は実行証拠を説明するものであり、AI Cockpit が Security Sandbox であることや、単独で enterprise compliance を保証することを主張しません。
