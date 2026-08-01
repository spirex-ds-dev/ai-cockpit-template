---
author: Ray
title: "操作時ポリシー再評価"
description: "高リスクなツール呼び出しのための限定的なローカル判断モデル。"
---

# 操作時ポリシー再評価

入力時のレビューは、後続の操作への許可ではありません。列挙された高リスク呼び出しの直前に、ローカルモデルは次を再評価します。

```text
入力信頼 + 要求された操作 + 実際のツール呼び出し + 対象リソース
+ 現在の権限 + 証拠の鮮度 + 破壊的影響
= 実行判断
```

`OperationTimeRequest` は要求、実際の呼び出し、対象、宣言された scope、以前の承認 binding、現在の権限、証拠の鮮度、破壊的影響を束縛します。`evaluate_operation_time_policy` は `allow`、`confirm`、`block` だけを返し、コマンド実行や Provider 権限の付与はしません。

削除、テスト/CI変更、Branch Protection変更、Secret書き込み、push、merge、release、migration、script 実行、外部 API 書き込み、install/upgrade、governance component の uninstall を対象にします。実際の呼び出しは要求と一致しなければならず、対象または scope の変更は古い承認を無効にします。証拠が古い場合や現在の権限がない場合は人間の確認が必要で、影響未分類または要求/呼び出しの不一致は回復条件付きで停止します。

たとえば script の作成は後の実行を許可しません。後続の `execute_script` は独立して再評価され、`create_script` の承認を再利用できません。

## 制限

これは決定的なローカルポリシー証拠です。人物の認証、Provider イベントの検証、Branch Protection の設定、script 実行、外部書き込みは行いません。呼び出し元は判断を保持し、適用される Provider とリポジトリの制御を実施する必要があります。
