---
author: Ray
title: "実フィクスチャ証拠"
description: "フィクスチャ実験におけるライフサイクル事実と証拠境界。"
keywords:
  - lifecycle
  - evidence
---

`make ai-lifecycle-facts` は、Bootstrap、Calibration、Governed Development、No Active Work Item の状態を機械可読 JSON として出力します。これは読み取り専用の観測であり、`readiness` と `enterpriseAssurance` は `not_claimed`、プロバイダー資産と外部エンタープライズ保証は `not_run` のままです。ローカルのフィクスチャ実行結果からセキュリティ、コンプライアンス、本番準備を推論してはいけません。

## End-to-End Adoption Validation

完全なローカルマトリクスは次のコマンドで実行します。

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 scripts/end_to_end_adoption_validation.py --output target/end-to-end-adoption-validation.json
```

マトリクスは、Python service、TypeScript web application、Java backend、Android application、iOS Swift Package、Flutter application、mixed monorepo の使い捨て Git リポジトリを作成します。各リポジトリで実際のローカルインストール、Calibration、Adoption Work Item 作成、安全な小変更と復元、Scope/Test Weakening の probe、finish/archive、集約 PR 検証、ローカル bare remote での merge と branch cleanup、Upgrade、意図的に失敗させた Upgrade の Rollback を実行します。

攻撃的ケースは、テスト削除、skip 追加、Coverage 低下、参照中関数の削除、外部 Markdown 命令、偽造承認、未実行テストの成功主張を含みます。`blocked` は自動実行を進められないという意味であり、依頼者の悪意を証明するものではありません。インストール失敗マトリクスでは Dirty worktree、不正 Marker、Makefile conflict、Detached HEAD の復元、利用不能な Remote、不正 Release metadata も確認します。

証拠種別は明確に分離します。

- `local_real_execution`: 使い捨てローカルリポジトリで実際に実行した操作。
- `policy_probe`: 危険な要求自体は実行せず、正規の決定的 Policy で評価した結果。
- `local_provider_simulation`: ローカル bare Git remote による merge-base、push、merge、branch cleanup。GitHub や Provider の証拠ではありません。
- Hosted Provider、Provider Identity、Device/Signing、Enterprise Assurance は `not_run` または `not_claimed` のままです。

七つの外部 Toolchain をダウンロードしないため、Fixture の finish は `SKIP_QUALITY=true` を使用します。プロジェクト固有の Compile、Device 実行、Signing、Hosted CI は別の Delegated Evidence であり、未実行の Project Quality を成功として報告しません。
