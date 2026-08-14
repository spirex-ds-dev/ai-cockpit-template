---
author: Ray
title: "Injection Boundary"
description: "The bounded repository-level response to hostile or misleading instructions."
audience:
  - security_reviewer
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Injection Boundary

<!-- capability-claim: repository_governance_layer -->

AI Cockpit is not a general prompt-injection detector. It can reject or stop
repository actions when instructions conflict with declared scope, evidence,
authority, protected paths, requested-operation policy, or required human
confirmation.

Untrusted text remains data until a governed operation binds it to reviewable
evidence and authority. A gate passing proves only its declared input and rule;
it does not prove that all hostile intent was detected.

Authentication, hosting, network controls, and dependency scanning remain the responsibility of the target project and external tools. AI Cockpit is not a sandbox, identity provider, or runtime security control.

Concrete adversarial cases and their evidence limits are maintained in
[Real Absurd Injection Cases](../reference/real-absurd-injection-cases.md).
