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

前提条件、Wizard 全部选项、脚手架检查、十阶段校准、第一个 PR、故障恢复与平台实例，请继续阅读[完整中文安装手顺](installation.zh-CN.md)。

<!-- doc-domain: wizard-start -->
## 启动 Wizard

推荐初学者把下面提示词复制给已经打开对象工程的 AI 编程代理：

```text
请帮助我从权威公开仓库
https://github.com/spirex-ds-dev/ai-cockpit-template.git
开始安装 AI Cockpit。先只读确认：这是目标 Git 工程、已有初始 commit、
工作区干净，且 Python 3.10+、Git、GNU Make、curl 可用。
读取公开 release.json，解析固定发布 tag，并用日常语言解释 release、tag、
digest 证据。展示精确计划并得到我只针对安装步骤的批准前，不要下载或执行。
不得 commit、push、创建/合并 PR、删除或发布。
```

预期结果：平易的前提/固定 release 报告和一个有限批准问题。私有仓库或镜像必须继续按[完整中文安装手顺](installation.zh-CN.md)，向 source owner 索取信任证据，不能猜 URL。

### 高级手动备用方式

下面代码块只供无法使用代理的有经验 operator 在对象工程终端执行。成功标志是 Wizard 打开；任意错误都立即停止，并按完整安装手顺的恢复表处理。

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
