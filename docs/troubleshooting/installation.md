---
author: Ray
title: "Installation Troubleshooting"
description: "Symptom-first recovery guidance for AI Cockpit installation."
---

# Installation Troubleshooting

Stop on uncertainty. Do not use a weaker workaround to make an installation look successful.

## The working tree is not clean

Save or explain the changes first; never overwrite them during installation.

## There is no initial commit or default branch

Ask the repository owner to establish the project baseline before installing.

## Python, Make, or another required tool is missing

Install or request the approved toolchain, then repeat the readiness check.

## Release verification fails

Do not silently choose an older release. Use the
[strict verification route](../getting-started/installation-security.md).

## A Work Item is already active, files conflict, status is stale, or a PR cannot be created

Preserve the evidence, name the missing fact and owner, and start or resume the
appropriate Work Item. Do not bypass the lifecycle.

## Hosted CI did not run

Record the exact commit and failed job, then ask the repository or CI owner.

## Remove AI Cockpit

Use the separate [uninstall route](uninstall.md). It first gathers facts and
creates a reviewable removal plan; it never silently deletes project work.
