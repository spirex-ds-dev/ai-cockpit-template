---
author: Ray
title: "Human-Agent Trust Layer（人間・エージェント信頼レイヤー）"
description: AI Cockpit の存在理由、統制対象、証拠・fail-closed 制御・信頼チェーン・サプライチェーン証拠・人間の判断の連携を説明する。
keywords: [ai-cockpit, trust-layer, human-agent-trust, evidence, human-decision]
---

# Human-Agent Trust Layer（人間・エージェント信頼レイヤー）

AI Cockpit は Repository Governance Layer（リポジトリガバナンス層）です。レビュー可能な証拠を使い、統制対象の変更を続行できる時、人間へ制御を返す時、統制された経路を停止する時を判断します。SKILL、Agent Runtime、Security Sandbox ではありません。

3 言語版はすべて完全な同等版です。英語版を文言の権威版とし、中国語版と日本語版も同じ構造、境界、実装証拠、制限を保ちます。

<!-- section-id: why -->
## なぜ存在するか（Why）

エージェントはもっともらしい説明を生成できても、リポジトリ変更を信頼するための証拠を生成するとは限りません。したがって Human-Agent Trust は絶対的な信頼ではなく、校正された信頼です。既知のこと、欠けていること、誰が判断すべきか、どう復旧するかを明示します。

中心原則は Evidence over Self-Declaration（自己申告より証拠）です。AI Cockpit governs evidence; it does not replace evidence-producing tools（AI Cockpit は証拠を統制しますが、証拠を生成するツールを置き換えません）。チャット上の主張、エージェントの自信、自己申告の承認は、独立した権限付与ではありません。

Trust Layer は、リポジトリガバナンス、fail-closed 制御、信頼チェーン、委任ドメイン証拠、人間の判断を接続します。安全な次の行動を明確にしますが、ローカルなリポジトリ層だけで組織、プロバイダー、モデル、本番環境の全属性を証明するとは主張しません。

<!-- section-id: what -->
## 何を統制するか（What）

AI Cockpit はリポジトリ内の意思決定境界を統制します。人間の依頼を Work Item Contract に結び付け、ポリシーと範囲を評価し、検証を記録し、人間レビュー向けに結果を圧縮し、判断を再構成できる証拠を保存します。

7 つのガバナンス層は次のとおりです。

1. **実行境界** — 要求された操作、範囲、権限、許可された効果を結び付ける。
2. **制御の返却** — 証拠が欠落、失効、矛盾、または高リスクなら停止し、人間の判断を求める。
3. **既知リスク防護** — リポジトリのゲートが対象とする決定論的な注入、根拠のない主張、荒唐無稽な要求、バイパス、不安全操作を拒否する。
4. **完全な信頼チェーン** — 各システムが実際に生成した場合に、SHA-256、Git History、Digital Signature、Branch Protection、Hosted CI / External Audit Evidence、Human Approval をつなぐ。
5. **ソフトウェア・サプライチェーン証拠** — SBOM、Provenance、リリース識別子、チェックサム、スキャン、プロバイダー証拠を記録する。ただし委任証拠をネイティブな証明とは扱わない。
6. **人間の判断の圧縮** — 状態、Trust Signal、変更、問題、停止理由、未知、人間の判断、証拠の根拠、次の行動を、スコアや見せかけの信頼度なしに示す。
7. **アーカイブと復旧** — Contract、Summary、イベント、判断記録、リリース証拠、Archive Manifest を保存し、停止・完了した経路をレビューおよび復旧可能にする。

完全な信頼チェーンは、AI Cockpit の単一機能ではなく組み合わせです。SHA-256 はバイト列を束縛し、Git History はリポジトリの祖先関係を束縛し、Digital Signature は外部署名システムが提供する場合に署名者を束縛し、Branch Protection はホスト型リポジトリのポリシーを束縛し、Hosted CI / External Audit Evidence はプロバイダーまたは監査者の結果を束縛し、Human Approval は責任者の判断を記録します。欠けたリンクは欠けたままです。

SBOM と Provenance は異なります。SBOM はソフトウェア成果物のコンポーネントと依存関係を記述します。Provenance は成果物がどのソースから、どのビルド処理、識別子、環境で生成されたかを記述します。SBOM は Delegated Domain Evidence（委任ドメイン証拠）です。AI Cockpit は記録・統制できますが、ファイルが存在するだけでドメインの事実を生成・独立検証することはありません。

AI Cockpit は、識別、実行時分離、改ざん不能な監査ログ、ブランチ保護、デジタル署名、脆弱性がないこと、企業コンプライアンスを単独では保証しません。AI Cockpit is not a Security Sandbox（AI Cockpit はセキュリティサンドボックスではありません）。企業統制は導入先、関係するプロバイダー、監査者の責任です。

<!-- section-id: how -->
## どのように統制するか（How）

統制された経路は次のとおりです。

```text
人間の意図 → Raw Request Binding → Work Item Contract → Preflight
→ Requested Operation / Capability Mapping → 変更
→ 検証と外部証拠 → Human Decision and Recovery
→ Task Outcome / Status → Archive Manifest
```

Raw Request Binding は作業を開始した依頼を保存します。Requested Operation は target、action、environment、effect、authority 要件を明示します。Capability Mapping はリポジトリポリシーから必要な能力を導出し、自己申告の能力一覧で未マッピングの操作を許可することはできません。

Preflight は既定で enforced profile を使用します。`ready` の新しいレポートだけが続行できます。`not_ready`、`needs_human_confirmation`、`human_decision_recorded`、失効、矛盾、失敗した証拠は経路を停止します。人間の判断はワークフロー上の不確実性を解消しますが、未検証のチェックを合格には変えません。復旧では証拠を追加・修正し、該当チェックを再実行します。

Human Decision and Recovery には、何が起きたか、なぜ重要か、選択肢、推奨、証拠、再開条件を記録します。判断結果は Work Item と共にアーカイブしますが、テスト、CI、セキュリティ、リリース、識別、企業統制の証拠の代わりにはなりません。

<!-- section-id: current-implementation -->
## 現在の実装（Current Implementation）

現在のリポジトリはローカルで決定論的な Trust Layer を実装しています。以下の実装詳細は権威ある内容であり、概念をきれいに見せるために削除してはいけません。

- **Unsupported Claim Regression Gate**（`make unsupported-claim-regression`）は、根拠のない完了、承認、実行、ファイル、リリース主張を拒否します。
- **`delusion-test-gate`**（`make delusion-test-gate`）は、荒唐無稽、バイパス、注入、曖昧な作業を含む有限の既知シナリオ回帰を実行します。
- **Guard Signal Envelope** は `signalId`、`state`、`confidence`、`evidence`、`policyReference`、`humanDecisionAllowed`、`safeAlternatives` と、互換用の `name`、`value`、`sources` を保持します。決定論的な confidence は証拠品質であり、権限ではありません。
- **Preflight enforced profile** は `.ai/guards/preflight_review_policy.yaml` に設定され、新しく計算された `ready` レポートだけが統制された start と finish を通過します。
- **Raw Request Binding**、**Requested Operation**、**Capability Mapping** は該当する Contract v2 code Work Item の境界です。
- **Human Decision and Recovery** は構造化された依頼と証拠を保存し、その後 Preflight とプロジェクト検査の再実行を求めます。
- **Archive Manifest** は自己参照しないアーカイブ記録に、凍結された Contract と Summary の SHA-256 ダイジェストを記録します。

これらはリポジトリ内の実装事実です。普遍的な意味リスク分類、一般的な日本語モデル流暢性、プロバイダー識別、実行時分離、企業 readiness を証明しません。WI-16 の日本語評価は決定論的な日本語ガバナンス経路に限定され、一般的な流暢性の non-claim を意図的に残しています。

<!-- section-id: deterministic-coverage -->
## 決定論的なカバレッジ（Deterministic Coverage）

ゲートは、欠落・失効した証拠、根拠のない主張、不正な Work Item 状態、範囲違反、raw request と操作の不一致、選択された prompt injection 指示、不安全な重要領域効果、人間確認が必要なシナリオを対象とします。認識できるケースでは fail-closed です。

[実在する不合理要求と注入ケースの評価](reference/real-absurd-injection-cases.ja.md) は、12 件の具体的な負例と現在の結果を記録します。現在直接カバーされる 5 件の入力信頼ケースと、レビューが必要な 7 件のリポジトリ/ライフサイクル証拠不足を区別します。依頼者や文書が悪意を持つとは推断せず、束縛されていないゲートを防護済みとは主張しません。

エージェントの内部状態、すべての言語のニュアンス、普遍的な prompt injection 防御、外部統制の設定済み状態を証明するものではありません。Capability Truth Matrix が現在の実装状態の唯一の事実源です。この文書の理念から、planned、template-only、adopter-installed、externally required を implemented に格上げしてはいけません。

<!-- section-id: machine-readable-evidence -->
## 機械可読な証拠（Machine-Readable Evidence）

機械可読な証拠チェーンは Contract v2、Guard Signal、Preflight レポート、テスト・品質結果、Task Outcome、Cockpit Status、人間の判断依頼・証拠、リリース証拠、Archive Manifest で構成されます。各記録にはライフサイクル上の所有段階があり、パス、コマンド、コミット、ダイジェスト、プロバイダー結果で参照します。

Native Governance Evidence はこのリポジトリの統制コマンドと schema が生成します。Delegated Domain Evidence は独立ツール、ホスト型プロバイダー、導入先プロジェクト、監査者、署名サービス、SBOM/Provenance 生成器、脆弱性スキャナーが生成します。AI Cockpit は委任証拠を要求、束縛、表示、アーカイブできますが、事実を静かに作り出すことはできません。

<!-- section-id: commands-and-demonstration -->
## コマンドとデモ（Commands and Demonstration）

オフラインで安全な失敗指向デモは次のとおりです。

```sh
./docs/examples/trust-layer-demo.sh
```

品質・ライフサイクル経路で証拠を生成するコマンドは次のとおりです。

```sh
make unsupported-claim-regression
make delusion-test-gate
make ai-preflight CONTRACT=.ai/work-items/active/<task>.contract.json
make ai-finish TASK=<task>
make ai-close-work-item TASK=<task>
```

出力、入力コミット、環境、所有 Work Item が記録されて初めて、コマンド結果は証拠になります。デモはオフラインで無害であり、ホスト型リリースや企業統制をシミュレートしません。

<!-- section-id: boundaries-and-navigation -->
## 境界とナビゲーション（Boundaries and Navigation）

各文書は次の権威範囲で使用します。

- [Design Philosophy](philosophy/design-philosophy.md) — North Star と設計原則。
- [Architecture](architecture.md) — コンポーネント、証拠の所有、データフロー。
- [セキュリティとリリース検証](getting-started/security-release-verification.ja.md) — リリースレベルの外部証拠要件。
- [Capability Truth Matrix](reference/capability-truth-matrix.md) — 現在の実装状態の唯一の事実源。
- [Enterprise Control Checklist](reference/enterprise-control-checklist.md) — 導入先と外部統制の責任。
- [Documentation Architecture](reference/documentation-architecture.ja.md) — 権威ある役割の地図。

README は短い入口です。この文書は完全な Trust Layer の権威説明です。どちらも証拠を生成するツールや外部統制の代わりにはなりません。
