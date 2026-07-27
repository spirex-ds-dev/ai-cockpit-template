#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
head='c2022fa1d0c2d94ed3edf6c1d16a89260d3fd68f'
valid="$tmp/valid.json"
jq -n --arg head "$head" '{format:"ai-cockpit-ci-release-evidence",schemaVersion:1,state:"verified",evidenceSource:"github_api",workflowRunId:"12345",headSha:$head,mergeCommitSha:("d"*40),headToMergeRelationship:"pull_request_merge_ref",requiredJobNames:["template-smoke"],workflowRuns:[{workflowRunId:"12345",workflowName:"smoke.yml",headSha:$head,requiredJobNames:["template-smoke"],jobs:[{name:"template-smoke",conclusion:"success"}],conclusion:"success",failureReasons:[]}],conclusion:"success",failureReasons:[],artifactDigests:{"sbom.json":("a"*64),"provenance.json":("b"*64)},sbom:{digest:("a"*64),sourceCommit:$head},provenance:{digest:("b"*64),sourceCommit:$head}}' > "$valid"
bash "$root/scripts/check_ci_release_evidence.sh" "$valid" "$head"

for mutation in missing-run stale-head failed-without-reason pr-body; do
  case "$mutation" in
    missing-run) jq '.workflowRunId = ""' "$valid" > "$tmp/$mutation.json" ;;
    stale-head) jq '.headSha = ("e"*40)' "$valid" > "$tmp/$mutation.json" ;;
    failed-without-reason) jq '.state = "failed" | .conclusion = "failure"' "$valid" > "$tmp/$mutation.json" ;;
    pr-body) jq '.evidenceSource = "pr_body"' "$valid" > "$tmp/$mutation.json" ;;
  esac
  if bash "$root/scripts/check_ci_release_evidence.sh" "$tmp/$mutation.json" "$head"; then
    echo "negative evidence case unexpectedly passed: $mutation" >&2
    exit 1
  fi
done
bad_required_jobs="$tmp/bad-required-jobs.json"
jq '.requiredJobNames += ["installation-smoke"]' "$valid" > "$bad_required_jobs"
if bash "$root/scripts/check_ci_release_evidence.sh" "$bad_required_jobs" "$head"; then
  echo 'incomplete required-job evidence unexpectedly passed' >&2
  exit 1
fi
all_three="$tmp/all-three.json"
jq '.state = "candidate" | .requiredJobNames = ["template-smoke","installation-smoke","release-evidence"] | .workflowRuns[0].requiredJobNames = ["template-smoke","installation-smoke","release-evidence"] | .workflowRuns[0].jobs += [{name:"installation-smoke",conclusion:"success"},{name:"release-evidence",conclusion:"success"}] | .state = "candidate" | .conclusion = "success"' "$valid" > "$all_three"
bash "$root/scripts/check_ci_release_evidence.sh" "$all_three" "$head"
upstream_failed="$tmp/upstream-failed.json"
jq '.state = "failed" | .conclusion = "failure" | .failureReasons = ["template-smoke:failure","installation-smoke:skipped","release-evidence:skipped"] | .workflowRuns[0].conclusion = "failure" | .workflowRuns[0].failureReasons = .failureReasons | .workflowRuns[0].jobs[0].conclusion = "failure" | .workflowRuns[0].jobs += [{name:"installation-smoke",conclusion:"skipped"},{name:"release-evidence",conclusion:"skipped"}]' "$valid" > "$upstream_failed"
bash "$root/scripts/check_ci_release_evidence.sh" "$upstream_failed" "$head"
downstream_failed="$tmp/downstream-failed.json"
jq '.state = "failed" | .conclusion = "failure" | .failureReasons = ["installation-smoke:failure"] | .workflowRuns[0].conclusion = "failure" | .workflowRuns[0].failureReasons = .failureReasons | .workflowRuns[0].jobs += [{name:"installation-smoke",conclusion:"failure"},{name:"release-evidence",conclusion:"success"}]' "$valid" > "$downstream_failed"
# Make the downstream-failure fixture require and record all three jobs.
jq '.requiredJobNames = ["template-smoke","installation-smoke","release-evidence"] | .workflowRuns[0].requiredJobNames = .requiredJobNames' "$downstream_failed" > "$tmp/downstream-failed-3.json"
bash "$root/scripts/check_ci_release_evidence.sh" "$tmp/downstream-failed-3.json" "$head"
missing_job="$tmp/missing-job.json"
jq '.state = "failed" | .conclusion = "failure" | .failureReasons = ["installation-smoke:skipped"] | .requiredJobNames = ["template-smoke","installation-smoke"] | .workflowRuns[0].requiredJobNames = .requiredJobNames | .workflowRuns[0].conclusion = "failure" | .workflowRuns[0].failureReasons = .failureReasons' "$valid" > "$missing_job"
if bash "$root/scripts/check_ci_release_evidence.sh" "$missing_job" "$head"; then
  echo 'missing required job evidence unexpectedly passed' >&2
  exit 1
fi
success_with_failure_reason="$tmp/success-with-failure-reason.json"
jq '.state = "candidate" | .failureReasons = ["template-smoke:success"] | .workflowRuns[0].failureReasons = ["template-smoke:success"]' "$valid" > "$success_with_failure_reason"
if bash "$root/scripts/check_ci_release_evidence.sh" "$success_with_failure_reason" "$head"; then
  echo 'successful evidence with a success failure reason unexpectedly passed' >&2
  exit 1
fi
mkdir "$tmp/release"
jq -n '{releaseTag:"v0.5.33"}' > "$tmp/release/release.json"
jq -n '{releaseTag:"v0.5.34",releaseState:"candidate",published:false,basedOnReleaseTag:"v0.5.33"}' > "$tmp/release/next-release.json"
pub_digest="$(sha256sum "$tmp/release/release.json" | cut -d' ' -f1)"
candidate_digest="$(sha256sum "$tmp/release/next-release.json" | cut -d' ' -f1)"
jq -n --arg source "$head" --arg pub "$pub_digest" --arg candidate "$candidate_digest" --slurpfile evidence "$valid" '{schemaVersion:1,canonical:true,projections:{published:"release.json",candidate:"next-release.json"},state:"candidate_verified",releaseTag:"v0.5.34",sourceCommit:$source,previousRelease:"v0.5.33",evidenceStatus:"verified",evidenceBundleDigest:("a"*64),metadataDigests:{published:$pub,candidate:$candidate},ciEvidence:$evidence[0]}' > "$tmp/release/release-state.json"
PYTHONDONTWRITEBYTECODE=1 python3 "$root/scripts/check_release_state_consistency.py" --root "$tmp/release"
jq '.ciEvidence.evidenceSource = "pr_body"' "$tmp/release/release-state.json" > "$tmp/release/bad.json"
mv "$tmp/release/bad.json" "$tmp/release/release-state.json"
if PYTHONDONTWRITEBYTECODE=1 python3 "$root/scripts/check_release_state_consistency.py" --root "$tmp/release"; then
  echo 'PR Body-only canonical evidence unexpectedly passed' >&2
  exit 1
fi
echo 'CI/Release Evidence shell regression passed'
