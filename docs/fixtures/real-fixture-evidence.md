---
author: Ray
title: "Real Fixture Repository Evidence"
description: Evidence boundary and lifecycle results for stack fixture experiments.
keywords:
  - fixtures
  - evidence
  - ai-cockpit
---

# Real Fixture Repository Evidence

The TypeScript Web fixture now executes local npm install/build/test/lint/format and lifecycle commands. Its evidence is limited to the checked-out fixture and local toolchain. Provider assets, trusted identity, sandbox isolation, immutable audit, and enterprise compliance remain `not_run`, not inferred from the local result.

The dependency-free `scripts/fixture_harness.py` exercises the adoption lifecycle for Python and fixture manifests. The Java multi-module fixture additionally runs real `javac`/`java` commands across its `core` and `app` modules; its lifecycle records Install → Configure → Normal Work Item → Ambiguous Request → Critical Domain Change → Upgrade → Rollback → Release Check.

Fixture reports may use the same lifecycle vocabulary as `make ai-lifecycle-facts`; local execution evidence is separate from provider assets and enterprise assurance, which remain `not_run`/`not_claimed`.

The ambiguous and critical-domain phases are expected `blocked` outcomes with a resume condition and policy reference. The harness output is a reviewable evidence bundle, but it is not proof of platform isolation, identity, authentication, immutable audit, enterprise compliance, or production safety.

Python is locally executable through the repository's Python runtime. TypeScript Web is locally executable through npm. Java's Maven path is `not_run` when Maven is unavailable, while its dependency-free Java compiler/runtime path remains independently observable. Flutter remains a documented future boundary for this experiment. Performance and multi-agent conflict measurements are explicitly `not_run` or `not_applicable`, never inferred.

## End-to-end adoption validation

Run the complete local matrix with:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 scripts/end_to_end_adoption_validation.py --output target/end-to-end-adoption-validation.json
```

The matrix creates disposable, committed Git repositories for a Python service, TypeScript web application, Java backend, Android application, iOS Swift Package, Flutter application, and mixed monorepo. Each repository receives a real local AI Cockpit installation and executes calibration, adoption Work Item creation, a restored safe edit, scope and test-weakening probes, governance finish/archive, aggregate PR validation, local bare-remote merge/branch cleanup, upgrade, and deliberately failed-upgrade rollback.

The adversarial probes cover test deletion, added skip, lowered coverage, deletion of a referenced function, external Markdown instructions, forged approval, and fabricated test success. A blocked policy result means automatic execution cannot continue; it does not prove malicious intent. The installation-failure matrix separately checks dirty worktrees, malformed markers, Makefile conflicts, detached-HEAD restoration, unavailable remotes, and invalid release metadata.

Evidence kinds are intentionally distinct:

- `local_real_execution` means the operation ran against a disposable local repository.
- `policy_probe` means a canonical deterministic policy evaluated the case without executing the requested harmful operation.
- `local_provider_simulation` means a local bare Git remote exercised merge-base, push, merge, and branch cleanup semantics. It is not GitHub or provider evidence.
- Hosted provider checks, provider identity, device/signing behavior, and enterprise assurance remain `not_run` or `not_claimed`.

The fixture finish step uses `SKIP_QUALITY=true` because the matrix does not download seven external toolchains. Project-specific compilation, device execution, signing, and hosted CI remain separate delegated evidence; a skipped project-quality route is never reported as a pass.
