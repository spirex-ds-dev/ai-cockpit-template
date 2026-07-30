---
author: Ray
title: "Install AI Cockpit"
description: "A beginner-first, prompt-first path for installing AI Cockpit and starting calibration."
---

# Install AI Cockpit

<!-- public-quality-target: ai-cockpit-quality -->

This page is the simple path. You do not need to understand AI Cockpit's
internal records to use it. Keep your target project open, copy one prompt at
a time to your coding agent, and read the result before continuing.

## What happens after you start

```text
Open the project → check readiness → review a plan → install Runtime
→ verify the result → start a calibration Work Item
```

Installing the Runtime is not the same as calibrating it for your project.
After installation, start a separate project-calibration Work Item.

## Before you start

- Open the project where you want AI Cockpit.
- Make sure the project uses Git.
- Make sure you can create a branch and a pull request later.
- Use an AI coding agent that can read the project and show its work.

If you already installed AI Cockpit in this project, do not repeat installation.
Go directly to **Step 6** and start the Work Item you need.

## Step 1 — Open the right project

**Do this:** paste the following prompt into your agent.

```text
Check the project currently open in my editor. Read only; do not change files.
Tell me the project path, current Git branch, whether there are uncommitted
changes, and whether this is a Git repository. Reply with: Can continue,
Need my confirmation, or Cannot continue. Mark anything uncertain as Unknown.
```

**You should see:** the path, branch, and a simple status.

**Stop and ask:** if it is not the intended project or there are unexplained changes.

## Step 2 — Check installation readiness

```text
Check whether this project is ready for AI Cockpit installation. Read only.
Check Git, the required local tools, and whether the project has a usable
default branch. Tell me what is ready, what is missing, and who can help.
Use simple language. Mark uncertain facts as Unknown; do not guess.
```

**Why:** this avoids writing files into an unsuitable project.

**You should see:** a short ready / needs-help result.

**Stop and ask:** if a required tool, repository fact, or owner is Unknown.

## Step 3 — Review an installation plan

```text
Create an AI Cockpit installation plan for this project, but do not execute it.
Explain which official release will be used, which branch will be created,
which files would change, whether existing code is affected, and how to recover
if installation stops. Wait for my approval.
```

**Why:** you approve the exact change before anything is written.

**You should see:** a small, reviewable plan.

**Stop and ask:** if the plan includes unexpected files, a conflict, or an Unknown.

## Step 4 — Install the Runtime

```text
I approve the installation plan just shown. Perform only the listed Runtime
installation and its verification. Do not commit, push, create a pull request,
or merge. Stop immediately if the plan changes, a conflict appears, or a fact
is Unknown. Report the result in simple language.
```

**You should see:** the installed files and the local verification result.

**Stop and ask:** if the agent proposes extra work or would overwrite your changes.

## Step 5 — Confirm installation

```text
Read only: confirm whether AI Cockpit Runtime is installed correctly in this
project. List the evidence you checked, the files added or changed, and the
next safe action. Do not create a commit, push, pull request, or merge.
```

**You should see:** a clear installed / not installed answer.

**Stop and ask:** if the evidence is incomplete or the result is not clear.

## Step 6 — Start project calibration

```text
Start a Work Item to calibrate AI Cockpit for this project. First inspect the
project and propose the task scope; do not change project policy or source code
until the Work Item plan is ready. Ask simple questions about the source paths,
tests, generated files, important risks, and the reviewer who can confirm them.
Mark unknown answers as Unknown and stop when confirmation is needed.
```

**Why:** calibration adapts the installed Runtime to this particular project.

**You should see:** one small tracked task and a short list of questions.

**Stop and ask:** if the proposed task reaches outside calibration or lacks an owner.

## Installation is complete when

- The Runtime is installed.
- The installation result has been checked.
- A separate calibration Work Item is ready or already running.
- No commit, push, pull request, merge, or activation happened without its own approval.

## Need more detail?

- [Strict installation and supply-chain verification](installation-security.md)
- [Project calibration guide](calibration.md)
- [Installation troubleshooting](../troubleshooting/installation.md)
- [iOS](examples/ios.md), [Android](examples/android.md), and [Java](examples/java.md) examples
- [Calibration-session model for maintainers and auditors](../reference/calibration-session-model.md)

AI Cockpit must not guess Unknown facts, overwrite your work, silently fall
back to a different release, or treat one approval as permission for later
actions. The detailed controls live in the linked advanced guides.
