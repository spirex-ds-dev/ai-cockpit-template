---
author: Ray
title: "厳格なインストールとサプライチェーン検証"
description: "Release 担当者とセキュリティ担当者のための AI Cockpit 導入検証の入口。"
---

# 厳格なインストールとサプライチェーン検証

Release 承認、プライベートミラー、またはサプライチェーン根拠を担当する場合に使います。
初回導入の簡単な経路で、先に読む必要はありません。

動的に解決した Release、tag に固定されたメタデータとソース commit、installer と archive
asset、それらの SHA-256 を検証してください。古い Release や移動するブランチへ黙って
切り替えてはいけません。例外は Release 担当者が確認した後で根拠を再検証します。

完全な根拠規則、プライベートミラー境界、企業責任の制限は
[セキュリティと Release 検証](security-release-verification.ja.md) にあります。
