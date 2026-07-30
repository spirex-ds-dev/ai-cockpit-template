---
author: Ray
title: "校正セッション内部モデル"
description: "保守者と監査者のための校正事実、提案、確認、有効化の参照モデル。"
---

# 校正セッション内部モデル

これは保守者と監査者の参照であり、インストール手順ではありません。

校正 Runtime は、再開可能な Session、回答と根拠、チェックリスト根拠、段階記録、
レビュー可能な提案を保存します。Unknown を残し、事実を作りません。提案は有効な方針ではなく、
有効化には独立した人の確認と現在の根拠が必要です。

<!-- calibration-session-evidence-boundary: combined-stage-seven-column-record,labels-not-actor-proof -->
`checklistEvidence` は、統合した段階記録の七列確認表に必要な事実を保存します。
ラベルだけで本人確認や役割分離を証明するものではありません。Session の事実、
Work Item の理由と外部根拠、人による本人確認はそれぞれ別の責任です。

詳細な Runtime フィールド、古い根拠の規則、確認境界、現在の実装状態は
[Calibration Session](calibration-session.ja.md) と
[Capability Truth Matrix](capability-truth-matrix.md) を参照してください。
Work Item は理由、受入条件、担当判断、外部検証リンクを記録しますが、保存された校正事実を
置き換えず、人の身元を証明しません。
