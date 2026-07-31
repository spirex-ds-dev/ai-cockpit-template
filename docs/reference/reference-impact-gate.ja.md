---
author: Ray
title: "Reference Impact Gate"
description: 破壊的変更または互換性に影響する変更の前に、参照影響を証拠で判定する。
audience:
  - adopter
  - maintainer
status: current
authority: derived
lastVerifiedBy: capability-truth-matrix
keywords:
  - ai-cockpit
  - reference-impact
  - destructive-change
---
# Reference Impact Gate

Reference Impact Gate は、削除、名称変更、移動、非推奨化、可視性・シグネチャ変更、設定削除、公開 API 削除を受け入れる前に、宣言済みの影響記録を評価します。判定は `continue`、`needs_human_confirmation`、`block` のいずれかです。検索結果がゼロでも、動的参照や外部 Consumer が存在しない証明にはなりません。

## 使用方法

version 1 の記録を `.ai/evidence/reference-impact/` に置き、次を実行します。

```sh
make check-ai-reference-impact
```

`check-ai-pr` も同じ Gate を実行し、結果を `target/reference-impact/` に出力します。強制モードでは `block` と `needs_human_confirmation` は非ゼロ終了です。Canonical Schema は `.ai/schemas/reference_impact.schema.json` です。

## 判定と復旧

- `block`: 静的、テスト、文書、設定、Workflow の参照が残る、回避要求がある、または自己申告の承認を破壊的変更の権限として使っている。参照を移行するか、不正な要求を除去します。
- `needs_human_confirmation`: 動的参照、外部 Consumer、Monitoring の証拠が未知・空・古い、Governance 証拠が不足、または公開 API / 設定 Key の削除である。現在有効な移行・Owner 証拠を追加して再実行します。
- `continue`: Repository 内の参照がすべて解消され、Repository 外と Governance の証拠も明示されています。

Python は AST 名解析、TypeScript は基本テキスト解析、それ以外は `generic_analysis_only` です。Reflection、生成コード、Alias、動的ロード、外部 Repository、Monitoring Consumer は見逃す可能性があります。逆に実行されない文字列を参照として報告する可能性もあります。したがって完全な意味解析を主張しません。

旧記録の欠落フィールドは推測せず、Archive Evidence を書き換えません。パスは Repository 相対に限定し、Path Traversal と Symbolic Link Target を拒否します。
