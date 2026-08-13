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
capabilityClaims:
  - reference_impact_gate
keywords:
  - ai-cockpit
  - reference-impact
  - destructive-change
---
# Reference Impact Gate

Reference Impact Gate は、依頼者の意図を推測せず、観測可能な操作影響を評価します。削除、名称変更、移動、非推奨化、可視性・シグネチャ変更、設定・公開 API 変更、Maven Module の削除を対象にします。検索結果がゼロでも、動的参照や外部 Consumer が存在しない証明にはなりません。

## 使用方法

version 1 の記録を `.ai/evidence/reference-impact/` に置き、次を実行します。

```sh
make check-ai-reference-impact
```

`check-ai-pr` も同じ Gate を実行し、結果を `target/reference-impact/` に出力します。影響対象の変更に対応する記録がない場合は `needs_human_confirmation` と回復条件を出して停止し、空の記録を成功として扱いません。通常の文書など影響なしの Path は `not_applicable` の高速経路です。強制モードでは `block` と `needs_human_confirmation` は非ゼロ終了です。Canonical Schema は `.ai/schemas/reference_impact.schema.json` です。

依頼の信頼、権限の結合、安全証拠、Scope 整合性は別々に記録し、最も厳しい判定を有効判定にします。「不要」「承認済み」は検証対象の主張であり、安全証拠ではありません。

## 判定と復旧

- `block`: 静的、テスト、文書、設定、Workflow、Maven Build の参照が残る、または実際の Diff と宣言に事実上の矛盾がある。参照を移行し、Scope を修正します。
- `needs_human_confirmation`: 影響証拠が不足している、分析の回避を要求している、または承認が対象に独立して結び付けられていない。Gate は停止して再開に必要な証拠または承認を示します。悪意を推測したり、変更を永久に否定したりはしません。
- `needs_human_confirmation`: 動的参照、外部 Consumer、Monitoring の証拠が未知・空・古い、Governance 証拠が不足、または公開 API / 設定 Key の削除である。現在有効な移行・Owner 証拠を追加して再実行します。
- `continue`: Repository 内の参照がすべて解消され、Repository 外と Governance の証拠も明示されています。

Python は AST 名解析、TypeScript は基本テキスト解析、それ以外は `generic_analysis_only` です。Reflection、生成コード、Alias、動的ロード、外部 Repository、Monitoring Consumer は見逃す可能性があります。逆に実行されない文字列を参照として報告する可能性もあります。したがって完全な意味解析を主張しません。

Maven `build_module` では、親 POM の `<modules>`、POM の artifact/dependency テキスト、Module Path/POM を参照する Test を保守的に検索します。Runtime、公開済み、外部 Consumer の完全な不存在を示すものではありません。

旧記録の欠落フィールドは推測せず、Archive Evidence を書き換えません。パスは Repository 相対に限定し、Path Traversal と Symbolic Link Target を拒否します。
