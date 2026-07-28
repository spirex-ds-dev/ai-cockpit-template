---
author: Ray
title: "標準導入ガイド"
description: "導入先のインストール、校正、Work Item、CI、人のレビューに関するガイド。"
keywords:
  - adoption
  - governance
  - verification
---

# 標準導入ガイド

このページは lifecycle の要約です。完全な[日本語インストール手順](installation.ja.md)と併用し、省略された scaffold・Calibration 手順を推測で補わないでください。

初心者は完全手順の copy-ready prompt を使います。以下の command block は上級
operator の参照であり、unattended script として実行しません。

<!-- semantic-domain: north-star -->
<!-- semantic-domain: product-boundary -->
AI Cockpit は Calibrated Human-Agent Trust を支える Repository Governance Layer です。レビュー可能なリポジトリ証拠を管理し、Agent Runtime、Workflow Engine、Security Sandbox にはなりません。

このガイドは installer が `adopt_ai_cockpit` を生成した後の導入先を対象にします。先に[インストール](installation.ja.md)の前提条件と導入を完了してください。installer が生成した Contract には、以下で使う導入前の base commit が記録されます。

<!-- doc-domain: adoption -->
<!-- semantic-domain: installation-flow -->
## Adoption

公開済み release から導入先へインストールし、`adopt_ai_cockpit` を完了して diff をレビューし、この Adoption Work Item を 1 つの PR で扱います。インストールはガバナンス実行系を配置しますが、プロジェクト適応を完了しません。

```text
日本語インストール手順の Adoption closure prompt を 1 判断ずつ進めてください。
最初は local finish/archive と evidence 表示だけです。その後 commit、push/PR、
人の merge、closure を別々に待ちます。下記 block を連続 script として実行せず、
Adoption closure 前に configuration を開始しないでください。
```

<!-- command-evidence: adopter_required -->
```sh
make ai-finish TASK=adopt_ai_cockpit
```

停止して archive/diff を示し、別の commit 承認を取得します。その後だけ:

<!-- command-evidence: adopter_required -->
```sh
git add .
git commit -m "adopt AI Cockpit governance"
make check-ai-pr AI_BASE_COMMIT='<pre-adoption-commit>'
```

次の順序でライフサイクルを完了します。

1. local finish/archive を実行し、レビューのため停止します。
2. 明示的な承認を取得し、完全な archive bundle を commit してから installer が記録した base で PR check を実行します。
3. push 前に別の承認を取得します。
4. auto-merge と provider 側の source branch 自動削除を無効にして PR を作成し、人が merge します。
5. closure の承認を得てから次を実行します。

<!-- command-evidence: adopter_required -->
```sh
make ai-close-work-item TASK=adopt_ai_cockpit
```

closure は base 同期を検証し、local/remote の Work Item branch を削除します。完全な停止条件は[インストールの Adoption 手順](installation.ja.md#calibration-前に-adoption-work-item-を完全に閉じる)を参照してください。

<!-- doc-domain: calibration -->
## Calibration

別の `configure_ai_cockpit` Work Item で Project Profile、Guard、品質コマンド、Coverage、CI の証拠をレビューします。Unknown または stale な証拠は readiness をブロックします。

```text
日本語インストール手順の Calibration 10 段階を 1 件ずつ案内してください。
回答記録前に evidence、例の意味、安全な回答、PASS/STOP、owner を説明します。
proposed Profile の copy/activate を人の承認と扱わないでください。
```

<!-- command-evidence: adopter_required -->
```sh
make cockpit-doctor
make cockpit-calibrate
cp .ai/project_profile.proposed.yaml .ai/project_profile.yaml
${EDITOR:-vi} .ai/project_profile.yaml
make check-ai-project-profile
make check-ai-guard-calibration
make ai-cockpit-quality
make check-ai-adoption-ready
```

proposed Profile の copy だけでは承認になりません。人が事実をレビューし、すべての `blocking:` unknown を解消し、境界を承認し、品質コマンド、Coverage、CI、CODEOWNERS、SECURITY.md を校正してから readiness を実行します。

<!-- doc-domain: work-item -->
<!-- semantic-domain: task-outcome-fields -->
## Work Item と Task Outcome

各変更は 1 つの Contract（範囲契約）、専用 branch、Summary（引き継ぎ記録）、PR、archive（監査証拠）、merge、closure（終了検証）、branch cleanup を使います。Task Outcome は finding、risk、停止理由、解決、防止策、verification、unknown、人の決定、残存リスクを保持し、成功だけを報告してはなりません。

<!-- doc-domain: ci -->
## CI

完全な Git history を取得し、公開 project quality target と `check-ai-pr` を必須にします。template の Hosted fixture は導入先固有コマンドの証明ではありません。

```text
Contract の remote/default branch と CI requirement を読み、実行前に exact base、
required jobs、command provenance を示してください。Unknown、shallow history、
skipped job、wrong Head SHA、failure で停止します。
```

<!-- command-evidence: adopter_required -->
```sh
ADOPTER_REMOTE="${ADOPTER_REMOTE:?Contract に記録された remote を使用してください}"
ADOPTER_DEFAULT_BRANCH="${ADOPTER_DEFAULT_BRANCH:?Contract に記録された default branch を使用してください}"
make ai-cockpit-quality
make check-ai-pr AI_BASE_COMMIT="$(git merge-base HEAD "$ADOPTER_REMOTE/$ADOPTER_DEFAULT_BRANCH")"
```

<!-- doc-domain: human-approval -->
<!-- semantic-domain: human-confirmation -->
## 人の承認

導入先では commit、push、merge、`ai-close-work-item` の前にそれぞれ停止し、人の決定を取得します。詳細は[インストールの Adoption 手順](installation.ja.md#calibration-前に-adoption-work-item-を完全に閉じる)を参照してください。自動 merge や provider 側の自動 branch 削除で lifecycle closure を迂回しません。

<!-- doc-domain: target-project-adaptation -->
<!-- semantic-domain: supported-scope -->
## 導入先プロジェクトへの適応

Preset は出発点です。実際の module、variant、SDK/JDK、formatter、test、build plugin、Coverage path、branch policy、Hosted CI を校正します。事実が明確になるまで `generic` は fail closed です。能力状態は Capability Truth Matrix だけを根拠にします。
