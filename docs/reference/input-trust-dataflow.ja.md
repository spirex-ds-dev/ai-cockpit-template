---
author: Ray
title: "入力信頼データフロー"
description: "間接インジェクション処理のための限定的な来歴追跡と信頼ラベル。"
---

# 入力信頼データフロー

このリポジトリは、内容が段階をまたぐときにローカルな来歴記録を保持します。これは内容を分類するだけで、ID を認証せず、Provider イベントを検証せず、外部操作を許可しません。

`direct_user_instruction` と `repository_policy` は `authority`、リポジトリ文書は `repository_content`、Issue・PR コメント・Web・ビルドログ・テスト fixture は `untrusted_content`、Agent 生成内容は `generated_content`、ツール出力は `unknown_source`、`provider_verified_event` は `provider_verified` です。

ラベルは権限ではなく来歴の事実です。Markdown のコマンドは Content のままであり、Issue の管理者自己申告は本人確認ではありません。Agent の結論は後続段階で独立した証拠になりません。ツール出力は `raw_data`、`tool_interpretation`、`agent_interpretation` を区別し、段階間の伝播は元の source と trust label を保持します。

高リスク操作では、来歴チェーンの欠落、不信頼または未知の内容、生成された結論がローカル `block` になります。回復には各変換を記録した上での人間レビューが必要です。このモデルは Provider の本人確認や外部実行を主張しません。
