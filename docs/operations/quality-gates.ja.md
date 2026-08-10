---
author: Ray
title: "Quality Gate 運用"
description: AI Cockpit の Quality Gate、証拠、Work Item 追跡の運用説明。
capabilityClaims:
  - risk_based_quality_routing
keywords:
  - ai-cockpit
  - quality-gates
  - ci
  - evidence
---

# Quality Gate 運用

AI Cockpit は `make quality` の後方互換性を維持します。`make quality` は
`make quality-full` と同じです。短いローカルフィードバックには
`make quality-fast`、リリース準備には `make quality-release` を使います。

## Adopter の quality 設定

インストール済み template は常に `make quality` を提供します。実際の
format、lint、test は adopter が所有する `Makefile.ai.stack` の
`PROJECT_FORMAT_CHECK`、`PROJECT_LINT`、`PROJECT_TEST` に委譲されます。
三つすべてを project の command で設定してください。未設定または空の値は、
該当する variable を示す recovery message で fail-closed になります。

Hosted snapshot preparation は同じ entrypoint を必要とし、quality が失敗した
場合は receipt を書きません。`Makefile.ai.stack` の不足 variable を設定して
から、`make quality`、続けて
`make ai-prepare-hosted-verification-snapshot CONTRACT=<active-contract>` を実行します。

## 責任範囲

- `quality-fast` は format、lint、diff、schema、文書メタデータ、Project Profile、status policy を担当します。
- `quality-full` は完全なテスト、証拠、サプライチェーン、プロジェクト整合性を追加します。個別の Trust テストはデバッグ用の独立 target として残し、完全な pytest 後に再実行しません。
- `quality-release` はインストールとリリース証拠を追加します。Fast の結果やキャッシュ結果はリリース証拠の代わりになりません。
- Compatibility job は Python/platform matrix の検証だけを行い、完全な quality graph は実行しません。
- Hosted smoke では完全な `project-test` 集合の各 entry に唯一の owner を割り当てます。履歴 duration で均衡化した `project-test-core`、`project-test-governance`、`project-test-installer`、`project-test-lifecycle`、`project-test-release` runner が source-bound な JUnit、coverage、timing、log、receipt artifact を publish します。`project-test-aggregate` は `always()` の fail-closed consumer であり、missing、cancelled、failed、stale、wrong-SHA、不完全な shard evidence を拒否してからでなければ `template-smoke` は aggregate receipt を再利用できません。ローカルの `make project-test` は serial diagnostic の等価入口として残ります。
- release-blocking の全履歴 secret scan には唯一の独立 owner `secret-scan` を割り当て、project-test graph と並行して開始します。`template-smoke` は source checkout scan の成功と fail-closed aggregate receipt の両方を待機します。これは回避可能な終端待機だけを除去し、security verification は除去しません。
- Adopter 向け配布物には runtime skeleton、policy、必要な baseline を含めますが、template 保守用の Work Item starts、decision 履歴、archive 履歴は含めません。Installer は走査前にそれらの tree を除外し、一回の install 中では不変の source inventory を再利用します。

## 証拠と fail-closed

`make quality` の各実行は `target/quality/sessions/` 配下に新しい directory を作成し、commit、Hosted run/attempt、または一意な local identity に結び付けます。`scripts/run_quality_gate.py` は Gate 出力をリアルタイムに stream しながら、各 Gate の完全な log と JSON timing を記録します。証拠には session/run identity、command、commit、所要時間、終了コード、timeout または cancel 状態、cache 状態、出力 digest、長さを制限した末尾が含まれます。Top-level invocation は終了時に `current-session.txt` を自分の session へ再バインドするため、nested dry-run や test fixture が Hosted 公開対象として選ばれることはありません。Telemetry wrapper は検証済みで開いている Make jobserver descriptor だけを引き継ぎ、無効または利用不能な descriptor は転送しません。`project-test` は JUnit 証拠も書き出し、log には最も遅い test の report が含まれます。`scripts/summarize_quality_gates.py` は wall time、Gate 合計時間、parallel efficiency、最長 Gate、失敗末尾、skip、最終判定を JSON と Markdown に出力します。

Hosted CI は `if: always()` で session directory 全体と wrapper log を upload するため、success、failure、cancel、timeout のいずれでも診断証拠を保持します。timing または artifact 証拠がない場合は fail-closed とし、cache hit を最終証拠にはしません。

`template-smoke` の残りの quality 実行には 25 分の実行上限があります。`timeout` は最初の signal を無視する descendant process に対して、有限の 30 秒の強制終了 grace を続けます。heartbeat と診断証拠を保った terminal failed gate になり、PR が無期限に in-progress のままになることはありません。この上限は quality gate の skip や downgrade を許可しません。

smoke を手動実行する時は purpose を明示します。source-bound な性能測定には
`gh workflow run smoke.yml --ref <measurement-branch> -f purpose=hosted_measurement`
を使います。`release_preparation` は引き続き厳格な default で release-state
証拠検査を実行し、性能測定の dispatch は release intent を主張しません。

baseline と candidate sample は別々の receipt に保持します。比較には、同じ厳密な SHA/tree と runner class 上の、成功した一意の workflow run/attempt sample が少なくとも五つ必要です。cache hit は検証の代わりになりません。

Hosted の前後 timing は推測ではなく証拠です。WI-20 の baseline または hosted run を取得できない場合は、構造化した `not-run` 理由、run ID、制限を記録し、改善を主張してはいけません。

`scripts/determine_quality_scope.py` は変更 path から Fast、Full、Release を決定します。未知または混在する範囲は Full になります。並列実行は `.ai/quality/gates.yaml` で出力の競合がない場合に限ります。

## トレーサビリティ

すべての Work Item は PR、merge、archive、branch cleanup の前に「指示 → 計画 → 実装 → 受入」の双方向追跡を検証しなければなりません。実装証拠のない受入項目、または計画された受入項目のない実装指示は漏れとして記録し、修正してから進めます。

完全な流れは Contract、実装、検証と Summary、PR、merge、`make ai-close-work-item`、最後に local/remote branch cleanup です。本書は実行証拠を説明するものであり、AI Cockpit が Security Sandbox であることや、単独で enterprise compliance を保証することを主張しません。
