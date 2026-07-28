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

<!-- semantic-domain: north-star -->
<!-- semantic-domain: product-boundary -->
AI Cockpit は Calibrated Human-Agent Trust を支える Repository Governance Layer です。レビュー可能なリポジトリ証拠を管理し、Agent Runtime、Workflow Engine、Security Sandbox にはなりません。

このガイドは installer が `adopt_ai_cockpit` を生成した後の導入先を対象にします。先に[インストール](installation.ja.md)の前提条件と導入を完了してください。installer が生成した Contract には、以下で使う導入前の base commit が記録されます。

<!-- doc-domain: adoption -->
<!-- semantic-domain: installation-flow -->
## Adoption

公開済み release から導入先へインストールし、`adopt_ai_cockpit` を完了して diff をレビューし、この Adoption Work Item を 1 つの PR で扱います。インストールはガバナンス実行系を配置しますが、プロジェクト適応を完了しません。

<!-- command-evidence: adopter_required -->
```sh
make ai-finish TASK=adopt_ai_cockpit
# archive bundle の commit 前に停止し、承認を取得する。
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

closure は base 同期を検証し、local/remote の Work Item branch を削除します。完全な停止条件は[インストールの Adoption 手順](installation.ja.md)を参照してください。

<!-- doc-domain: calibration -->
## Calibration

別の `configure_ai_cockpit` Work Item で Project Profile、Guard、品質コマンド、Coverage、CI の証拠をレビューします。Unknown または stale な証拠は readiness をブロックします。

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

導入先では commit、push、merge、`ai-close-work-item` の前にそれぞれ停止し、人の決定を取得します。詳細は[インストールの Adoption 手順](installation.ja.md)を参照してください。自動 merge や provider 側の自動 branch 削除で lifecycle closure を迂回しません。

<!-- doc-domain: target-project-adaptation -->
<!-- semantic-domain: supported-scope -->
## 導入先プロジェクトへの適応

Preset は出発点です。実際の module、variant、SDK/JDK、formatter、test、build plugin、Coverage path、branch policy、Hosted CI を校正します。事実が明確になるまで `generic` は fail closed です。能力状態は Capability Truth Matrix だけを根拠にします。
