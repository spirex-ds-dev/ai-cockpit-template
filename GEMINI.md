---
author: Ray
title: "Gemini Operating Rules"
description: Gemini operating rules for AI Cockpit governed repositories.
keywords:
  - gemini
  - ai-agents
  - ai-cockpit
  - governance
  - agent-rules
---

# Gemini Operating Rules

Gemini uses the same collaborative AI Cockpit environment as Codex, Claude, Cursor, Antigravity, and other coding agents.

## Contract First

Do not begin implementation until the active Work Item Contract describes:

- the task boundary in `scope`;
- files and behavior excluded by `outOfScope`;
- source material used for the decision;
- remaining unknowns;
- acceptance criteria;
- verification commands;
- task-specific rules in `guidelines` (if any).

The Contract is both delegation and description: it assigns the work boundary and makes the task reviewable before implementation begins.

If the Contract contains an `intent` section, read it before implementing. When context is available, fill in at least `intent.problem` (detailed background and gap), `intent.constraints` (constraints to respect), and `intent.rationale` (why this approach). All `intent` fields are optional — do not invent content when context is not provided; leave them empty or mark them as `not provided`.

If the Contract has `mode: code`, then `unknowns` must be empty and `notCodable` must be `false`.
If `unknowns` remain or the task is `notCodable`, report that state explicitly instead of forcing implementation.

When `make ai-start ... MODE=code` or `make ai-preflight` reports `needs_human_confirmation` or `not_ready`, pause and report the Preflight Review to the user before coding continues. The command can still exit successfully in advisory mode; the agent workflow must not silently continue.

## Summary Required

Before declaring the work complete, update the matching Summary with:

- changed files and reasons;
- sources used;
- verification commands and results;
- compliance details for each of the task's guidelines in `guidelinesCompliance`;
- remaining unknowns;
- risk level and detail;
- generated files;
- destructive changes;
- observed issues.

Summary is both an audit record and a collaboration handoff for the next reviewer or agent. Use checkpoints to prevent drift during longer tasks, and record optional `intentAlignment` evidence only when it is genuinely available.
Run `make ai-finish TASK=<task> REPORT_LANGUAGE=<conversation-locale>` when the Summary is ready. The locale is explicit (`en`, `ja`, or `zh-CN`); missing or unsupported locale is a fail-closed error.

Before archive, every agent and subagent must relay the generated Outcome directly in the conversation. The handoff is not a file path: it must answer, in order, what was completed; total/blocking/warning problems; stops and their reason/stage/resolution; resolved problems and evidence; risks avoided; remaining risks; unknowns; human decisions; verification; impact; and next action. Claims without evidence references are marked `inference`, never presented as fact. Self-congratulatory claims (for example, dramatically improving quality or saving time) are forbidden without quantitative evidence.

Closure is not complete until the archived evidence is verified and both local and remote branches, plus local worktrees, are checked clean. Any residue remains a blocking Outcome and must be reported with its exact location and recovery action.
