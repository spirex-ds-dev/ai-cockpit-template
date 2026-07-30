---
author: Ray
title: "Project Calibration Guide"
description: "Question-oriented project calibration performed through a Work Item."
---

# Project Calibration Guide

Run calibration in a Work Item after Runtime installation. The agent asks, the
project owner confirms, and Unknown stays blocked until evidence arrives.

## Questions to confirm

1. What role does this repository have?
2. Which languages and stacks are actually used?
3. Where are production sources and tests?
4. Which files are generated or supplied by vendors?
5. Which paths are critical or risky?
6. Which local and hosted quality commands are authoritative?
7. Who reviews changes and releases?
8. What risks, exceptions, and Unknown facts remain?
9. Is the project ready to adopt blocking controls?
10. What must be rechecked after an upgrade or major change?

The Work Item turns answers into a reviewable proposal. It does not activate
policy, prove ownership, or replace human approval by itself. For platform
examples, use [iOS](examples/ios.md), [Android](examples/android.md), or
[Java](examples/java.md). For stored internal mechanics, see the
[Calibration-session model](../reference/calibration-session-model.md).
