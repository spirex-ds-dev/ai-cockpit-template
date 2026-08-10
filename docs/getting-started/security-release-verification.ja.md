---
author: Ray
title: "セキュリティとリリース検証"
description: "セキュリティ、サプライチェーン、version、release 判断の証拠境界。"
keywords:
  - security
  - release
  - supply-chain
  - verification
---

# セキュリティとリリース検証

現在の能力状態は [Capability Truth Matrix](../reference/capability-truth-matrix.md) だけを正本とします。このページは検証責任を説明するものであり、計画中または外部へ委譲された統制を実装済みへ昇格させません。

<!-- semantic-domain: security-limits -->
<!-- semantic-domain: prompt-injection-limits -->
セキュリティ証拠は、検証対象の正確な tag、source commit、artifact、digest を各記録に結び付けます（source-bound）。不一致があれば fail closed です。Prompt Injection 検出と入力信頼制御は既知のリポジトリリスクを下げますが、実行の封じ込め（containment）、信頼できる identity、隔離、安全な実行を証明しません。

<!-- doc-domain: release-metadata -->
<!-- semantic-domain: release-version -->
## Release metadata

`release.json` が公開済み事実の投影（published projection）です。候補記録と履歴記録は代替できません。tag、source commit、installer、archive asset、checksum を一致させます。

この projection は repository の主張であり、provider Release の公開を独立して証明するものではありません。次を分離します。

| 記録 | 証明すること | 証明しないこと |
| --- | --- | --- |
| `release.json` | repository が公開済みとして投影する version | provider Release の存在、stable 状態、Asset の取得可能性 |
| `next-release.json` | 次の candidate と予定 version | 公開、tag 作成、release readiness |
| Git tag | 不変な source reference の存在 | provider Release または Asset の公開 |
| provider draft Release | provider 側の draft record の存在 | stable な公開 |
| provider stable Release と Asset | provider が release record と指定 Asset を公開したこと | 独立検証なしの digest/source 正当性 |
| Release freeze 証拠 | candidate fact を review 用に固定したこと | 公開または post-publish 検証 |

### 導入先の経路

正規の公開 projection または別途検証した private mirror だけを使います。stable provider Release、tag 固定 metadata、source、installer、archive Asset、digest のいずれかが一致しなければ停止します。最大の tag を代替にしてはいけません。

選択した公開 tag の `release-digests.json` は、source commit を固定した後に生成される release Asset です。Quick Install はこの Asset を使い捨ての tag clone へ取得し、tag、source commit、artifact digest を検証してからでなければ導入先を書き換えません。tag tree 内のコピーは履歴上の baseline であり、後続 release の authority にはできません。取得または検証が失敗した場合、file の差し替えや失敗の回避はせず、error を保持し、正確な tag の公開 release Asset を検証します。不変の履歴 release に誤りがあれば、新しい修正 tag を公開します。

### Maintainer の経路

candidate と freeze 証拠を先に検証します。provider 公開後、stable Release と取得可能な Asset を別途 post-publish 検証してから公開 projection を変更します。candidate、publication、post-publish verification は別の状態です。

<!-- doc-domain: digest -->
## Digest

installer とダウンロード可能な archive の SHA-256 binding を検証します。呼び出し側の追加断言（caller assertion）は公開済み metadata を置き換えません。

<!-- doc-domain: provenance -->
## Provenance

Provenance は artifact を source/build statement に結び付けます。SBOM とは異なり、外部の build、署名、attestation tool で生成または検証します。AI Cockpit は委譲された証拠を記録・検証しますが、外部断言を独立して生成しません。

<!-- doc-domain: sbom -->
## SBOM

SBOM は software component の一覧です。build 方法、脆弱性がないこと、企業コンプライアンスを証明しません。

<!-- doc-domain: trust-root -->
## Trust root

公開導入の trust chain は tag 付き `release.json`、不変の tag/source identity、archive asset、digest です。証拠が欠ければ停止します。

<!-- doc-domain: private-mirror -->
## Private mirror

private mirror は同等の metadata、tag/source identity、asset、digest を公開し、独立して保護する必要があります。AI Cockpit は mirror 運営者を証明しません。

<!-- doc-domain: local-source -->
## Local source

local source 導入は意図的な非公開経路です。導入先 Work Item に source commit/path 境界を記録し、公開 release 検証とは呼びません。

<!-- doc-domain: enterprise-boundary -->
<!-- semantic-domain: enterprise-compliance-boundary -->
## Enterprise boundary

AI Cockpit は repository-local SDLC 証拠に寄与できますが、企業コンプライアンス、信頼できる ID、production 隔離、不変な外部監査、provider 統制を単独では保証しません。

次のコマンドは template release maintainer 用です。release candidate checkout で実行し、Hosted CI でも同じ check を必須にします。導入先のインストール手順ではありません。

| Check | 検証する証拠 |
| --- | --- |
| `check-release-distribution` | 公開 metadata、tag/source、installer、archive、digest の投影 |
| `check-sbom` | machine-readable な component inventory と source binding |
| `check-provenance` | artifact と source/build statement の binding |
| `check-secret-scanning` | repository の secret scanning 証拠 |
| `check-dependency-vulnerabilities` | release gate が利用する依存脆弱性証拠 |

<!-- command-evidence: hosted_executed -->
```sh
make check-release-distribution
make check-sbom
make check-provenance
make check-secret-scanning
make check-dependency-vulnerabilities
```

すべての check は同一の正確な candidate source に対して成功する必要があります。証拠が欠落、stale、または矛盾する場合は release preparation を停止し、失敗証拠を保持して[トラブルシューティング](../reference/troubleshooting.ja.md)に従います。導入先検証や local-source 検証へ読み替えてはなりません。入力と artifact ownership は[配布リファレンス](../reference/distribution.ja.md)を参照してください。

[包括的な日本語能力評価](../reference/japanese-capability-assessment.md)は別の必須公開前段階です。digest は正確な file bytes を bind し、対象 file の変更で stale になります。すべての corrective 後に生成した `final_reassessment` だけが release preflight を満たします。このページは version を公開せず、その評価を完了扱いにしません。
