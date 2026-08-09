AI_CONTRACT ?= $(shell ls .ai/work-items/active/*.contract.json 2>/dev/null | head -n 1)
AI_SUMMARY ?= $(shell ls .ai/work-items/active/*.summary.json 2>/dev/null | head -n 1)
CONTRACT ?= $(AI_CONTRACT)
SUMMARY ?= $(AI_SUMMARY)
SUMMARY_ARGS ?= $(if $(CONTRACT),--contract $(CONTRACT))
STATUS_ARGS ?= $(if $(SUMMARY),--summary $(SUMMARY))
ARGS ?=
TASK ?=
TITLE ?=
MODE ?= investigate
SKIP_QUALITY ?= false
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
AI_PYTHON = PYTHONDONTWRITEBYTECODE=1 $(PYTHON)
override AI_COCKPIT_MAKE_ENTRYPOINT := $(firstword $(MAKEFILE_LIST))
export AI_COCKPIT_MAKE_ENTRYPOINT
export RELEASE_PREFLIGHT_SOURCE_COMMIT
AI_NESTED_MAKE = "$(MAKE)" -f "$(AI_COCKPIT_MAKE_ENTRYPOINT)"
# Resolve a configured executable name before recipes change directory.  Using
# abspath on a bare name would incorrectly turn `python3` into a path under the
# temporary lockfile directory.
PYTHON_EXECUTABLE = $(if $(findstring /,$(PYTHON)),$(abspath $(PYTHON)),$(shell command -v "$(PYTHON)" 2>/dev/null))
AI_PREFLIGHT_VALIDATE_CONTRACT ?= true
QUALITY_SESSION_ID ?= legacy
QUALITY_RUN_ID ?= $(if $(GITHUB_RUN_ID),$(GITHUB_RUN_ID),local)
QUALITY_TIMING_DIR ?= target/quality/timing
QUALITY_LOG_DIR ?= target/quality/logs
QUALITY_JUNIT_DIR ?= target/quality/junit
QUALITY_SUMMARY_DIR ?= target/quality
QUALITY_PROFILE ?= unknown
QUALITY_ESCALATIONS ?=
QUALITY_ESCALATION_REASONS ?=
GOVERNANCE_PROFILE ?=
GOVERNANCE_RECEIPT ?= target/quality/governance-profile.json
QUALITY_SESSION_LOCK ?= target/quality/session.lock
QUALITY_SESSION_LOCK_HELD ?= false

.PHONY: help \
	test check-quality-toolchain project-format-check project-test project-lint diff-check quality quality-gates \
	ai-cockpit-project-format-check ai-cockpit-project-test ai-cockpit-project-lint ai-cockpit-diff-check ai-cockpit-quality \
check-docs-metadata check-capability-claims check-trust-layer-docs check-real-absurd-injection-docs check-governance-complexity \
	check-ai-system-invariants check-ai-project-profile check-ai-calibration-profile check-ai-guard-calibration cockpit-doctor cockpit-calibrate cockpit-calibration-inventory cockpit-validate-calibration \
	check-bandit-evidence check-bandit-baseline refresh-bandit-baseline check-sbom check-provenance check-release-evidence refresh-candidate-release-evidence check-secret-scanning \
	check-release-distribution check-release-state-consistency check-japanese-capability check-release-readiness check-release-preflight check-ci-release-evidence \
	check-source-bound-evidence check-changed-critical-coverage check-dependabot-intake \
	check-lockfile-reproducibility \
	check-quality-architecture \
	check-deprecated-assets \
	check-instruction-traceability \
	check-trust-schemas check-trust-guards check-critical-domain-guards check-decision-protocol check-baseline-evidence \
	ai-start ai-resume-work-item ai-synchronize-work-item ai-transition-conflict-successor ai-finish ai-open-post-archive-recovery ai-onboard check-ai check-ai-contract check-ai-work-item check-ai-scope check-ai-guards \
	ai-verify-focused ai-verify-full \
	ai-doctor check-ai-adoption-ready \
	check-ai-agent-risk ai-checkpoint check-ai-backtrack check-ai-coverage-guard check-ai-reference-impact check-ai-test-weakening check-ai-test-weakening-fast check-ai-guidelines check-ai-review-policy template-adoption-ready \
	check-ai-scenario-coverage check-ai-start-receipt check-ai-archive-recovery generate-ai-preflight-review check-ai-preflight-review ai-preflight ai-prepare-implementation ai-revalidate-contract-amendment \
	check-ai-lifecycle-truth \
	ai-prepare-hosted-verification-snapshot \
	check-ai-change-summary generate-cockpit-status generate-cockpit-status-ja check-ai-status check-ai-status-ja check-ai-status-consistency repair-ai-status archive-work-item ai-close-work-item check-ai-pr check-ai-pr-core check-ai-diff-ownership ai-pre-merge \
	ai-assess-provider-merge-state-recovery \
	quality-fast quality-standard quality-full quality-release quality-fast-static quality-fast-policy quality-fast-static-gates quality-fast-policy-gates quality-heavy quality-tests-group quality-evidence-group quality-supply-chain-group quality-project-consistency-group quality-installation quality-release-evidence \
	quality-fast-owned quality-standard-owned quality-full-owned quality-release-owned project-test-owned \
	check-ai-serial-order check-ai-budget-impact ai-lifecycle-facts ai-cockpit-version ai-cockpit-update-check \
	check-ai-task-outcome generate-human-benefit-report check-human-benefit-report \
	ai-cockpit-update-propose ai-cockpit-update-apply ai-cockpit-rollback-propose ai-cockpit-disable ai-cockpit-enable \
	ai-cockpit-uninstall-facts ai-cockpit-uninstall-propose ai-cockpit-uninstall-execute
	ai-work-item-status ai-work-item-intelligence-rebuild

check-ai-diff-ownership:
	$(AI_PYTHON) scripts/ai_check_diff_ownership.py $(if $(AI_BASE_COMMIT),--base $(AI_BASE_COMMIT),) $(if $(CONTRACT),--contract $(CONTRACT),)

check-ai-start-receipt:
	$(AI_PYTHON) scripts/ai_start_receipt.py --contract "$(CONTRACT)" $(if $(RECEIPT),--receipt "$(RECEIPT)",)

check-ai-archive-recovery:
	$(AI_PYTHON) scripts/ai_check_archive_recovery.py $(ARGS)

ai-pre-merge:
	@set -e; \
		echo 'Content quality:'; env -u AI_BASE_COMMIT -u AI_COCKPIT_EXECUTION_MODE -u MAKEFLAGS -u MAKEOVERRIDES $(AI_NESTED_MAKE) quality || { echo 'ALLOW COMMIT / MERGE: no (content quality failed)'; exit 1; }; \
		echo 'Lifecycle evidence:'; env -u AI_BASE_COMMIT -u AI_COCKPIT_EXECUTION_MODE -u MAKEFLAGS -u MAKEOVERRIDES $(AI_NESTED_MAKE) check-ai-status-consistency || { echo 'ALLOW COMMIT / MERGE: no (lifecycle evidence failed)'; exit 1; }; \
		echo 'Diff ownership preview:'; $(AI_NESTED_MAKE) check-ai-diff-ownership AI_BASE_COMMIT="$(AI_BASE_COMMIT)" || { echo 'ALLOW COMMIT / MERGE: no (diff ownership failed)'; exit 1; }; \
		echo 'PR ownership:'; $(AI_NESTED_MAKE) check-ai-pr AI_BASE_COMMIT="$(AI_BASE_COMMIT)" || { echo 'ALLOW COMMIT / MERGE: no (PR ownership failed)'; exit 1; }; \
		echo 'ALLOW COMMIT / MERGE: yes'

help:
	@printf '%s\n' 'AI Cockpit template commands:'
	@printf '%s\n' '  make ai-start TASK=<task> TITLE="..." MODE=code'
	@printf '%s\n' '  make ai-resume-work-item CONTRACT=<contract.json> BASE_REMOTE=<remote> BASE_BRANCH=<default-branch>'
	@printf '%s\n' '  make ai-synchronize-work-item CONTRACT=<contract.json> BASE_REMOTE=<remote> BASE_BRANCH=<default-branch>  # synchronize an eligible active Work Item; dirty state requires Contract synchronizationCheckpoint authorization'
	@printf '%s\n' '  make check-ai-archive-recovery ARGS="--target origin/main"  # run before rebasing archived evidence'
	@printf '%s\n' '  make ai-onboard [PHASE=1|2|3]'
	@printf '%s\n' '  make ai-doctor'
	@printf '%s\n' '  make check-ai-adoption-ready'
	@printf '%s\n' '  make template-adoption-ready  # explicit template-maintenance readiness mode'
	@printf '%s\n' '  make check-ai-contract CONTRACT=<contract.json>'
	@printf '%s\n' '  make check-ai-serial-order CONTRACT=<contract.json>'
	@printf '%s\n' '  make check-ai-budget-impact CONTRACT=<contract.json>'
	@printf '%s\n' '  make check-ai-scope CONTRACT=<contract.json>'
	@printf '%s\n' '  make check-ai-guards'
	@printf '%s\n' '  make check-ai-agent-risk CONTRACT=<contract.json> SUMMARY=<summary.json>'
	@printf '%s\n' '  make ai-checkpoint CONTRACT=<contract.json> SUMMARY=<summary.json> STAGE=before_finish'
	@printf '%s\n' '  make check-ai-review-policy SUMMARY=<summary.json>'
	@printf '%s\n' '  make check-ai-backtrack'
	@printf '%s\n' '  make check-ai-coverage-guard'
	@printf '%s\n' '  make check-ai-scenario-coverage'
	@printf '%s\n' '  make ai-preflight'
	@printf '%s\n' '  make ai-verify-focused CONTRACT=<contract.json> SUMMARY=<summary.json>'
	@printf '%s\n' '  make ai-verify-full CONTRACT=<contract.json> SUMMARY=<summary.json> [STAGE=pr|release]'
	@printf '%s\n' '  make ai-prepare-hosted-verification-snapshot CONTRACT=<contract.json>  # validate a push-only measurement snapshot'
	@printf '%s\n' '  make generate-ai-preflight-review'
	@printf '%s\n' '  make check-ai-preflight-review'
	@printf '%s\n' '  make check-ai-change-summary SUMMARY=<summary.json> CONTRACT=<contract.json>'
	@printf '%s\n' '  make generate-cockpit-status CONTRACT=<contract.json> SUMMARY=<summary.json>'
	@printf '%s\n' '  make check-ai-status CONTRACT=<contract.json> SUMMARY=<summary.json>'
	@printf '%s\n' '  make check-ai-status-consistency'
	@printf '%s\n' '  make repair-ai-status'
	@printf '%s\n' '  make ai-finish TASK=<task>'
	@printf '%s\n' '  make check-ai'
	@printf '%s\n' '  make quality'
	@printf '%s\n' '  make test'
	@printf '%s\n' '  make check-docs-metadata'
	@printf '%s\n' '  make check-governance-complexity'
	@printf '%s\n' '  make check-instruction-traceability'
	@printf '%s\n' '  make check-ai-system-invariants'
	@printf '%s\n' '  make cockpit-doctor'
	@printf '%s\n' '  make cockpit-calibrate'
	@printf '%s\n' '  make cockpit-validate-calibration'
	@printf '%s\n' '  make check-ai-calibration-profile [ARGS="--previous-level standard"]'
	@printf '%s\n' '  make check-release-distribution  # networked public release contract'
	@printf '%s\n' '  make check-trust-schemas'
	@printf '%s\n' '  make check-trust-guards'
	@printf '%s\n' '  make check-decision-protocol'
	@printf '%s\n' '  make archive-work-item CONTRACT=<contract.json> [ARGS="--dry-run"]'
	@printf '%s\n' '  make ai-close-work-item TASK=<task>  # verify merge, synchronize base, and clean branches'
	@printf '%s\n' '  make ai-assess-provider-merge-state-recovery ARGS="--evidence <json> --human-confirmed"  # assess an exceptional provider inconsistency; never cleans branches'
	@printf '%s\n' ''
	@printf '%s\n' 'Customize project-format-check, project-test, and project-lint for your stack.'

check-quality-toolchain:
	$(AI_PYTHON) scripts/check_dev_tool_versions.py --manifest requirements-dev.in --tool ruff

project-format-check: check-quality-toolchain
	$(AI_PYTHON) -m ruff format --check scripts tests
	git diff --check

check-quality-architecture:
	$(AI_PYTHON) scripts/ai_quality_architecture.py

check-deprecated-assets:
	$(AI_PYTHON) scripts/check_deprecated_assets.py

check-instruction-traceability:
	$(AI_PYTHON) scripts/check_instruction_traceability.py

project-test:
	$(call RUN_QUALITY_SESSION,project-test)

project-test-owned:
	mkdir -p "$(QUALITY_JUNIT_DIR)"
	$(AI_PYTHON) -m pytest -q --cov=scripts --cov-report=term-missing --cov-report=json:target/coverage.json --cov-fail-under=85.10 --junitxml="$(QUALITY_JUNIT_DIR)/project-test.xml" --durations=25 --durations-min=1
	bash tests/test_installer_boundaries.sh
	$(AI_PYTHON) scripts/check_critical_coverage.py
	bash tests/test_ci_release_evidence.sh

# Compatibility jobs validate the interpreter/platform matrix without repeating
# the release-blocking full quality graph owned by template-smoke.
compatibility-test:
	$(AI_PYTHON) -m pytest -q --no-cov \
		tests/test_input_trust.py \
		tests/test_input_trust_corpus.py \
		tests/test_workflows.py \
		tests/test_ci_quality_orchestration.py

test: project-test unsupported-claim-regression adopter-long-cycle delusion-test-gate

adopter-long-cycle:
	$(AI_PYTHON) scripts/external_adopter_long_cycle.py

unsupported-claim-regression:
	$(AI_PYTHON) scripts/unsupported_claim_gate.py

delusion-test-gate:
	$(AI_PYTHON) -m pytest -q tests/test_delusion_scenarios.py tests/test_unsupported_claim_regression.py

project-lint: check-quality-toolchain
	$(AI_PYTHON) -m ruff check scripts tests
	$(AI_PYTHON) -m mypy scripts/*.py
	$(AI_PYTHON) scripts/check_governance_complexity.py
	$(AI_PYTHON) -m py_compile scripts/*.py tests/*.py

diff-check:
	git diff --check

check-docs-metadata:
	$(AI_PYTHON) scripts/check_docs_metadata.py
	$(AI_PYTHON) scripts/ai_check_capability_claims.py

ai-documentation-read-set:
	$(AI_PYTHON) scripts/ai_documentation_authority.py $(if $(INCLUDE_REFERENCE),--include-reference,)

check-capability-claims:
	$(AI_PYTHON) scripts/ai_check_capability_claims.py

check-trust-layer-docs:
	$(AI_PYTHON) scripts/check_trust_layer_docs.py

check-real-absurd-injection-docs:
	$(AI_PYTHON) scripts/check_real_absurd_injection_docs.py

check-governance-complexity:
	$(AI_PYTHON) scripts/check_governance_complexity.py

check-release-distribution:
	$(AI_PYTHON) scripts/check_release_distribution.py

check-release-distribution-post-publish:
	AI_RELEASE_POST_PUBLISH=1 $(AI_PYTHON) scripts/check_release_distribution.py

check-release-state-consistency:
	$(AI_PYTHON) scripts/check_release_state_consistency.py --root .

check-japanese-capability:
	$(AI_PYTHON) scripts/ai_japanese_capability.py --check

check-source-bound-evidence:
	$(AI_PYTHON) scripts/ai_capability_truth.py
	$(AI_PYTHON) scripts/ai_japanese_capability.py --check --require-final-reassessment
	$(AI_PYTHON) scripts/check_pre_release_documentation_alignment.py

check-changed-critical-coverage:
	$(AI_PYTHON) scripts/check_changed_critical_coverage.py --base "$(AI_BASE_COMMIT)" $(if $(CONTRACT),--contract "$(CONTRACT)")

check-dependabot-intake:
	$(AI_PYTHON) scripts/ai_check_dependabot_intake.py --event-name "$(GITHUB_EVENT_NAME)" --author "$(AI_PR_AUTHOR)" --pull-request-url "$(AI_PR_URL)" --head "$(AI_PR_HEAD_SHA)"

check-release-preflight:
	$(AI_NESTED_MAKE) check-source-bound-evidence
	$(AI_PYTHON) scripts/check_release_preflight.py --root .

check-release-readiness:
	$(AI_NESTED_MAKE) check-source-bound-evidence
	$(AI_PYTHON) scripts/check_release_preflight.py --root . --mode repository-readiness

finalize-release-freeze:
	$(AI_PYTHON) scripts/finalize_release_freeze.py \
		$(if $(SOURCE_COMMIT),--source-commit "$(SOURCE_COMMIT)",) \
		$(if $(TAG_TARGET),--tag-target "$(TAG_TARGET)",) \
		$(if $(METADATA_COMMIT),--metadata-commit "$(METADATA_COMMIT)",)

finalize-release-freeze-candidate:
	test -n "$(CANDIDATE_TASK)"
	$(AI_PYTHON) scripts/finalize_release_freeze.py --candidate-task "$(CANDIDATE_TASK)" \
		$(if $(SOURCE_COMMIT),--source-commit "$(SOURCE_COMMIT)",) \
		$(if $(TAG_TARGET),--tag-target "$(TAG_TARGET)",) \
		$(if $(METADATA_COMMIT),--metadata-commit "$(METADATA_COMMIT)",)

finalize-release-freeze-runtime:
	test -n "$(RUNTIME_SOURCE_COMMIT)"
	test -n "$(RUNTIME_DEFAULT_BRANCH)"
	$(AI_PYTHON) scripts/finalize_release_freeze.py --runtime-source-commit "$(RUNTIME_SOURCE_COMMIT)" \
		--runtime-default-branch "$(RUNTIME_DEFAULT_BRANCH)"

finalize-release-freeze-premerge:
	test -n "$(TASK)"
	$(AI_PYTHON) scripts/finalize_release_freeze.py --premerge-task "$(TASK)" \
		$(if $(SOURCE_COMMIT),--source-commit "$(SOURCE_COMMIT)",) \
		$(if $(TAG_TARGET),--tag-target "$(TAG_TARGET)",) \
		$(if $(METADATA_COMMIT),--metadata-commit "$(METADATA_COMMIT)",)

check-ci-release-evidence:
	test -n "$(CI_RELEASE_EVIDENCE)"
	bash scripts/check_ci_release_evidence.sh "$(CI_RELEASE_EVIDENCE)" "$(CI_EXPECTED_HEAD_SHA)"

check-trust-schemas:
	$(AI_PYTHON) scripts/ai_trust_schema.py --check

check-trust-guards:
	$(AI_PYTHON) -m pytest -q tests/test_trust_guards.py

check-critical-domain-guards:
	$(AI_PYTHON) -m pytest -q tests/test_critical_domain_guards.py

check-baseline-evidence:
	$(AI_PYTHON) -m pytest -q tests/test_baseline_evidence.py

check-decision-protocol:
	$(AI_PYTHON) -m pytest -q tests/test_decision_protocol.py

check-ai-system-invariants:
	$(AI_PYTHON) scripts/check_system_invariants.py

check-bandit-evidence:
	mkdir -p target/quality
	@status=0; $(AI_PYTHON) -m bandit -q -r scripts -f json -o target/quality/bandit.json || status=$$?; test "$$status" -eq 0 -o "$$status" -eq 1

check-bandit-baseline: check-bandit-evidence
	$(AI_PYTHON) scripts/check_bandit_baseline.py --input target/quality/bandit.json

refresh-bandit-baseline: check-bandit-evidence
	$(AI_PYTHON) scripts/check_bandit_baseline.py --input target/quality/bandit.json --refresh

check-sbom:
	$(AI_PYTHON) scripts/check_supply_chain.py sbom

check-provenance:
	$(AI_PYTHON) scripts/check_supply_chain.py provenance

check-release-evidence:
	$(AI_PYTHON) scripts/check_supply_chain.py release

refresh-candidate-release-evidence:
	$(AI_PYTHON) scripts/check_supply_chain.py refresh $(if $(SOURCE_COMMIT),--source-commit "$(SOURCE_COMMIT)",)

check-lockfile-reproducibility:
	@set -e; test -n "$(PYTHON_EXECUTABLE)" && test -x "$(PYTHON_EXECUTABLE)" || { echo "lockfile reproducibility check failed: PYTHON=$(PYTHON) did not resolve to an executable" >&2; exit 1; }; tmp=$$(mktemp -d); normalized=$$(mktemp -d); trap 'rm -rf "$$tmp" "$$normalized"' EXIT; cp requirements-dev.lock "$$tmp/"; (cd "$$tmp" && ln -s "$(CURDIR)/requirements-dev.in" requirements-dev.in && "$(PYTHON_EXECUTABLE)" -m piptools compile --no-upgrade --generate-hashes --allow-unsafe --output-file=requirements-dev.lock requirements-dev.in >/dev/null && sed -i.bak -E 's/^# This file is autogenerated by pip-compile with Python .*/# This file is autogenerated by pip-compile with canonical Python 3.11/' requirements-dev.lock && rm requirements-dev.lock.bak); awk '/^    # via/ { print "    # via"; skip=1; next } skip && /^    #   / { next } { skip=0; print }' requirements-dev.lock > "$$normalized/committed.lock"; awk '/^    # via/ { print "    # via"; skip=1; next } skip && /^    #   / { next } { skip=0; print }' "$$tmp/requirements-dev.lock" > "$$normalized/generated.lock"; cmp -s "$$normalized/generated.lock" "$$normalized/committed.lock" || { echo 'lockfile reproducibility check failed: regenerated requirements-dev.lock differs from the committed lockfile' >&2; exit 1; }

check-secret-scanning:
	$(AI_PYTHON) scripts/check_supply_chain.py secrets

check-dependency-vulnerabilities:
	$(AI_PYTHON) scripts/check_supply_chain.py vulnerabilities

cockpit-doctor:
	$(AI_PYTHON) scripts/ai_doctor.py --root .
	$(AI_PYTHON) scripts/ai_project_doctor.py --root .

cockpit-calibrate:
	$(AI_PYTHON) scripts/ai_calibrate.py generate --root .

cockpit-calibration-wizard:
	$(AI_PYTHON) scripts/ai_calibration_wizard.py --root . $(ARGS)

cockpit-calibration-inventory:
	$(AI_PYTHON) scripts/ai_calibration_inventory.py --root . $(ARGS)

cockpit-validate-calibration:
	$(AI_PYTHON) scripts/ai_calibrate.py validate --profile "$(or $(PROFILE),.ai/project_profile.proposed.yaml)" $(ARGS)

check-ai-project-profile:
	$(AI_PYTHON) scripts/ai_calibrate.py validate --profile .ai/project_profile.yaml --confirmed

check-ai-calibration-profile:
	$(AI_PYTHON) scripts/ai_calibration_profiles.py --profile "$(or $(PROFILE),.ai/project_profile.yaml)" $(ARGS)

check-ai-guard-calibration: check-ai-project-profile
	$(AI_PYTHON) scripts/ai_check_guard_calibration.py --root .

QUALITY_FAST_STATIC_GATES := project-format-check project-lint diff-check
QUALITY_FAST_POLICY_GATES := check-trust-schemas check-docs-metadata check-ai-system-invariants check-ai-project-profile check-ai-guard-calibration check-ai-status-consistency check-ai-test-weakening-fast
QUALITY_TEST_GATES := project-test
QUALITY_EVIDENCE_GATES := unsupported-claim-regression adopter-long-cycle check-release-evidence check-release-state-consistency check-dependency-vulnerabilities
QUALITY_SUPPLY_CHAIN_GATES := check-bandit-baseline check-sbom check-provenance check-secret-scanning
QUALITY_PROJECT_CONSISTENCY_GATES := check-quality-architecture check-deprecated-assets check-instruction-traceability
QUALITY_MAKE = $(AI_NESTED_MAKE)

define RUN_QUALITY_GATE
	$(AI_PYTHON) scripts/run_quality_gate.py --gate $(1) --category $(2) --session-id "$(QUALITY_SESSION_ID)" --run-id "$(QUALITY_RUN_ID)" --output "$(QUALITY_TIMING_DIR)/$(1).json" --log "$(QUALITY_LOG_DIR)/$(1).log" -- $(QUALITY_MAKE) --no-print-directory $(1)
endef

# A worktree-local kernel lock protects shared coverage and report writers.
# Nested quality targets inherit the owner marker instead of acquiring again.
define RUN_QUALITY_SESSION
	@if test "$(QUALITY_SESSION_LOCK_HELD)" = true; then \
		$(QUALITY_MAKE) --no-print-directory $(1)-owned; \
	else \
		$(AI_PYTHON) scripts/quality_session_lock.py --lock "$(QUALITY_SESSION_LOCK)" --worktree "$(CURDIR)" -- $(QUALITY_MAKE) --no-print-directory QUALITY_SESSION_LOCK_HELD=true $(1)-owned; \
	fi
endef

# Fast is intentionally narrower than Full.  It never implies release readiness.
quality-fast:
	$(call RUN_QUALITY_SESSION,quality-fast)

quality-fast-owned:
	$(QUALITY_MAKE) --no-print-directory quality-fast-static
	$(QUALITY_MAKE) --no-print-directory quality-fast-policy

quality-fast-static:
	$(QUALITY_MAKE) --no-print-directory -j2 quality-fast-static-gates

quality-fast-static-gates: qg-project-format-check qg-project-lint qg-diff-check

qg-project-format-check:
	$(call RUN_QUALITY_GATE,project-format-check,static)
qg-project-lint:
	$(call RUN_QUALITY_GATE,project-lint,static)
qg-diff-check:
	$(call RUN_QUALITY_GATE,diff-check,static)

quality-fast-policy:
	$(QUALITY_MAKE) --no-print-directory -j2 quality-fast-policy-gates

quality-fast-policy-gates: qg-check-trust-schemas qg-check-docs-metadata qg-check-ai-system-invariants qg-check-ai-project-profile qg-check-ai-guard-calibration qg-check-ai-status-consistency $(if $(filter true,$(TEST_WEAKENING_FULL_OWNERSHIP)),,qg-check-ai-test-weakening-fast)

qg-check-trust-schemas:
	$(call RUN_QUALITY_GATE,check-trust-schemas,policy)
qg-check-docs-metadata:
	$(call RUN_QUALITY_GATE,check-docs-metadata,policy)
qg-check-ai-system-invariants:
	$(call RUN_QUALITY_GATE,check-ai-system-invariants,policy)
qg-check-ai-project-profile:
	$(call RUN_QUALITY_GATE,check-ai-project-profile,policy)
qg-check-ai-guard-calibration:
	$(call RUN_QUALITY_GATE,check-ai-guard-calibration,policy)
qg-check-ai-status-consistency:
	$(call RUN_QUALITY_GATE,check-ai-status-consistency,policy)
qg-check-ai-test-weakening-fast:
	$(call RUN_QUALITY_GATE,check-ai-test-weakening-fast,policy)

# Standard reuses existing gate owners and replaces the Fast weakening sample
# with the full diff analysis. It intentionally excludes Full/Release groups.
quality-standard:
	$(call RUN_QUALITY_SESSION,quality-standard)

quality-standard-owned:
	$(QUALITY_MAKE) --no-print-directory quality-fast TEST_WEAKENING_FULL_OWNERSHIP=true
	$(QUALITY_MAKE) --no-print-directory project-test
	$(QUALITY_MAKE) --no-print-directory check-ai-reference-impact
	$(QUALITY_MAKE) --no-print-directory check-ai-test-weakening

# Heavy groups are separate ownership units.  Their outputs are either read-only
# or isolated by the gate itself; no blanket high-parallelism quality target is used.
quality-heavy:
	$(QUALITY_MAKE) --no-print-directory -j2 quality-tests-group quality-evidence-group quality-supply-chain-group quality-project-consistency-group

quality-tests-group:
quality-tests-group: qg-project-test

qg-project-test:
	$(call RUN_QUALITY_GATE,project-test,tests)

quality-evidence-group:
quality-evidence-group: qg-unsupported-claim-regression qg-adopter-long-cycle qg-check-release-evidence qg-check-release-state-consistency qg-check-dependency-vulnerabilities

qg-unsupported-claim-regression:
	$(call RUN_QUALITY_GATE,unsupported-claim-regression,evidence)
qg-adopter-long-cycle:
	$(call RUN_QUALITY_GATE,adopter-long-cycle,evidence)
qg-check-release-evidence:
	$(call RUN_QUALITY_GATE,check-release-evidence,evidence)
qg-check-release-state-consistency:
	$(call RUN_QUALITY_GATE,check-release-state-consistency,evidence)
qg-check-dependency-vulnerabilities:
	$(call RUN_QUALITY_GATE,check-dependency-vulnerabilities,evidence)

quality-supply-chain-group:
quality-supply-chain-group: qg-check-bandit-baseline qg-check-sbom qg-check-provenance qg-check-secret-scanning

qg-check-bandit-baseline:
	$(call RUN_QUALITY_GATE,check-bandit-baseline,supply-chain)
qg-check-sbom:
	$(call RUN_QUALITY_GATE,check-sbom,supply-chain)
qg-check-provenance:
	$(call RUN_QUALITY_GATE,check-provenance,supply-chain)
qg-check-secret-scanning:
	$(call RUN_QUALITY_GATE,check-secret-scanning,supply-chain)

quality-project-consistency-group:
quality-project-consistency-group: qg-check-quality-architecture qg-check-deprecated-assets qg-check-instruction-traceability qg-check-ai-test-weakening

qg-check-quality-architecture:
	$(call RUN_QUALITY_GATE,check-quality-architecture,project-consistency)
qg-check-deprecated-assets:
	$(call RUN_QUALITY_GATE,check-deprecated-assets,project-consistency)
qg-check-instruction-traceability:
	$(call RUN_QUALITY_GATE,check-instruction-traceability,project-consistency)
qg-check-ai-test-weakening:
	$(call RUN_QUALITY_GATE,check-ai-test-weakening,project-consistency)

quality-full:
	$(call RUN_QUALITY_SESSION,quality-full)

quality-full-owned:
	@set -eu; \
		commit=$$(git rev-parse --short=12 HEAD 2>/dev/null || printf unknown); \
		run_id="$${GITHUB_RUN_ID:-local}"; \
		attempt="$${GITHUB_RUN_ATTEMPT:-0}"; \
		nonce="$${GITHUB_RUN_ID:-local}-$$(date -u +%Y%m%dT%H%M%SZ)-$$$$"; \
		session_id="$$commit-$$nonce-$$attempt"; \
		session_root="target/quality/sessions/$$session_id"; \
		timing="$$session_root/timing"; logs="$$session_root/logs"; junit="$$session_root/junit"; \
		mkdir -p "$$timing" "$$logs" "$$junit"; \
		trap 'printf "%s\n" "$$session_id" > target/quality/current-session.txt' EXIT; \
		printf '%s\n' "$$session_id" > target/quality/current-session.txt; \
		$(AI_PYTHON) scripts/run_quality_session.py --phase quality-fast --phase quality-heavy -- $(QUALITY_MAKE) --no-print-directory QUALITY_SESSION_ID="$$session_id" QUALITY_RUN_ID="$$run_id" QUALITY_TIMING_DIR="$$timing" QUALITY_LOG_DIR="$$logs" QUALITY_JUNIT_DIR="$$junit" TEST_WEAKENING_FULL_OWNERSHIP=true; \
		$(AI_PYTHON) scripts/summarize_quality_gates.py --input "$$timing" --json-output "$$session_root/summary.json" --markdown-output "$$session_root/summary.md" --profile "$(QUALITY_PROFILE)" $(QUALITY_ESCALATIONS) $(QUALITY_ESCALATION_REASONS); \
		cp "$$session_root/summary.json" target/quality/summary.json; \
		cp "$$session_root/summary.md" target/quality/summary.md

# Backward-compatible aliases.  These names are compatibility/debug views of
# the new ownership graph; none invokes the removed duplicate gate graph.
quality:
	$(QUALITY_MAKE) --no-print-directory quality-full

# Historical aggregate alias; it is intentionally routed to the new Full graph.
quality-gates: quality-full
quality-static: quality-fast-static
quality-tests: quality-tests-group
quality-evidence: quality-evidence-group

quality-installation:
	@echo 'Installation gates are owned by the installation-smoke workflow in this phase.'

quality-release-evidence:
	$(QUALITY_MAKE) --no-print-directory check-release-distribution check-release-state-consistency check-release-preflight check-ci-release-evidence

quality-release:
	$(call RUN_QUALITY_SESSION,quality-release)

quality-release-owned:
	$(QUALITY_MAKE) --no-print-directory quality-full
	$(QUALITY_MAKE) --no-print-directory quality-installation
	$(QUALITY_MAKE) --no-print-directory quality-release-evidence

ai-cockpit-project-format-check: project-format-check

ai-cockpit-project-test: project-test

ai-cockpit-project-lint: project-lint

ai-cockpit-diff-check: diff-check

ai-verify:
	$(AI_PYTHON) scripts/ai_verify.py --root . --contract "$(CONTRACT)" --summary "$(SUMMARY)" --stage "$(or $(STAGE),task)" --mode "$(or $(MODE),unified)"

ai-verify-focused:
	$(AI_PYTHON) scripts/ai_verify.py --root . --contract "$(CONTRACT)" --summary "$(SUMMARY)" --stage "$(or $(STAGE),task)" --mode unified --scope focused

ai-verify-full:
	$(AI_PYTHON) scripts/ai_verify.py --root . --contract "$(CONTRACT)" --summary "$(SUMMARY)" --stage "$(or $(STAGE),release)" --mode unified --scope full

ai-verify-policy:
	PYTHONPATH=scripts $(AI_PYTHON) -c 'from ai_verification_policy import order_checks; print(order_checks({"scope": [], "tests": ["scope"], "trust": ["scope"]}))'

ai-verify-impact-graph:
	PYTHONPATH=scripts $(AI_PYTHON) -c 'from ai_verification_policy import evaluate_current_impact_graph; print(evaluate_current_impact_graph(profile="standard", receipt_bindings={}))'

ai-cockpit-quality:
	+@set -eu; \
		$(AI_PYTHON) scripts/determine_governance_profile.py \
			$(if $(AI_BASE_COMMIT),--base "$(AI_BASE_COMMIT)",) \
			$(if $(CONTRACT),--contract "$(CONTRACT)",) \
			$(if $(GOVERNANCE_PROFILE),--profile "$(GOVERNANCE_PROFILE)",) \
			--output "$(GOVERNANCE_RECEIPT)"; \
		target=$$($(PYTHON_EXECUTABLE) -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["dispatchTarget"])' "$(GOVERNANCE_RECEIPT)"); \
		profile=$$($(PYTHON_EXECUTABLE) -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("selectedProfile", "unknown"))' "$(GOVERNANCE_RECEIPT)"); \
		escalations=$$($(PYTHON_EXECUTABLE) -c 'import json, sys; print(" ".join("--escalation " + value for value in json.load(open(sys.argv[1], encoding="utf-8")).get("verificationEscalations", [])))' "$(GOVERNANCE_RECEIPT)"); \
		escalation_reasons=$$($(PYTHON_EXECUTABLE) -c 'import json, shlex, sys; print(" ".join("--escalation-reason " + shlex.quote(value) for value in json.load(open(sys.argv[1], encoding="utf-8")).get("releaseEscalationReasons", [])))' "$(GOVERNANCE_RECEIPT)"); \
		case "$$target" in quality-fast|quality-standard|quality-full|quality-release) ;; *) echo "invalid governance dispatch target: $$target" >&2; exit 2;; esac; \
		$(QUALITY_MAKE) --no-print-directory "$$target" QUALITY_PROFILE="$$profile" QUALITY_ESCALATIONS="$$escalations" QUALITY_ESCALATION_REASONS="$$escalation_reasons"

ai-start:
	$(AI_PYTHON) scripts/ai_start.py --task "$(TASK)" --title "$(TITLE)" --mode "$(MODE)" $(if $(AI_START_CONCURRENCY_BOUNDARY),--concurrency-boundary '$(AI_START_CONCURRENCY_BOUNDARY)',) $(if $(AI_START_CALIBRATION_CORRECTIVE),--calibration-corrective '$(AI_START_CALIBRATION_CORRECTIVE)',)

ai-resume-work-item:
	@test -n "$(CONTRACT)" -a -n "$(BASE_REMOTE)" -a -n "$(BASE_BRANCH)" || (echo "CONTRACT, BASE_REMOTE, and BASE_BRANCH are required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_resume_work_item.py --contract "$(CONTRACT)" --base-remote "$(BASE_REMOTE)" --base-branch "$(BASE_BRANCH)"

ai-synchronize-work-item:
	@test -n "$(CONTRACT)" -a -n "$(BASE_REMOTE)" -a -n "$(BASE_BRANCH)" || (echo "CONTRACT, BASE_REMOTE, and BASE_BRANCH are required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_resume_work_item.py --synchronize --project-root "$(or $(TARGET_ROOT),.)" --contract "$(CONTRACT)" $(if $(TARGET_ROOT),$(if $(TARGET_SUMMARY),--summary "$(TARGET_SUMMARY)",),$(if $(SUMMARY),--summary "$(SUMMARY)",)) --base-remote "$(BASE_REMOTE)" --base-branch "$(BASE_BRANCH)"

ai-transition-conflict-successor:
	@test -n "$(SOURCE_ROOT)" -a -n "$(SOURCE_CONTRACT)" -a -n "$(SUCCESSOR_CONTRACT)" -a -n "$(BASE_REMOTE)" -a -n "$(BASE_BRANCH)" -a -n "$(ISSUE)" -a -n "$(AUTHORITY)" -a -n "$(REASON)" || (echo 'SOURCE_ROOT, SOURCE_CONTRACT, SUCCESSOR_CONTRACT, BASE_REMOTE, BASE_BRANCH, ISSUE, AUTHORITY, and REASON are required' >&2; exit 2)
	$(AI_PYTHON) scripts/ai_resume_work_item.py --transition-conflict-successor --project-root "$(or $(TARGET_ROOT),.)" --source-root "$(SOURCE_ROOT)" --source-contract "$(SOURCE_CONTRACT)" --successor-contract "$(SUCCESSOR_CONTRACT)" --base-remote "$(BASE_REMOTE)" --base-branch "$(BASE_BRANCH)" --issue "$(ISSUE)" --authority "$(AUTHORITY)" --reason "$(REASON)"

ai-onboard:
	$(AI_PYTHON) scripts/ai_onboard.py --root . $(if $(PHASE),--phase $(PHASE),) $(if $(SKIP_CALIBRATE),--skip-calibrate,) $(if $(SKIP_READINESS_CHECKS),--skip-readiness-checks,)

ai-doctor:
	$(AI_PYTHON) scripts/ai_doctor.py --root .

ai-lifecycle-facts:
	$(AI_PYTHON) scripts/ai_lifecycle_facts.py --root .

ai-work-item-status:
	$(AI_PYTHON) scripts/ai_work_item_status.py $(ARGS)

ai-work-item-intelligence-rebuild:
	$(AI_PYTHON) scripts/ai_work_item_status.py --rebuild $(ARGS)

ai-cockpit-version:
	$(AI_PYTHON) scripts/ai_install_status.py version --root .

ai-cockpit-update-check:
	$(AI_PYTHON) scripts/ai_install_status.py update-check --root . $(if $(TARGET_VERSION),--target-version $(TARGET_VERSION),)

ai-cockpit-update-propose:
	@test -n "$(OLD_TEMPLATE)" -a -n "$(NEW_TEMPLATE)" -a -n "$(UPGRADE_ID)" || (echo "OLD_TEMPLATE, NEW_TEMPLATE, and UPGRADE_ID are required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_upgrade_proposal.py --old-template "$(OLD_TEMPLATE)" --new-template "$(NEW_TEMPLATE)" --current-project . --upgrade-id "$(UPGRADE_ID)" --output ".ai/upgrade/proposals/$(UPGRADE_ID).json"

ai-cockpit-update-apply:
	@test -n "$(PROPOSAL)" || (echo "PROPOSAL is required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_upgrade_apply.py --proposal "$(PROPOSAL)" --root . $(if $(CONFIRM),--confirm "$(CONFIRM)",) $(if $(EXCLUDE),$(foreach path,$(EXCLUDE),--exclude "$(path)"),)

ai-cockpit-rollback-propose:
	@test -n "$(SNAPSHOT)" || (echo "SNAPSHOT is required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_rollback.py --snapshot "$(SNAPSHOT)" --current-root . --output "$(OUTPUT)"

ai-cockpit-disable:
	@test -n "$(STATE)" || (echo "STATE is required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_disable_enable.py disable --state "$(STATE)" --output "$(OUTPUT)"

ai-cockpit-enable:
	@test -n "$(STATE)" || (echo "STATE is required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_disable_enable.py enable --state "$(STATE)" --checks "$(CHECKS)" --output "$(OUTPUT)"

ai-cockpit-uninstall-propose:
	@test -n "$(FACTS)" || (echo "FACTS is required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_uninstall_proposal.py --facts "$(FACTS)" --mode "$(or $(UNINSTALL_MODE),preserve-evidence)" --output "$(OUTPUT)"

ai-cockpit-uninstall-facts:
	@test -n "$(ROOT)" -a -n "$(SESSION_ID)" -a -n "$(OUTPUT)" || (echo "ROOT, SESSION_ID, and OUTPUT are required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_uninstall_facts.py --root "$(ROOT)" --session-id "$(SESSION_ID)" --output "$(OUTPUT)"

ai-cockpit-uninstall-execute:
	@test -n "$(ROOT)" -a -n "$(PROPOSAL)" -a -n "$(CONFIRM_DIGEST)" || (echo "ROOT, PROPOSAL, and CONFIRM_DIGEST are required" >&2; exit 2)
	$(AI_PYTHON) scripts/ai_detached_uninstaller.py --root "$(ROOT)" --proposal "$(PROPOSAL)" --confirm-digest "$(CONFIRM_DIGEST)"

cross-stack-long-cycle:
	$(AI_PYTHON) scripts/cross_stack_long_cycle.py --root . > target/cross-stack-long-cycle.json

delusion-regression:
	$(AI_PYTHON) -m pytest -q tests/test_delusion_scenarios.py tests/test_unsupported_claim_regression.py

check-ai-adoption-ready:
	$(AI_PYTHON) scripts/ai_check_adoption_ready.py --root .

template-adoption-ready:
	AI_COCKPIT_EXECUTION_MODE=template_maintenance $(AI_NESTED_MAKE) check-ai-adoption-ready

check-ai-contract check-ai-work-item:
	$(AI_PYTHON) scripts/ai_check_work_item.py $(CONTRACT)

check-ai-serial-order:
	$(AI_PYTHON) scripts/ai_check_serial_order.py --contract "$(CONTRACT)"

check-ai-budget-impact:
	$(AI_PYTHON) scripts/ai_check_budget_impact.py --contract "$(CONTRACT)"

check-ai-scope:
	$(AI_PYTHON) scripts/ai_check_scope.py $(CONTRACT)

check-ai-guards:
	$(AI_PYTHON) scripts/ai_check_guards.py $(if $(CONTRACT),--contract $(CONTRACT))

check-ai-agent-risk:
	$(AI_PYTHON) scripts/ai_check_agent_risk.py $(if $(CONTRACT),--contract $(CONTRACT)) $(if $(SUMMARY),--summary $(SUMMARY))

ai-checkpoint:
	$(AI_PYTHON) scripts/ai_checkpoint.py --contract $(CONTRACT) $(if $(SUMMARY),--summary $(SUMMARY)) --stage "$(or $(STAGE),manual)" $(if $(PREVIOUS_CONTRACT_HASH),--previous-contract-hash "$(PREVIOUS_CONTRACT_HASH)") $(if $(AMENDMENT_REASON),--reason "$(AMENDMENT_REASON)")

check-ai-backtrack:
	$(AI_PYTHON) scripts/ai_check_backtrack.py

check-ai-coverage-guard:
	$(AI_PYTHON) scripts/ai_check_coverage_guard.py

REFERENCE_IMPACT_DIR ?= .ai/evidence/reference-impact
REFERENCE_IMPACT_OUTPUT_DIR ?= target/reference-impact

check-ai-reference-impact:
	@set -eu; \
		dir="$(REFERENCE_IMPACT_DIR)"; output_dir="$(REFERENCE_IMPACT_OUTPUT_DIR)"; found=false; \
		mkdir -p "$$output_dir"; \
		if test -d "$$dir"; then \
			for record in "$$dir"/*.json; do \
				test -f "$$record" || continue; found=true; name=$${record##*/}; \
				$(AI_PYTHON) scripts/ai_check_reference_impact.py --root . --record "$$record" --output "$$output_dir/$${name%.json}.decision.json" --enforce; \
			done; \
		fi; \
		if test "$$found" = false; then printf '%s\n' 'Reference impact: no declared records.'; fi

check-ai-test-weakening-fast:
	$(AI_PYTHON) scripts/ai_check_test_weakening.py --root . $(if $(AI_BASE_COMMIT),--base-ref "$(AI_BASE_COMMIT)",) --mode fast --policy .ai/guards/test_weakening_policy.yaml

check-ai-test-weakening:
	$(AI_PYTHON) scripts/ai_check_test_weakening.py --root . $(if $(AI_BASE_COMMIT),--base-ref "$(AI_BASE_COMMIT)",) --mode full --policy .ai/guards/test_weakening_policy.yaml

check-ai-scenario-coverage:
	$(AI_PYTHON) scripts/ai_check_scenario_coverage.py $(if $(CONTRACT),--contract $(CONTRACT)) $(if $(SUMMARY),--summary $(SUMMARY))

ai-preflight:
	$(AI_PYTHON) scripts/ai_preflight_review.py $(if $(CONTRACT),--contract $(CONTRACT))
	$(AI_PYTHON) scripts/ai_preflight_review.py --check $(if $(CONTRACT),--contract $(CONTRACT))
	@if [ "$(AI_PREFLIGHT_VALIDATE_CONTRACT)" = "true" ]; then $(AI_PYTHON) scripts/ai_check_work_item.py $(CONTRACT); fi
	$(AI_NESTED_MAKE) check-ai-serial-order CONTRACT="$(CONTRACT)"
	$(AI_NESTED_MAKE) check-ai-budget-impact CONTRACT="$(CONTRACT)"

ai-prepare-implementation:
	@test -n "$(CONTRACT)" -a -n "$(SUMMARY)" || (echo 'CONTRACT and SUMMARY are required' >&2; exit 2)
	$(AI_NESTED_MAKE) ai-preflight CONTRACT="$(CONTRACT)"
	$(AI_NESTED_MAKE) ai-checkpoint CONTRACT="$(CONTRACT)" SUMMARY="$(SUMMARY)" STAGE="before_edit"

ai-revalidate-contract-amendment:
	@test -n "$(CONTRACT)" -a -n "$(SUMMARY)" -a -n "$(PREVIOUS_CONTRACT_HASH)" -a -n "$(AMENDMENT_REASON)" || (echo 'CONTRACT, SUMMARY, PREVIOUS_CONTRACT_HASH, and AMENDMENT_REASON are required' >&2; exit 2)
	$(AI_NESTED_MAKE) ai-preflight CONTRACT="$(CONTRACT)"
	$(AI_NESTED_MAKE) ai-checkpoint CONTRACT="$(CONTRACT)" SUMMARY="$(SUMMARY)" STAGE="contract_amendment_revalidation" PREVIOUS_CONTRACT_HASH="$(PREVIOUS_CONTRACT_HASH)" AMENDMENT_REASON="$(AMENDMENT_REASON)"

check-ai-lifecycle-truth:
	$(AI_PYTHON) scripts/ai_lifecycle_truth.py --check

ai-transition-to-successor:
	@test -n "$(PREDECESSOR_TASK)" -a -n "$(SUCCESSOR_TASK)" -a -n "$(SUCCESSOR_BRANCH)" -a -n "$(SUCCESSOR_BASE)" -a -n "$(ISSUE)" -a -n "$(AUTHORITY)" -a -n "$(MODE)" -a -n "$(REASON)" || (echo 'PREDECESSOR_TASK, SUCCESSOR_TASK, SUCCESSOR_BRANCH, SUCCESSOR_BASE, ISSUE, AUTHORITY, MODE, and REASON are required' >&2; exit 2)
	$(AI_PYTHON) scripts/ai_lifecycle_truth.py --transition-to-successor --root "$(or $(TARGET_ROOT),.)" --predecessor-task "$(PREDECESSOR_TASK)" --successor-task "$(SUCCESSOR_TASK)" --successor-branch "$(SUCCESSOR_BRANCH)" --successor-base "$(SUCCESSOR_BASE)" --issue "$(ISSUE)" --authority "$(AUTHORITY)" --mode "$(MODE)" --reason "$(REASON)"

ai-open-post-archive-recovery:
	@test -n "$(TASK)" -a -n "$(AI_BASE_COMMIT)" -a -n "$(ISSUE)" -a -n "$(AUTHORITY)" -a -n "$(RECOVERY_PATHS)" || (echo 'TASK, AI_BASE_COMMIT, ISSUE, AUTHORITY, and RECOVERY_PATHS are required' >&2; exit 2)
	@if test -n "$(HOSTED_RUN_ID)$(HOSTED_JOB_ID)$(HOSTED_REPOSITORY)$(HOSTED_PULL_REQUEST)$(HOSTED_CANDIDATE_HEAD)"; then \
		test -n "$(HOSTED_REPOSITORY)" -a -n "$(HOSTED_PULL_REQUEST)" -a -n "$(HOSTED_CANDIDATE_HEAD)" -a -n "$(HOSTED_RUN_ID)" -a -n "$(HOSTED_JOB_ID)" || { echo 'HOSTED_REPOSITORY, HOSTED_PULL_REQUEST, HOSTED_CANDIDATE_HEAD, HOSTED_RUN_ID, and HOSTED_JOB_ID are all required together' >&2; exit 2; }; \
		$(AI_PYTHON) scripts/ai_post_archive_recovery.py --task "$(TASK)" --base "$(AI_BASE_COMMIT)" --issue "$(ISSUE)" --authority "$(AUTHORITY)" $(foreach path,$(RECOVERY_PATHS),--recovery-path "$(path)") --hosted-repository "$(HOSTED_REPOSITORY)" --hosted-pull-request "$(HOSTED_PULL_REQUEST)" --hosted-candidate-head "$(HOSTED_CANDIDATE_HEAD)" --hosted-run-id "$(HOSTED_RUN_ID)" --hosted-job-id "$(HOSTED_JOB_ID)"; \
	else \
		$(AI_PYTHON) scripts/ai_post_archive_recovery.py --task "$(TASK)" --base "$(AI_BASE_COMMIT)" --issue "$(ISSUE)" --authority "$(AUTHORITY)" $(foreach path,$(RECOVERY_PATHS),--recovery-path "$(path)"); \
	fi

ai-prepare-hosted-verification-snapshot:
	@test -n "$(CONTRACT)" || (echo 'CONTRACT=<active-contract.json> is required' >&2; exit 2)
	$(AI_PYTHON) scripts/ai_prepare_hosted_verification.py \
		--contract "$(CONTRACT)" \
		--output "$(or $(OUTPUT),target/hosted-verification-snapshot.json)"

generate-ai-preflight-review:
	$(AI_PYTHON) scripts/ai_preflight_review.py $(if $(CONTRACT),--contract $(CONTRACT))

check-ai-preflight-review:
	$(AI_PYTHON) scripts/ai_preflight_review.py --check $(if $(CONTRACT),--contract $(CONTRACT))

check-ai-guidelines:
	$(AI_PYTHON) scripts/ai_check_guidelines.py --contract $(CONTRACT) --summary $(SUMMARY)

check-ai-review-policy:
	$(AI_PYTHON) scripts/ai_check_review_policy.py $(if $(SUMMARY),--summary $(SUMMARY))

check-ai-change-summary:
	$(AI_PYTHON) scripts/ai_check_summary.py $(SUMMARY) $(SUMMARY_ARGS) $(ARGS)

generate-cockpit-status:
	$(AI_PYTHON) scripts/ai_generate_status.py $(CONTRACT) $(STATUS_ARGS) $(ARGS)

generate-cockpit-status-ja:
	$(AI_PYTHON) scripts/ai_generate_status.py $(CONTRACT) $(STATUS_ARGS) --language ja --output target/ai_cockpit_status.ja.md

check-ai-status:
	$(AI_PYTHON) scripts/ai_check_status.py .ai/cockpit/current_status.md $(SUMMARY_ARGS) $(STATUS_ARGS)

check-ai-status-ja:
	$(AI_PYTHON) scripts/ai_check_status.py target/ai_cockpit_status.ja.md $(SUMMARY_ARGS) $(STATUS_ARGS) --language ja

check-ai-status-consistency:
	$(AI_PYTHON) scripts/ai_check_status_consistency.py

check-ai-task-outcome:
	@test -n "$(OUTCOME)" || (echo 'OUTCOME=<outcome.json> is required'; exit 2)
	$(AI_PYTHON) -c "import json, pathlib, sys; sys.path.insert(0, 'scripts'); from ai_check_task_outcome import validate_outcome; outcome=json.loads(pathlib.Path('$(OUTCOME)').read_text()); report=validate_outcome(outcome, pathlib.Path('$(MARKDOWN)').read_text() if '$(MARKDOWN)' else None); print('task outcome valid' if report.valid else '\\n'.join(f'{e.code}: {e.message}' for e in report.errors)); raise SystemExit(0 if report.valid else 1)"

generate-human-benefit-report:
	@test -n "$(OUTCOME)" || (echo 'OUTCOME=<outcome.json> is required'; exit 2)
	$(AI_PYTHON) scripts/ai_generate_human_report.py "$(OUTCOME)" "$(or $(OUTPUT_JSON),.ai/cockpit/task_report.json)" "$(or $(OUTPUT_MARKDOWN),.ai/cockpit/task_report.md)"

check-human-benefit-report:
	@test -n "$(OUTCOME)" || (echo 'OUTCOME=<outcome.json> is required'; exit 2)
	$(AI_PYTHON) scripts/ai_generate_human_report.py --check "$(OUTCOME)" "$(or $(OUTPUT_JSON),.ai/cockpit/task_report.json)" "$(or $(OUTPUT_MARKDOWN),.ai/cockpit/task_report.md)"

render-task-outcome-pr:
	@test -n "$(OUTCOME)" || (echo 'OUTCOME=<outcome.json> is required'; exit 2)
	@test -n "$(PROFILE)" || (echo 'PROFILE=<project_profile.yaml> is required'; exit 2)
	$(AI_PYTHON) scripts/ai_render_task_outcome_pr.py "$(OUTCOME)" "$(PROFILE)" $(if $(LANGUAGE),--language "$(LANGUAGE)") $(if $(OUTPUT),--output "$(OUTPUT)")

render-task-outcome-multilingual:
	@test -n "$(OUTCOME)" || (echo 'OUTCOME=<outcome.json> is required'; exit 2)
	@test -n "$(PROFILE)" || (echo 'PROFILE=<project_profile.yaml> is required'; exit 2)
	@test -n "$(OUTPUT_DIR)" || (echo 'OUTPUT_DIR=<directory> is required'; exit 2)
	$(AI_PYTHON) scripts/ai_render_task_outcome_multilingual.py "$(OUTCOME)" "$(PROFILE)" "$(OUTPUT_DIR)"

repair-ai-status:
	$(AI_PYTHON) scripts/ai_check_status_consistency.py --repair

archive-work-item:
	$(AI_PYTHON) scripts/ai_archive_work_item.py $(CONTRACT) $(ARGS)

ai-close-work-item:
	$(AI_PYTHON) scripts/ai_close_work_item.py --task "$(TASK)" $(ARGS)

ai-assess-provider-merge-state-recovery:
	$(AI_PYTHON) scripts/ai_provider_merge_state_recovery.py $(ARGS)

check-ai:
	@if [ -n "$(CONTRACT)" ]; then \
		$(AI_NESTED_MAKE) check-ai-contract CONTRACT="$(CONTRACT)" && \
		$(AI_NESTED_MAKE) check-ai-serial-order CONTRACT="$(CONTRACT)" && \
		$(AI_NESTED_MAKE) check-ai-budget-impact CONTRACT="$(CONTRACT)" && \
		$(AI_NESTED_MAKE) check-ai-scope CONTRACT="$(CONTRACT)" && \
		$(AI_NESTED_MAKE) check-ai-guards CONTRACT="$(CONTRACT)" && \
		$(AI_NESTED_MAKE) check-ai-agent-risk CONTRACT="$(CONTRACT)" SUMMARY="$(SUMMARY)" && \
		$(AI_NESTED_MAKE) check-ai-review-policy SUMMARY="$(SUMMARY)" && \
		$(AI_NESTED_MAKE) check-ai-backtrack && \
		$(AI_NESTED_MAKE) check-ai-coverage-guard && \
		$(AI_NESTED_MAKE) check-ai-scenario-coverage CONTRACT="$(CONTRACT)" SUMMARY="$(SUMMARY)" && \
		$(AI_NESTED_MAKE) check-ai-guidelines CONTRACT="$(CONTRACT)" SUMMARY="$(SUMMARY)" && \
		$(AI_NESTED_MAKE) check-ai-change-summary SUMMARY="$(SUMMARY)" CONTRACT="$(CONTRACT)" && \
		$(AI_NESTED_MAKE) generate-cockpit-status CONTRACT="$(CONTRACT)" SUMMARY="$(SUMMARY)" && \
		$(AI_NESTED_MAKE) check-ai-status CONTRACT="$(CONTRACT)" SUMMARY="$(SUMMARY)" && \
		$(AI_NESTED_MAKE) check-ai-status-consistency; \
	else \
		$(AI_NESTED_MAKE) check-ai-status-consistency && \
		$(AI_NESTED_MAKE) check-ai-backtrack && \
		$(AI_NESTED_MAKE) check-ai-coverage-guard && \
		$(AI_NESTED_MAKE) check-ai-diff-ownership && \
		test -n "$(AI_BASE_COMMIT)" && \
		$(AI_NESTED_MAKE) check-ai-pr AI_BASE_COMMIT="$(AI_BASE_COMMIT)"; \
	fi

check-ai-pr-core:
	$(AI_PYTHON) scripts/ai_check_pr.py --base "$(AI_BASE_COMMIT)"

check-ai-pr:
	@set -e; \
		$(AI_NESTED_MAKE) project-format-check; \
		$(AI_NESTED_MAKE) project-lint; \
		$(AI_NESTED_MAKE) check-changed-critical-coverage AI_BASE_COMMIT="$(AI_BASE_COMMIT)"; \
		$(AI_NESTED_MAKE) check-ai-reference-impact; \
		$(AI_NESTED_MAKE) check-ai-test-weakening AI_BASE_COMMIT="$(AI_BASE_COMMIT)"; \
		if test -f scripts/check_governance_complexity.py && test -f .ai/guards/governance_complexity_policy.yaml; then \
			$(AI_PYTHON) scripts/check_governance_complexity.py; \
		fi; \
		$(AI_NESTED_MAKE) check-ai-pr-core AI_BASE_COMMIT="$(AI_BASE_COMMIT)"

ai-finish:
	@# ARCHIVE is a one-shot lifecycle request. Do not let Make propagate it into
	@# nested project/test invocations, where it could archive an unrelated Work Item.
	env -u ARCHIVE -u MAKEFLAGS -u MAKEOVERRIDES REPORT_LANGUAGE= $(AI_PYTHON) scripts/ai_finish.py --task "$(TASK)" $(if $(filter true,$(SKIP_QUALITY)),--skip-quality) $(if $(filter true,$(ARCHIVE)),--archive) $(if $(REPORT_LANGUAGE),--language "$(REPORT_LANGUAGE)")
