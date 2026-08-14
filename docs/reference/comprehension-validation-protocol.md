---
author: Ray
title: "P0 Reader Comprehension Validation Protocol"
description: "A bounded, anonymized study protocol for testing whether a nontechnical reader understands the P0 documentation journey."
audience:
  - adopter
  - reviewer
  - maintainer
authority: implementation_record
---

# P0 Reader Comprehension Validation Protocol

This is a study protocol, not a comprehension result. It is the controlled handoff for an independent reader study after the English, Simplified Chinese, and Japanese P0 routes have been revised.

## Eligibility and ethics

- Recruit people who do not work on AI Cockpit and who can read the selected language.
- Prefer readers without software-development backgrounds; record only an anonymous participant pseudonym.
- Do not collect names, contact details, employer, exact location, or other identifying information.
- Explain that participation is voluntary and answers may be used only in aggregate documentation evidence.

## Bounded journey

1. Give the reader only the selected language root README and its documentation home.
2. Ask the reader to follow the links through purpose, philosophy, architecture, capabilities, decision states, first calibration, first Work Item, and recovery.
3. Do not explain terms, correct the reader, or point to another language during the task.
4. Record the exact document revision and language before asking the questions.

## Six questions

1. In your own words, what problem does this project solve?
2. What is the project's North Star, and what does it mean in practice?
3. What does AI Cockpit control, and what remains the responsibility of people or external tools?
4. What would make you continue, investigate, or stop?
5. What would you do first to adopt the project and then start the first Work Item?
6. If a required check or evidence is missing, what would you do, and what would you not do?

## Scoring

Score each answer as `correct`, `partially_correct`, `incorrect`, or `no_answer` against the answer key maintained by the reviewer. Record the quote or paraphrase that supports the score. A passing result requires every P0 concept to be represented by the required minimum sample declared in the active study handoff; this protocol alone never supplies that sample.

## Evidence boundary

Raw answers must be stored using [the response schema](comprehension-validation-response.schema.json). A deterministic test, an Agent's own review, a link check, or a page-count comparison is not participant evidence. Until the required raw answers are received and reviewed, the documentation status remains `comprehension_unverified`.
