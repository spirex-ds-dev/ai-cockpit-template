---
author: Ray
title: "導入準備"
description: インストール後リポジトリ向けの AI Cockpit 導入完了ガイド（日本語）。
---

# 導入準備

[English](adoption.md)

インストールはガバナンス runtime を配置するだけです。プロジェクト固有の品質コマンド、Coverage Guard パス、pull request CI が正しいことは自動では証明されません。

AI Cockpit を本番ゲートとして必須化する前に、次を完了してください。

## 3 フェーズの導入フロー

```sh
make ai-onboard
```

上記は次の 3 フェーズを順に実行します。

| フェーズ | 内容 | 主なコマンド |
| --- | --- | --- |
| 1. 環境確認 | Python、Git、Make、初期 commit、品質コマンド設定の確認 | `cockpit-doctor` |
| 2. キャリブレーション | 検出結果から Project Profile 提案を生成し、人間確認を促す | `cockpit-calibrate` |
| 3. 導入準備 | Profile、Guard、Coverage、CI の残タスクを一覧化 | `check-ai-adoption-ready` |

個別実行が必要な場合:

```sh
make ai-onboard PHASE=1
make ai-onboard PHASE=2
make ai-onboard PHASE=3
```

## 詳細チェックリスト

1. `make cockpit-doctor` でプロジェクト事実、証拠、信頼度、候補境界、Guard 不一致、unknowns を記録する。
2. `make cockpit-calibrate` を実行する。提案された Profile を承認済みとみなさない。
3. 明示的に確認した境界と承認メタデータで `.ai/project_profile.yaml` を作成する。`blocking:` unknowns をすべて解消する。
4. `make check-ai-project-profile` と `make check-ai-guard-calibration` で Profile と Guard を検証する。
5. `Makefile.ai.stack` のプレースホルダを置き換え、`make ai-cockpit-quality` が成功することを確認する。
6. Coverage パスをレビューし、`adoptionReviewed: true` を設定する。
7. CI で完全 Git 履歴を取得し、`make check-ai-pr AI_BASE_COMMIT=<merge-base-sha>` と `make ai-cockpit-quality` を独立した必須チェックとして実行する。
8. `make check-ai-adoption-ready` で静的設定の完全性を検証する。

Doctor は `target/` 配下のレポート以外は読み取り専用です。Calibration は `.ai/project_profile.proposed.yaml` のみを書き込み、Guard は上書きしません。確定 Project Profile はプロジェクト所有で、アップグレード後も保持されます。

`make check-ai-adoption-ready` は fail-closed ですが、Profile 承認や readiness 自体はセキュリティ証明ではありません。`make ai-cockpit-quality` と `check-ai-pr` の CI 成功を独立した必須チェックとして要求してください。

## 設定 Work Item との関係

初回インストール後は `configure_ai_cockpit` Work Item が Project Profile、Guard、品質コマンド、CI 適応を所有します。上記チェックリストを完了したら:

```sh
make ai-finish TASK=configure_ai_cockpit
git add .
git commit -m "configure AI Cockpit for this project"
make check-ai-pr AI_BASE_COMMIT=<configure-base-commit>
```

その後、通常の governed 開発を開始できます。

```sh
make ai-start TASK=<task> TITLE="..." MODE=code
make ai-finish TASK=<task>
```
