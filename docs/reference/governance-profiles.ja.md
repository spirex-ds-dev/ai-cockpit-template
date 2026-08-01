---
author: Ray
title: "Governance Profile"
description: AI Cockpit Work Item 向けの Lite、Standard、Strict、Release リスクベース品質ルーティング。
audience:
  - adopter
  - maintainer
status: current
authority: translation
canonical: docs/reference/governance-profiles.md
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - risk_based_quality_routing
keywords:
  - ai-cockpit
  - governance-profile
  - quality-routing
---
# Governance Profile

AI Cockpit は Repository Evidence で正当化できる最小の Quality Graph を選択します。
順序は `light < standard < strict` です。混在変更は最高 Profile、未知または
空の Path Evidence は少なくとも Standard になります。Release は第 4 の Profile ではなく、
操作固有の検証エスカレーションです。

## Profile

| Profile | 代表的な変更 | Dispatch target |
| --- | --- | --- |
| Light | 文書、Comment、非実行 Example、Format のみ | `quality-fast` |
| Standard | 通常 Source、Test、Bug Fix、小規模 Refactor | `quality-standard` |
| Strict | Governance、CI、Installer、Security、Dependency、破壊的/Public API、Migration、Calibration、Evidence Schema | `quality-full` |

Standard は既存の Fast、Project Test、Reference Impact、Full Test Weakening の所有者を
再利用し、Strict は既存の Full Graph を再利用します。Release 関連の operation、resource、
capability claim を持つ Strict Work Item だけが `quality-release` の release-preflight と
distribution verification を追加で実行します。`make quality` は Full の
互換 Alias のまま、`make ai-cockpit-quality` が Evidence-based Entry Point です。

## Contract Evidence

Contract の `governanceProfile` は `selected`、`source`、`reasons`、`override` を記録します。
Router は `.ai/quality/governance-routing.yaml` を読み、Contract base からの Commit、Stage、
Unstage、Untracked Path を統合し、`target/quality/governance-profile.json` に自動/選択 Profile、
理由、Group、Dispatch、Override 判定を出力します。不正 Git base、Traversal、Policy 破損は
Fail Closed です。生成された Current Status、Work Item Start Receipt、現在の Outcome は証拠として残りますが、
単独では Profile を上げません。Evidence-only Diff は Standard になります。

最初の Work Item より前の導入先には Contract base がありません。この境界に限り Router は
`HEAD` を基準にし、Stage、Unstage、Untracked の Installer 変更を引き続き含めます。明示的な
`--base` または Active Contract の `baseCommit` が常に優先され、不正な明示 base は Fail Closed
のままです。

```sh
make ai-cockpit-quality CONTRACT=.ai/work-items/active/<task>.contract.json
make ai-cockpit-quality GOVERNANCE_PROFILE=strict
```

明示 Profile は自動結果を下げられません。降格には `human_override`、Approval Evidence、
理由、認識した Risk、実行しない Check、期限または現在 Work Item の厳密な Scope が必要です。
期限切れ、不完全、不一致の Evidence は拒否され、自動 Profile に戻ります。永続的な暗黙例外は
作成しません。

## 境界

Receipt は Repository Evidence であって Authorization Token ではありません。承認者の本人確認、
Hosted Branch Protection の変更、Path だけによる意味的 Risk の証明、Local/Cache 結果による
Release Evidence の代替は行いません。Adopter 固有の Strict Check は `AI_COCKPIT_STRICT_CHECK` で設定でき、
Work Item Lifecycle Gate は `ai-finish` が独立して実行します。Release Check が未設定なら Release は Fail Closed です。
