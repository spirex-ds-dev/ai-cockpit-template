---
author: Ray
title: "30 秒で開始"
description: "クリーンな導入先からレビュー可能な AI Cockpit Work Item へ進む最短の入口。"
keywords:
  - installation
  - quick-start
  - work-item
---

# 30 秒で開始

前提、Wizard の全選択、scaffold 確認、Calibration 10 段階、最初の PR、復旧、platform 例は、完全な[日本語インストール手順](installation.ja.md)へ進んでください。

<!-- doc-domain: wizard-start -->
## Wizard を開始する

初心者は、対象プロジェクトを開いた AI コーディングエージェントへ次をコピーします。

```text
正規 public repository
https://github.com/spirex-ds-dev/ai-cockpit-template.git
から AI Cockpit 導入を始めたいです。最初は読み取り専用で、対象 Git リポジトリ、
initial commit、clean worktree、Python 3.10+、Git、GNU Make、curl を確認してください。
public release.json から固定 published tag を解決し、release/tag/digest evidence を
平易な日本語で説明してください。正確な計画を示し、この install step だけを
私が承認するまで download/execute しないでください。
commit、push、PR 作成・merge、削除、publish は禁止です。
```

期待する結果: 前提と固定 release の平易なレポート、および限定された承認質問です。private repository/mirror は[完全な日本語インストール手順](installation.ja.md)を使い、source owner から trust evidence を取得します。URL を推測しません。

### 上級者向け手動 fallback

次の block は agent を利用できない経験者が対象プロジェクトの terminal でだけ使います。Wizard が開けば成功です。エラー時は停止し、完全手順の復旧表を使用します。

<!-- command-evidence: adopter_required -->
```sh
PUBLIC_REPOSITORY="${AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY:-https://github.com/spirex-ds-dev/ai-cockpit-template.git}"
RAW_BASE="${AI_COCKPIT_TEMPLATE_RAW_BASE:-https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template}"
RELEASE_TAG="$(curl -fsSL "$RAW_BASE/main/release.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["releaseTag"])')"
INSTALLER="$(mktemp)"
trap 'rm -f "$INSTALLER"' EXIT
curl -fsSL "$RAW_BASE/$RELEASE_TAG/install.sh" -o "$INSTALLER"
AI_COCKPIT_TEMPLATE_REPO="$PUBLIC_REPOSITORY" \
  AI_COCKPIT_TEMPLATE_REF="$RELEASE_TAG" sh "$INSTALLER" --interactive
```

<!-- doc-domain: does -->
## 実行すること

Wizard はリポジトリの事実を検出し、New Adoption、Upgrade、Dry Run を選択させ、レビュー可能な書き込み計画を表示します。明示的な人の確認後にだけ書き込みます。

<!-- doc-domain: does-not -->
## 実行しないこと

プロジェクト品質コマンドの校正、production readiness の証明、commit、push、PR の作成・merge、branch 削除、release 公開、企業コンプライアンス保証は行いません。

<!-- doc-domain: after-installation -->
## インストール後に必要なこと

生成された Adoption Work Item を完了し、必要な人の承認を取得し、別 Work Item で Project Profile、Guard、CI を設定します。その後に校正と導入準備確認を行い、[標準導入ガイド](standard-adoption-guide.ja.md)と[セキュリティとリリース検証](security-release-verification.ja.md)へ進みます。
