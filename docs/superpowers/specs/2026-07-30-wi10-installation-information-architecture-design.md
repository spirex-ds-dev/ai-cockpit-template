---
author: Ray
title: "WI-10 Installation Information Architecture"
description: "Beginner-first, Work Item-centered trilingual installation documentation design."
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# WI-10 Installation Information Architecture

## Goal

Let a reader with no programming background install AI Cockpit and start the
next governed action without learning internal governance terminology. Keep
the governance strict, but disclose it only when the reader needs it.

## Reader routes

| Reader | Entry | Next destination |
| --- | --- | --- |
| First-time adopter | `installation*.md` | Install Runtime, then create the calibration Work Item. |
| Existing adopter | `installation*.md` | Start the required Work Item directly; do not replay installation prompts. |
| Security/release owner | `installation-security*.md` | Existing security and Release evidence requirements. |
| Project calibrator | `calibration*.md` | Question-oriented ten-domain guidance, executed in a Work Item. |
| Maintainer/auditor | `calibration-session-model*.md`, maintenance guide | Persisted model and document invariants. |
| Person blocked during installation | `troubleshooting/installation*.md` | Symptom-first recovery and STOP ownership. |

## Home-page contract

Each language page has roughly 150–250 lines and contains only: a six-stage
map; prerequisites; six purpose/result/STOP steps; a completion definition;
and links to advanced routes. The post-install action is a calibration or
configuration Work Item. An already-installed repository starts its needed
Work Item directly.

The home page may say that Unknown stops progress, an agent must not overwrite
changes or silently downgrade a Release, and approval remains separated. It
does not teach digest construction, session schema, Candidate revisions,
phase records, maintainer proof-reading, CI evidence internals, or recovery
variants.

## Safety boundary

Advanced routes retain—not weaken—the current fail-closed guarantees. Runtime
and Work Item controls enforce the protocol; documentation must not claim that
a short prompt, a page, or an agent's statement proves identity, role
separation, security isolation, or enterprise compliance.

## Verification

Documentation tests will validate all three home pages, the route map, links,
language parity, required Work Item handoff, retained safety sentences, and
absence of prohibited internal vocabulary from the happy path. Full quality
and the normal Work Item lifecycle remain required.
