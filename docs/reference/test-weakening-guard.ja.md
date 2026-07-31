---
author: Ray
title: "Test Weakening Guard"
description: テスト検証強度の低下を Git 差分の証拠から warning、review、block に分類する。
audience:
  - adopter
  - maintainer
status: current
authority: translation
canonical: docs/reference/test-weakening-guard.md
lastVerifiedBy: capability-truth-matrix
keywords:
  - ai-cockpit
  - test-weakening
  - evidence
---
# Test Weakening Guard

Test Weakening Guard は、宣言された Git base と現在の worktree を比較し、テストの検証強度が低下した可能性を再現可能な証拠として出力します。Agent の説明文だけでは通過証拠になりません。Signal が空でも、意味的同等性や十分な Coverage を証明したとは主張しません。

## 利用方法と品質グラフ

```sh
make check-ai-test-weakening-fast
make check-ai-test-weakening
make check-ai-pr AI_BASE_COMMIT=<merge-base-sha>
```

Fast は、Skip 追加、テスト削除、CI の非 Blocking 化、明示的な成功回避など低コスト Signal を確認します。Full はさらに、Test Case、Assertion、例外 Assertion、Negative Test、Coverage の対象・閾値、テストコマンドの対象、Snapshot churn を比較します。単独の `quality-fast` は Fast を所有し、`quality-full` と `quality-release` は重複する Fast を省いて Full を一度だけ実行します。`check-ai-pr` は `AI_BASE_COMMIT` に対して Full を実行します。

`--base-ref` を省略した場合は唯一の Active Contract の `baseCommit`、Active Contract がなければ `HEAD` を使用します。Policy は `.ai/guards/test_weakening_policy.yaml`、Schema は `.ai/schemas/test_weakening.schema.json` です。

## 判定と回復

- `continue`: 設定済みの静的 Weakening Signal が見つかりません。テストが十分である証明ではありません。
- `warning`: ファイル Rename、Case 数と Assertion 数を維持し保護対象の Negative/Security/Regression 意味を削除しない Case Rename/Refactor、小規模 Snapshot 変更、軽微な Assertion 減少、条件緩和らしき変更を Reviewer に提示します。
- `review`: 大幅な Assertion 減少、Skip 追加、Case・例外・Negative Test の削除、Coverage やテストコマンド範囲の縮小、Required Check の非 Blocking 化、一般テスト削除、大規模 Snapshot churn は説明と独立した要件変更証拠を要求します。
- `block`: 失敗テストの削除・無効化要求、Security/Regression Test 削除、`continue-on-error`、`allow_failure`、`|| true`、現在結果を通す目的の Coverage 引下げを拒否します。

回復にはテスト強度を戻すか、独立してレビュー可能な要件変更証拠を追加し、同じ base で再実行します。「安全を確認した」という自己申告だけでは Signal を解除できません。

Version なしの旧 Report は `decision`、`signals`、`requiredExplanation` が揃う場合だけ version 0 として読み、`legacySourceVersion: 0` と再分析必須の回復条件を付けます。存在しない Git 証拠は補いません。未知の将来 Version と不正な Policy は fail closed です。

## 限界

これは言語・Framework 非依存のテキスト差分分析です。正当な Test 統合、生成 Snapshot、Concept Rename を False Positive にする可能性があります。Helper 内部の意味的緩和、Data-driven Case の欠落、独自 Skip、Provider 側 Required Check、動的・生成 Test は見逃す可能性があります。新規 Test File 内の Skip Case は Baseline Evidence の弱体化ではなく未完成の新規 Evidence なので、この Guard は `skip_added` として報告しません。閾値は Review 強度を選ぶだけで安全性を定義しません。外部 CI/Provider 状態は Repository Evidence の外です。

Path は worktree 内に正規化されます。不正 Revision、Traversal、非通常 File、Repository 外を指す Symbolic Link は fail closed です。Checker は読み取りと報告だけを行い、Test、Coverage、Workflow、Provider 設定を変更しません。
