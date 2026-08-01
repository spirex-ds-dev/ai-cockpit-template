---
author: Ray
title: "Operation-time Policy Reevaluation"
description: "A bounded local decision model for high-risk tool calls."
---

# Operation-time Policy Reevaluation

An input-time review is not an authorization for a later operation. Immediately
before a listed high-risk call, the repository-local model evaluates:

```text
Input Trust + Requested Operation + Actual Tool Call + Target Resource
+ Current Authority + Evidence Freshness + Destructive Impact
= Execution Decision
```

## Interception boundary

`OperationTimeRequest` binds the requested operation, actual call, target,
declared scope, former approval binding, current authority, evidence freshness,
and destructive impact. `evaluate_operation_time_policy` returns `allow`,
`confirm`, or `block`; it never runs a command or grants provider permission.

The model recognizes deletion, test and CI changes, branch-protection changes,
secret writes, push, merge, release, migration, script execution, external API
writes, installation or upgrade, and governance removal. The actual call must
equal the requested operation. A changed target or scope invalidates the former
approval binding; stale evidence or missing authority requires human
confirmation; unclassified impact and request/call mismatch block with an
explicit recovery condition.

For example, creating a script does not authorize its later execution. The
later `execute_script` call is independently evaluated and cannot reuse an
approval for `create_script`.

## Limits

This is deterministic, local policy evidence. It does not authenticate a
person, verify a provider event, configure branch protection, execute a script,
or perform any external write. Callers must retain the decision and apply their
own applicable provider and repository controls.
