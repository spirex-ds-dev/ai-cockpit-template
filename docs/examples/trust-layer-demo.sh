#!/bin/sh
set -eu

# Offline demonstration: no credentials, network, filesystem mutation, or production call.
blocked=0
for scenario in missing-evidence out-of-scope production-operation; do
  printf '{"scenario":"%s","decision":"stop","unsafeOperation":false}\n' "$scenario"
  blocked=$((blocked + 1))
done
printf '{"summary":{"blockedScenarios":%s,"unsafeOperations":0,"evidence":"machine-readable stop records"}}\n' "$blocked"
