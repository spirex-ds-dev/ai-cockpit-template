---
author: Ray
title: "Security and Release Verification"
description: "The evidence boundary for security, supply chain, version, and release decisions."
keywords:
  - security
  - release
  - supply-chain
  - verification
---

# Security and Release Verification

Current capability status is authoritative only in the [Capability Truth Matrix](../reference/capability-truth-matrix.md); this page explains verification responsibilities and does not promote a planned or delegated control to implemented status.

<!-- semantic-domain: security-limits -->
<!-- semantic-domain: prompt-injection-limits -->
Security evidence is source-bound: each record identifies the exact tag, source
commit, artifact, and digest it verifies, and any mismatch fails closed. Prompt Injection detection
and input-trust controls reduce known repository risks but do not prove complete
containment, identity, isolation, or safe execution.

<!-- doc-domain: release-metadata -->
<!-- semantic-domain: release-version -->
## Release metadata

`release.json` is the published projection; candidate and historical records are
not interchangeable with it. The exact tag, source commit, installer, archive
asset, and checksums must agree.

The projection is a repository claim, not independent proof that a provider
Release is public. Keep these records separate:

| Record | What it proves | What it does not prove |
| --- | --- | --- |
| `release.json` | The version projected by the repository as published | A provider Release exists, is stable, or has downloadable assets |
| `next-release.json` | The intended next candidate and version | Publication, tag creation, or release readiness |
| Git tag | An immutable source reference exists | A provider Release or its assets were published |
| Provider draft Release | A provider-side draft record exists | Public stable availability |
| Provider stable Release and assets | The provider exposes the release record and named assets | Digest or source correctness without independent verification |
| Release freeze evidence | Candidate facts were frozen for review | Publication or post-publish verification |

### Adopter route

Use only the authoritative public projection or a separately verified private
mirror. Stop unless the stable provider Release, tag-pinned metadata, source,
installer, archive asset, and digests agree. The installer records the same
canonical tag, version, source/tag/metadata commit, and artifact-digest tuple
in its validated lifecycle facts; disagreement fails before any installer
write. Do not select the highest tag as a substitute.

For a selected public tag, `release-digests.json` is a release asset generated
after the source commit is fixed. The Quick Install script fetches that asset
into its disposable tag clone, then validates its tag, source commit, and
artifact digests before it can write to the adopter. A tag-tree copy may be a
historical baseline and is not authority for a later release. If this fetch or
validation fails, do not replace the file or bypass the failure: preserve the
error, verify the public release assets against the exact tag, and publish a
new correction tag if the immutable historical release is wrong.

### Maintainer route

Validate the candidate and freeze evidence first. After provider publication,
perform a separate post-publish check of the stable Release and downloadable
assets before changing the public projection. Candidate, publication, and
post-publish verification are distinct states.

<!-- doc-domain: digest -->
## Digest

Verify SHA-256 bindings for the installer and downloadable archive. A caller
assertion cannot replace published metadata.

<!-- doc-domain: provenance -->
## Provenance

Provenance binds an artifact to its source/build statement. It is distinct from
an SBOM and must be generated or verified by an external build, signing, or
attestation tool. AI Cockpit records and validates that delegated evidence; it
does not independently produce the external assertion.

<!-- doc-domain: sbom -->
## SBOM

An SBOM inventories software components; it does not prove how an artifact was
built, that it is vulnerability-free, or that enterprise compliance exists.

<!-- doc-domain: trust-root -->
## Trust root

For public install, the tagged `release.json`, immutable tag/source identity,
archive asset, and digests form the documented trust chain. Missing evidence is
a stop condition.

<!-- doc-domain: private-mirror -->
## Private mirror

A private mirror must publish and independently protect equivalent metadata,
tag/source identity, assets, and digests. AI Cockpit does not attest the mirror
operator.

<!-- doc-domain: local-source -->
## Local source

Local source installation is an intentional non-public path. Record the source
commit/path boundary in the adopter Work Item and do not describe it as public
release verification.

<!-- doc-domain: enterprise-boundary -->
<!-- semantic-domain: enterprise-compliance-boundary -->
## Enterprise boundary

AI Cockpit can contribute repository-local SDLC evidence. It does not
independently guarantee enterprise compliance, trusted identity, production
isolation, immutable external audit, or provider controls.

The following commands are template-release-maintainer checks. Run them in the
release candidate checkout and require the same commands in hosted CI; they are
not adopter installation steps.

| Check | Evidence validated |
| --- | --- |
| `check-release-distribution` | Published metadata, tag/source, installer, archive, and digest projection |
| `check-sbom` | Machine-readable component inventory and its source binding |
| `check-provenance` | Artifact-to-source/build statement binding |
| `check-secret-scanning` | Repository secret-scanning evidence |
| `check-dependency-vulnerabilities` | Dependency vulnerability evidence available to the release gate |

<!-- command-evidence: hosted_executed -->
```sh
make check-release-distribution
make check-sbom
make check-provenance
make check-secret-scanning
make check-dependency-vulnerabilities
```

All checks must succeed for the exact candidate source. On missing, stale, or
conflicting evidence, stop release preparation, preserve the failure evidence,
and follow [Troubleshooting](../reference/troubleshooting.md); do not relabel the
result as an adopter or local-source verification. See
[Distribution](../reference/distribution.md) for inputs and artifact ownership.

The [comprehensive Japanese capability assessment](../reference/japanese-capability-assessment.md)
remains a separate mandatory pre-release stage. Its digest binds exact file
bytes; any bound edit makes it stale, and only a `final_reassessment` produced
after all correctives can satisfy release preflight. This page neither
publishes a version nor marks that assessment complete.
