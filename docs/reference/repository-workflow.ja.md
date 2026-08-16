---
author: Ray
title: "リポジトリワークフロー"
description: Work Item、ブランチ、PR、アーカイブの標準手順を説明する日本語リファレンス。
keywords:
  - ai-cockpit
  - repository-workflow
  - work-item
  - pull-request
---

# リポジトリワークフロー

標準のレビュー単位は、1 Work Item、1 専用ブランチ、1 Pull/Merge Request です。無関係な作業を同じ Contract や PR に混ぜません。

## 開始からレビューまで

1. テンプレートリポジトリでは最新の `origin/main`、導入先では発見したリモート既定ブランチの最新コミットを取得する。
2. 専用ブランチを作成し、`baseRemote`、`baseBranch`、`baseCommit` を Contract に記録する。
3. `make ai-start TASK=<task> TITLE="..." MODE=code` で Work Item を作成する。
4. Contract の scope、outOfScope、sources、acceptance、verification、unknowns、executionDecision を確定する。
5. `before_edit` checkpoint 後に宣言範囲だけを変更する。
6. Summary を更新し、`before_finish` checkpoint を記録して `make ai-finish TASK=<task> REPORT_LANGUAGE=<conversation-locale>` を実行する。
7. archived Contract/Summary と生成 Status を確認し、ブランチを push して PR を作成する。

## リポジトリ全体の active Work Item 境界

`ai-start` は Contract、Summary、Start Receipt、Cockpit Status を書き込む前に、
linked Git worktree を列挙します。別の非 detached worktree に active
Contract/Summary の組があれば、開始を停止し、worktree のパス、ブランチ、Work
Item ID を表示します。Contract または Summary だけの壊れた組も履歴ノイズとして
無視せず、fail closed にします。これにより、serial Work Item の規則は現在の
ディレクトリだけでなくリポジトリ全体に適用されます。

後から作られた replacement delivery が、先の active Work Item を暗黙に終了させる
ことはありません。replacement の archive/PR 証跡を保持し、predecessor と cleanup
の決定を専用 corrective Work Item に記録してから、承認された境界でだけ stale な
ローカル identity を清掃します。チェックを通すために archive を書き換えたり、stale
branch を merge したり、ユーザーの変更を捨てたりしてはいけません。

## 禁止されるショートカット

- PR 前に feature branch をローカル `main` へ merge しない。
- PR が merge される前に Work Item branch を削除しない。
- 自動 merge や、`ai-close-work-item` が branch ownership を確認する前の自動 branch 削除を有効にしない。
- Contract と Summary の片方だけを削除しない。

## Corrective 後の再開

process corrective のため停止した Work Item は、corrective の PR、archive、
`ai-close-work-item`、branch cleanup、base 同期が完了するまで再開しません。
完了後、元の専用 branch を最新 remote default branch へ rebase し、
`predecessorWorkItem` を corrective の closure 証跡へ更新して、次を実行します。

```sh
make ai-resume-work-item CONTRACT=<active-contract> \
  BASE_REMOTE=<remote> BASE_BRANCH=<default-branch>
```

元の Start Receipt は変更されません。コマンドが Git ancestry、開始時の専用
branch、正確な predecessor merge、closure postconditions、archive manifest と
digest を確認し、append-only な `resumeHistory` を追加した場合だけ Contract の
baseline を進めます。Receipt、`baseCommit`、history の手編集や不連続な chain は
fail closed です。成功後は Preflight と古くなった検証を再実行します。

## 導入・アップグレード

導入とアップグレードは導入先プロジェクトの履歴に属します。移動中のテンプレートブランチではなく、公開済みテンプレート release tag を使用し、導入・設定・通常開発を別 Work Item に分けます。

## クローズ

PR が merge され、merged PR と archive 証拠が確認できた後に、明示的な承認を得て次を実行します。

```sh
make ai-close-work-item TASK=<task>
```

このコマンドは archived Contract/Summary、PR 所有権、base の fast-forward 同期、ローカル/リモート branch の削除、clean worktree、base と remote base の一致を検証します。どれかが失敗した場合は fail closed です。

`make ai-lifecycle-facts` はリポジトリのライフサイクル状態を提供する機械可読な事実源です。利用側は `state`、アクティブ Work Item 数、`notRun` を使い、状態を再計算しないでください。準備完了やエンタープライズ保証を主張するものではありません。
