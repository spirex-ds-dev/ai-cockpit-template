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

無効化、通常の証拠保持アンインストール、または purge の途中で停止した場合は、
手動で残存ファイルを削除せず、
[日本語インストール手順の「AI Cockpit を無効化またはアンインストールする」](../getting-started/installation.ja.md#15-ai-cockpit-を無効化またはアンインストールする)
へ戻ってください。proposal（削除候補書）、drift/ownership（導入時からのずれと
所有者）、detached executor（別プロセスの公開削除機能）、receipt（完了記録）の
うち、最後に PASS した 15.x 段階を確認してから再開します。

## Wizard の復旧

- Installation Wizard が dirty worktree、remote/default branch 不在、管理対象 conflict を示した場合は、その場で変更せず停止します。原因と復旧計画を確認し、人がその修正だけを別途承認してから対応します。Dry Run では計画だけを確認できます。
- Calibration Wizard の Unknown または stale は迂回せず、事実や理由を入力して該当 stage を再検証します。
- EOF / Ctrl+C / Pause の後は `make cockpit-calibration-wizard` で再開します。保存済み Session は activation 済みとは扱われません。
- 外部モバイルコマンドがない場合は、導入先の Gradle Wrapper、Xcode、CocoaPods、JDK を確認します。AI Cockpit は外部 toolchain を導入・切替しません。
