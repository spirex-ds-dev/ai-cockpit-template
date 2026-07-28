---
author: Ray
title: "30 秒开始"
description: "从干净对象工程到可评审 AI Cockpit Work Item 的最短入口。"
keywords:
  - installation
  - quick-start
  - work-item
---

# 30 秒开始

<!-- doc-domain: wizard-start -->
## 启动 Wizard

在已有初始提交、工作区干净的对象工程中，解析公开 tag、下载该 tag 的 installer，再启动 Installation Wizard。可直接复制的默认值指向权威公开仓库；只有明确验证过其他来源时才覆盖。私有仓库或镜像请改用[安装指南](installation.md#choose-an-entrypoint)，不要猜测下载地址。

<!-- command-evidence: adopter_required -->
```sh
PUBLIC_REPOSITORY="${AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY:-https://github.com/spirex-ds-dev/ai-cockpit-template.git}"
RAW_BASE="${AI_COCKPIT_TEMPLATE_RAW_BASE:-https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template}"
RELEASE_TAG="$(curl -fsSL "$RAW_BASE/main/release.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["releaseTag"])')"
INSTALLER="$(mktemp)"
trap 'rm -f "$INSTALLER"' EXIT
curl -fsSL "$RAW_BASE/$RELEASE_TAG/install.sh" -o "$INSTALLER"
AI_COCKPIT_TEMPLATE_REPO="$PUBLIC_REPOSITORY" \
  AI_COCKPIT_TEMPLATE_REF="$RELEASE_TAG" sh "$INSTALLER" --interactive
```

<!-- doc-domain: does -->
## 它会做什么

Wizard 检测仓库事实，让人选择 New Adoption、Upgrade 或 Dry Run，并展示可评审的写入计划；只有得到明确人工确认后才写入。

<!-- doc-domain: does-not -->
## 它不会做什么

它不会完成项目质量命令校准，不会证明生产就绪，不会 commit、push、创建或合并 PR、删除分支、发布版本，也不会赋予企业合规保证。

<!-- doc-domain: after-installation -->
## 安装以后还要做什么

完成生成的 Adoption Work Item，取得规定的人工批准，在独立 Work Item 中配置 Project Profile、Guard 和 CI，执行校准并验证采用就绪。继续阅读[标准采用指南](standard-adoption-guide.zh-CN.md)和[安全与发布验证](security-release-verification.zh-CN.md)。
