---
author: Ray
title: "ドキュメント構成"
description: AI Cockpit の日本語ドキュメント入口と参照ページの構成。
keywords:
  - ai-cockpit
  - documentation
  - japanese
---

# ドキュメント構成

日本語利用者は [日本語 README](../../README.ja.md) から始めてください。

## 主要入口

| 目的 | 日本語ページ |
| --- | --- |
| 導入 | [インストール](../getting-started/installation.ja.md) |
| 導入先の設定 | [導入先プロジェクトの設定](../getting-started/adopter-configuration.ja.md) |
| 最初のタスク | [最初の Work Item](../getting-started/first-work-item.ja.md) |
| 概要 | [概要・コンセプトガイド](../overview.ja.md) |
| Why / What / How | [Human-Agent Trust Layer](../trust-layer.ja.md) |
| 設定 | [設定](../configuration.ja.md) |
| アーキテクチャ | [アーキテクチャ](../architecture.ja.md) |
| セキュリティと公開証拠 | [セキュリティとリリース検証](../getting-started/security-release-verification.ja.md) |
| 障害対応 | [トラブルシューティング](troubleshooting.ja.md) |
| 最短の導入 | [30 秒で開始](../getting-started/30-second-start.ja.md) |
| 導入ライフサイクル | [標準導入ガイド](../getting-started/standard-adoption-guide.ja.md) |
| 校正 | [Calibration Session](calibration-session.ja.md) |
| 能力の証拠 | [Capability Truth Matrix](capability-truth-matrix.md) |
| 日本語能力の証拠 | [日本語能力評価](japanese-capability-assessment.md) |
| Cockpit Status | [Cockpit Status の読み方](how-to-read-cockpit-status.ja.md) |
| 配布 | [配布](distribution.ja.md) |
| アップグレード | [アップグレード](upgrade.ja.md) |
| リポジトリ運用 | [リポジトリワークフロー](repository-workflow.ja.md) |
| Work Item クローズ | [Work Item ライフサイクルのクローズ](work-item-lifecycle-closure.ja.md) |
| 複雑度 | [ガバナンス複雑度](governance-complexity.ja.md) |

各日本語ページは、コマンド名、JSON フィールド名、製品名、標準規格名を除き、日本語の説明を主とします。日本語版が存在する主要経路では日本語版を正規入口とし、英語ページへ移動しなければ安全境界や手順が読めない構成にしません。Capability Truth Matrix の machine-readable な status と evidence field は翻訳せず、現在の実装事実の唯一の根拠として参照します。

対話型導入は Installation Wizard の境界としてインストールページで説明し、10 段階の校正、確認、stale、activation は日本語 Calibration Session リファレンスで説明します。Trust Layer は Why / What / How、Design Philosophy は North Star、Architecture は component/data flow、Security and Release Verification は外部公開証拠、Capability Truth Matrix は現在の実装状態を担当します。理念から実装済み能力を推測してはいけません。
