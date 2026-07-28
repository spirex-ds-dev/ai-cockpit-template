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

<!-- doc-domain: wizard-start -->
## Wizard を開始する

初回 commit があり、worktree が clean な導入先で、公開 tag を解決し、その tag の installer を取得して Installation Wizard を開始します。copy-ready な既定値は正規 public repository を指します。明示的に検証した source だけを override してください。private repository または mirror では URL を推測せず、[インストール](installation.ja.md#エントリポイントを選ぶ)の手順を使用してください。

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
