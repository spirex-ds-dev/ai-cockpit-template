# Post-archive hosted functional recovery design

## Purpose

Permit an archived Work Item to open its existing append-only recovery path
when a GitHub pull-request job completed with an independently verifiable
pytest functional failure.  The existing implementation only accepts an
incidental `blocked_recovery` marker, which rejects the actual hosted failure
from PR #813 even though its log contains concrete failed pytest node IDs and
a failed-test summary.

## Decision

Keep the provider and archive identity requirements unchanged.  Extend only
the functional-failure classifier so it accepts either:

- the existing explicit recovery marker; or
- a canonical pytest failure shape: one or more `FAILED <nodeid>` lines and a
  pytest summary reporting one or more failed tests.

The generated receipt will identify which supported signal was observed.  A
generic nonzero command, a coverage-only shortfall, a success/cancelled run,
or a mismatched repository, PR, SHA, workflow, or log digest remains
ineligible.

## Safety boundary

The correction does not modify archives, quality selection, coverage policy,
release/version metadata, or normal PR acceptance.  The receipt remains
append-only and source-bound to the failed candidate SHA, completed failed
provider job, workflow path, run attempt, and log digest.  It can grant only
the recovery paths explicitly listed by the existing recovery mechanism.

## Verification

Regression tests will first prove that a normal pytest failure is currently
rejected, then prove it creates a valid provider-bound receipt after the
change.  Negative tests preserve rejection for arbitrary failure text and
invalid provider bindings.  Focused tests and the Work Item's required
governance and quality checks provide the completion evidence.
