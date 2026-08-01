---
author: Codex
title: "Calibration Profiles"
description: プロジェクト校正向けの Lite、Standard、Strict コントロール要件。
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - project_calibration_profile_proposal
keywords:
  - ai-cockpit
  - calibration
  - governance-profile
---

# Calibration Profiles

Calibration Profile は、導入先が証拠化する常設コントロールを選択します。
Work Item の Quality Routing とは別の仕組みです。レベルは
`lite < standard < strict` の累積順序です。
この方針と Proposal はテンプレートで提供されますが、導入先での導入済みや
有効化を証明しません。

| レベル | このレベルで追加される必須コントロール |
| --- | --- |
| Lite | source/test/generated/protected path、quality command、default branch、project owner、reviewer、主要 Unknown |
| Standard | file ownership、scenario coverage、destructive change、dependency、CI、public API、lifecycle、delegated evidence policy |
| Strict | Reviewer/Owner 分離、external identity/release evidence、SBOM、provenance、signed tag、branch protection、audit retention、incident/exception policy |

Lite は supply-chain、release attestation、二者 activation、enterprise audit、
external identity を必須にしません。Deferred は不要の証明ではなく、現在の
レベルでは必須でないという記録です。

`.ai/project_profile.yaml` の `calibrationProfile` は level、`selectedBy:
human`、時刻、理由、required/deferred controls を保持します。control list は
`.ai/calibration/profiles.yaml` と完全一致しなければなりません。Proposal は
`pending_human` のまま生成され、人間の選択を偽装しません。

```sh
make check-ai-calibration-profile
make check-ai-calibration-profile ARGS="--previous-level standard"
```

Transition の検証時は、review 済み base evidence から previous level を渡します。
previous level がなければ repository history を検査したとは主張しません。
Upgrade は単調に許可されます。Downgrade には旧/新 level、理由、閉じる
control の完全な一覧、risk acceptor、有効 path scope が必要です。不足時は
旧 level を復元するか、境界付き transition evidence を完成させて再実行します。

`selectedBy: human` は authority class の記録であり、外部 ID 認証、compliance
認証、release attestation、delegated tool 実行の証明ではありません。
