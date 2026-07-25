---
author: Ray
title: "トラブルシューティング"
description: AI Cockpit の導入・検証エラーを調査する日本語ガイド。
keywords:
  - ai-cockpit
  - troubleshooting
  - recovery
---

# トラブルシューティング

エラーの詳細な一覧は [Troubleshooting](troubleshooting.md) を参照してください。まず次の順序で状態を確認します。

## 基本確認

```sh
git status --short
make check-ai-status-consistency
make check-ai-contract CONTRACT=.ai/work-items/active/<task>.contract.json
make check-ai-scope CONTRACT=.ai/work-items/active/<task>.contract.json
```

- **Contract エラー:** `scope`、`outOfScope`、`sources`、`acceptance`、`verification`、`unknowns` を確認します。
- **Scope エラー:** 差分に Contract 外のファイルが含まれていないか確認します。
- **Preflight エラー:** `needs_human_confirmation` または `not_ready` の理由を読み、必要な証拠を Contract に追加してから再実行します。
- **Status 不一致:** `current_status.md` は手編集せず、`make generate-cockpit-status` または `make repair-ai-status` を使います。

作業中の Work Item を一部だけ削除しないでください。中止する場合は Contract と Summary を組で保全または意図的に archive し、履歴とブランチの扱いを人が確認してください。

## Wizard の復旧

- Installation Wizard が dirty worktree、remote/default branch 不在、管理対象 conflict を示した場合は、確認せずにリポジトリを修正します。Dry Run で計画だけ確認できます。
- Calibration Wizard の Unknown または stale は迂回せず、事実や理由を入力して該当 stage を再検証します。
- EOF / Ctrl+C / Pause の後は `make cockpit-calibration-wizard` で再開します。保存済み Session は activation 済みとは扱われません。
- 外部モバイルコマンドがない場合は、導入先の Gradle Wrapper、Xcode、CocoaPods、JDK を確認します。AI Cockpit は外部 toolchain を導入・切替しません。
