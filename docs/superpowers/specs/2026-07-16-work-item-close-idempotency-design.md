# Work Item Close Idempotency Design

## Problem

`ai-close-work-item` currently treats a non-zero exit from `git push <remote> --delete <branch>` as fatal. GitHub can automatically delete a merged pull request's source branch before this explicit cleanup command runs, so the command can fail even though the required remote postcondition—no Work Item branch exists—is already true.

## Decision

Make remote branch deletion idempotent by separating the deletion request from its postcondition verification:

1. Run `git push <remote> --delete <branch>` without immediately raising on a non-zero result.
2. Run `git fetch <remote> --prune` as the authoritative refresh step.
3. Verify with `git ls-remote --exit-code --heads <remote> <branch>`.
4. Accept both a successful delete request and a failed request whose final remote state proves the branch is absent.
5. Continue to fail closed if the branch still exists or the remote state cannot be verified.

The implementation will not match provider-specific error text or rely on a pre-check, because either approach is brittle under concurrent deletion.

## Testing and documentation

The lifecycle closure tests will cover normal deletion, platform-predeleted branches, a still-existing branch after deletion failure, and an unverifiable remote state. The lifecycle reference will document that an already-absent remote branch is an accepted idempotent outcome only after final verification.
