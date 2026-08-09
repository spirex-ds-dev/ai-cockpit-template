---
author: Ray
title: "Java 校正を始める"
description: AI Cockpit のインストール後に使う、Java プロジェクト向けの簡単な Work Item 校正入口。
keywords: [ai-cockpit, java, maven, gradle, calibration]
---

# Java 校正を始める

AI Cockpit のインストール後にこのページを使います。始める前に JDK、Maven、Gradle、
module、service、または校正の内部仕組みを理解する必要はありません。

<!-- platform-entry: work-item-first -->
## 一度だけコピーする

```text
これは Java プロジェクトです。校正 Work Item の計画を作成してください。ただし、まだ
ファイルは変更しないでください。リポジトリを読み取り専用で確認し、どの種類の Java
プロジェクトか、見つけたもの、Unknown のもの、私が確認すべきことを平易な日本語で
示してください。JDK、build tool、module、profile、service、credential、command、CI
の事実を推測しないでください。書き込み前に私の承認を待ってください。
```

## 次に起こること

Agent はレビューできる校正 Work Item を作成します。あなたは計画を確認し、記載された
変更だけを承認します。Maven または Gradle file があるだけでは、JDK、wrapper、service、
credential、hosted CI の準備を証明しません。

## Maven の複数 module 向け修正テンプレート

internal module、private mirror、または複数の Java lane が関係する Maven failure の後だけに
使います。`pom.xml` から値を推測せず、次の事実を active Work Item に記録します。

1. 一つの project-declared **reactor command** か、明示された module dependency order のどちらかを
   選びます。選んだ command または順序付き module list、その working directory、この project で有効な
   理由を記録します。directory があるだけで individual module を実行しません。
2. Maven 実行前に、選んだ `settings.xml` の path、approved mirror が到達可能か、必要な
   private-repository access が利用可能かを記録します。credential、token、password、private repository URL を
   Work Item や command transcript に貼り付けません。
3. Java lane ごとに、必要な Java major と Maven command が選ぶ実際の `java` runtime を記録します。
   actual major が異なる lane は **blocked** です。approved toolchain を選ぶか lane declaration を修正してから
   retry します。

settings file、mirror、access grant、reactor command、dependency order、Java-major の事実が不足するときは、
不足した事実と recovery condition を含めて `blocked` を報告します。project owner の approved configuration を
取得して Work Item に記録し、宣言済み project command を再実行します。このテンプレートは Maven の設定、JDK の
install、private repository への access、adopter build の成功を行ったり証明したりしません。

## Java runtime lane gate

インストール済み Java preset は formatter、test、lint の各 command の前に runtime を確認します。
`Makefile.ai.stack` には project-approved lane と major を記録します。これは build file から推測する値ではなく、
校正する事実です。

```make
AI_COCKPIT_JAVA_LANE = java17
AI_COCKPIT_JAVA_REQUIRED_MAJOR = 17
AI_COCKPIT_JAVA_COMMAND = java
```

project-approved environment manager が `JAVA_HOME` で runtime を選ぶ場合、check は
`JAVA_HOME/bin/java` を確認します。そうでない場合は `AI_COCKPIT_JAVA_COMMAND`（既定は `PATH` の
`java`）を確認します。major が不足または不一致なら delegated command の前に **blocked** になります。
project-approved runtime を選択するか記録済み major を修正してから retry してください。preset は JDK、
`JAVA_HOME`、environment manager を install、switch、変更しません。

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-next: calibration-and-recovery -->
## 困ったとき

Work Item が質問する内容は[プロジェクト校正ガイド](../calibration.ja.md)を見てください。
Unknown がある、または確認が停止した場合は[インストールのトラブルシューティング](../../troubleshooting/installation.ja.md)
を使います。Unknown は Unknown のままにし、弱い確認で置き換えません。
