---
author: Ray
title: "Work Item ライフサイクルのクローズ"
description: Work Item を PR merge 後に安全にクローズする手順を説明する日本語リファレンス。
keywords:
  - ai-cockpit
  - work-item
  - lifecycle
  - closure
---

# Work Item ライフサイクルのクローズ

`make ai-close-work-item` は、PR merge 後の Work Item を閉じ、ブランチと base を安全に整合させる最後の処理です。単に branch を削除するコマンドではありません。

## 前提条件

- Contract と Summary が archive 済みである。
- 対応する PR が merge 済みである。
- Work Item branch が PR と一対一で識別できる。
- PR merge 以降、base branch に予期しない変更がない。
- ローカルとリモートの作業ツリーが clean である。

## 実行

```sh
make ai-close-work-item TASK=<task>
```

コマンドは Contract/Summary/Cockpit Status の archive 証拠、local Work Item
branch の Head SHA と merge 済み PR Head SHA の一致、base の
fast-forward-only 同期、clean worktree、remote branch の不在、local branch
の削除を順に検証します。remote branch の不在を証明する前に、再試行に必要な
local Work Item branch を削除しません。

## Worktree を使う場合

base branch が別の worktree で checkout されている場合、その worktree の
clean 状態を確認して base を fast-forward し、remote Work Item branch の
削除と不在を検証してから、Work Item worktree を detached にして local branch
を削除します。detach 後に local branch の削除が失敗した場合は、可能な限り
元の Work Item checkout を復元して再試行可能な状態を保ちます。ホスト環境が
管理する worktree は、コマンドが所有権を確認せずに削除しません。

## 失敗時の扱い

どれかの事後条件が満たされない場合は fail closed となり、Work Item は閉じた
と報告されません。remote branch の削除が失敗または検証不能の場合、local
branch を保持し、通常の worktree では元の Work Item checkout へ戻してから
失敗を報告します。エラーの証拠を確認し、同じコマンドを再実行してください。
`git branch -d` や手動の remote branch 削除を先に実行すると、PR ownership
または再試行 identity を失うため避けます。

## stacked PR の例外実行

通常は merge 済み Work Item branch 自身から closure を実行します。子の corrective
PR が active な親 Work Item branch に merge され、子 worktree が古い closure 実装を
保持している場合だけ、親 branch の現在の policy から、その子 worktree を明示して
実行できます。

```sh
make ai-close-work-item TASK=<child-task> ARGS="--worktree /absolute/path/to/child-worktree"
```

これは一般的な branch 削除 API ではありません。同じ repository に登録済みの Git
worktree root だけを受け付けます。Makefile は `ARGS` を変更せず CLI へ渡します。
provider 問い合わせ、receipt の書き込み、base の切り替え、branch 操作より前に、CLI
は選択された worktree の branch が厳密に `codex/<child-task>` であることを要求します。
task と worktree が一致しなければ fail closed で停止し、ある Work Item の receipt に
別 Work Item の PR や branch を結び付けることはできません。Git 操作は子 checkout
に限定され、provider の `gh` 問い合わせもその選択された子 branch を明示するため、現在の
policy checkout の PR を推測しません。通常の
merged PR、Head SHA、親 branch への merge 保持、clean worktree、receipt、remote 不在の
検証はすべて必須です。

## 過去の stacked PR チェーン receipt

archive は不変です。corrective Work Item が明示的な predecessor source を持たずに
すでに archive 済みの場合、aggregate PR check は archive の書き換えや task 名による
例外を許可しません。代わりに、`.ai/work-items/recovery-receipts/` 配下の限定された
append-only receipt が、連続する archive prefix を正確に束縛できます。各 Work Item ID、
Contract/Summary の path、SHA-256 digest、archive sequence、base commit、PR merge-base
を記録します。

checker はすべての束縛と base-commit ancestry edge を再計算します。receipt の完全に
compatible な prefix だけを受け入れ、その後の entry には通常の隣接 source recovery
rule が引き続き必要です。

この不変 prefix の後に既に merge 済みの子 Work Item が現れる場合もありますが、
repository history が次のすべてを証明するときだけ受け入れます。canonical Start Receipt
が有効であること、Contract と Summary が一つの immutable archive commit で同時に追加
されたこと、その commit が親 PR base の後にある二親 merge の第二親から、検査対象の
親 PR history に入ったことです。`HEAD` から到達できること、task 名、local Closure
Receipt、親 branch への直接追加だけでは十分ではありません。これにより実際の子 PR を
許可しつつ、親 PR 内の独立した Work Item を隠すことを防ぎます。

receipt の欠落、並び替え、不整合、未 merge、無関係な entry があれば、既定の
「一つの PR に一つの新規 Work Item」rule がそのまま適用されます。

## 完了状態

成功時は共通して次の条件が揃います。

- `active/` に Contract/Summary の組がない。
- archive 証拠が保持されている。
- local base が remote base と一致する。
- Work Item の local/remote branch が削除されている。
- 検証済み base worktree が clean である。

さらに、コマンドは次の二つを区別します。

- `ready_on_base`: 実行元 worktree 自体が同期済み base 上にあり、次の Work
  Item を開始できます。
- `closed_but_current_worktree_detached`: Work Item のクローズは完了しましたが、
  実行元 worktree は detached であり、次の Work Item を開始できません。
  コマンドが表示する同期済み base worktree へ移動して続行します。

## Provider merge 状態が不整合な場合の例外評価

`ai-close-work-item` には、`OPEN`、`CLOSED`、`skipped` などの PR を通常の
merge として扱う fallback はありません。通常の closure は引き続き provider の
`MERGED`、一致する branch/Head SHA、merge commit、merge timestamp を必要とし、
通常の open PR の branch cleanup を防ぎます。

まれに provider の部分成功が、base に存在する GitHub 検証済み・署名済みの
二親 merge commit と、`OPEN` のままで通常の merge facts がない PR API という
矛盾を残すことがあります。その場合だけ、読み取り専用の別境界を評価します。

```sh
make ai-assess-provider-merge-state-recovery \
  ARGS="--evidence provider-anomaly.json --human-confirmed --output target/provider-recovery.md"
```

evidence は元 PR の番号、URL、branch/Head SHA、観測済み base SHA、正確な
`[base, head]` 親、GitHub signature verification、base 到達性、およびその Head
に紐付く required hosted job 全件の成功を結び付けます。出力される receipt は
provider の不整合状態と通常の merge facts が利用不能であることを明記します。
この評価は branch 削除、PR 変更、PR の `MERGED` 化を一切行いません。後続の
recovery action には別の明示的人間判断と、この receipt の監査保持が必要です。
