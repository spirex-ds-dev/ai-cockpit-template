---
author: Ray
title: "AI Cockpit をインストールする"
description: "対話型を既定とするインストール、レビュー、rollback、校正境界。"
audience:
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - interactive_installation_wizard
---

# AI Cockpit をインストールする

<!-- public-quality-target: ai-cockpit-quality -->

人が使う既定経路は対話型インストーラーです。対象 Git リポジトリで実行します。

<!-- command-evidence: adopter_required -->
```bash
./install.sh --interactive
```

TTY で引数なし実行した場合も同じ Wizard が開きます。明示的な installer flag は
自動化向けの安定した入口として残り、非 TTY の引数なし実行は入力待ちせず停止します。

## Wizard が表示するもの

1. Target Repository
2. Readiness
3. Installation Mode
4. Governance Profile
5. Planned Changes
6. Conflict Review
7. Explicit Confirmation
8. Installation
9. Verification
10. Next Action

確認前に、対象 path、Git と tool の readiness、New Adoption / Upgrade /
Dry Run、Lite / Standard / Strict、追加・変更 file 数、source code への影響、
installation branch、検出した conflict を表示します。表示上の既定値は Standard です。

Profile の選択は installation intent の記録だけです。Installer は Lite、Standard、
Strict を有効化しません。Project Calibration は installation 後の別 Work Item です。

## 安全境界

明示的な `yes` までは対象を変更しません。Dry Run、blocked readiness、未解決 conflict、
空回答、拒否、EOF、中断では書き込み transaction を呼びません。
Readiness または conflict evidence が `Unknown` の場合は停止し、installation 前に解決します。

Installer は commit、push、Pull Request 作成、merge、成功した installation branch の削除、
Strict の有効化、Calibration 完了の報告を行いません。Transaction failure では既存の
Installer が元 branch または detached HEAD を復元し、作成・置換 file、managed section、
Makefile、agent marker を rollback します。再試行前に、報告された対象状態を確認してください。

## 自動化と Prompt 補助

決定的な自動化では `--dry-run`、`--upgrade`、`--create-adoption`、`--stack`、
`--update-makefile` などの明示 flag を使います。Prompt 中心の Agent 導入は補助経路です。
同じ read-only plan、conflict、予定 file を表示し、Installer 実行前に明示確認を待たせます。

## Installation 後

インストール後は、独立したプロジェクト校正 Work Item を開始します。
生成された Work Item と branch を review します。Git publication は通常の人間 review
lifecycle で行います。Calibration は別 Work Item として開始し、installation だけを
production readiness evidence として扱いません。

[最初の Calibration](first-calibration.ja.md)、続いて[最初の Work Item](first-work-item.ja.md)へ進みます。

## 詳細

- [厳格な installation と supply-chain verification](installation-security.ja.md)
- [Project Calibration guide](calibration.ja.md)
- [Calibration session model](../reference/calibration-session-model.ja.md)
- [Installation troubleshooting](../troubleshooting/installation.ja.md)
- [Interactive Wizard architecture](../architecture/interactive-installation-wizard.md)
- [iOS](examples/ios.ja.md)、[Android](examples/android.ja.md)、[Java](examples/java.ja.md) の例
