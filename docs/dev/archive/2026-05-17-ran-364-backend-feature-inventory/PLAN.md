# RAN-364: Backend Feature Inventory In atlas-catalog

Ryan explicitly authorized: "Plan + implement in one pass if straightforward." This plan records the scoped implementation contract followed in the same pass.

## Context Assembly

- **Files read (mandatory):**
  - Atlas main `docs/dev/ATLAS_DEV_WORKFLOW.md`
  - Atlas main `src/inference/backend_contract.py`
  - Atlas main `src/inference/backends/ollama.py`
  - Atlas main `src/inference/backends/cloud.py`
  - Atlas main `src/inference/backends/llama_cpp_server.py`
  - atlas-catalog `README.md`
  - atlas-catalog `catalog.json`
  - atlas-catalog `scripts/validate_catalog.py`
  - atlas-catalog `scripts/catalog_discovery/backend_score_schema.py`
  - atlas-catalog tests under `tests/`
- **Systems impacted:** atlas-catalog static catalog schema, catalog validator, README maintainer docs, tests.
- **Known constraints:** additive catalog-only change; current Atlas runtime must ignore the new `backends` collection; no Atlas app-code consumer changes; cite sources for feature flags; draft PR only for human catalog review.
- **Assumptions:** the missing `docs/dev/current/ran-190-v2/EPIC_ARCHITECTURE.md` path is superseded by Linear RAN-364 and merged RAN-335/RAN-336/RAN-345/RAN-352 source; `catalog_version` should bump from 4 to 5 because this is a top-level schema extension.

## Approach

Add a top-level `backends` inventory using the exact RAN-335 `BackendFeatureMatrix` field names. Preserve model rows unchanged so current Atlas runtime readers continue to ignore the additive collection.

Implement a focused backend inventory validator, thread top-level backend IDs into existing backend-composite-score validation, and add regression tests before implementation. Use current upstream documentation for forward-declared MLX-LM and vLLM values, and Atlas source declarations for already-implemented adapters.

## Execution Contract

- **Files allowed to edit:**
  - `catalog.json`
  - `README.md`
  - `scripts/validate_catalog.py`
  - `scripts/catalog_discovery/backend_score_schema.py`
  - `scripts/catalog_discovery/backend_inventory_schema.py`
  - `tests/test_backend_inventory_schema.py`
  - `docs/dev/current/ran-364/LINEAR_ISSUE.md`
  - `docs/dev/current/ran-364/PLAN.md`
  - `docs/dev/current/ran-364/CODEX_REPORT.md`
  - `docs/dev/current/ran-364/VALIDATION.md`
- **Files explicitly forbidden:** Atlas main application code; existing model row behavior except additive validation support; discovery publish behavior outside validator schema checks.
- **Acceptance criteria:** copied in `LINEAR_ISSUE.md`.
- **Required validation commands:**
  - `python -m unittest tests.test_backend_inventory_schema`
  - `python -m unittest discover -s tests`
  - `python scripts/validate_catalog.py catalog.json`
- **Verification targets:** catalog validates; focused tests reject malformed backends and unknown model/backend references; full test suite remains green.
- **Definition of done:** all acceptance criteria have evidence in `VALIDATION.md`, draft PR is opened, Linear receives implementation summary, and Goose/Claude receives a handoff prompt for human catalog review.

## Architecture

The new schema is data-only and additive. `backends[]` does not alter existing `models[]` fields or current runtime fetch semantics. Validator integration is intentionally one-way: backend inventory defines known backend IDs, and model/backend score references are checked against that inventory when present.

Do not break:

- Existing model row validation.
- Existing benchmark provenance validation.
- Existing backend composite score tests.
- Discovery worker output compatibility.

## Risk & Mitigation

- **Risk:** Feature values drift from Atlas runtime declarations. **Mitigation:** mirror RAN-335/RAN-336/RAN-345/RAN-352 source for implemented backends and cite upstream docs only as context.
- **Risk:** Forward-declared MLX-LM/vLLM flags overstate support. **Mitigation:** use conservative notes and cite current upstream docs; leave vLLM `max_batch_size` null because it is deployment-dependent.
- **Risk:** Validator blocks future catalog rows unexpectedly. **Mitigation:** support both `backend_id` and `backend_ids` only when rows declare them; existing rows without backend references remain valid.

## Test Strategy

Use TDD for schema behavior:

1. Add failing tests for valid backend inventory, malformed backend entries, unknown `backend_id`, and unknown backend composite score references.
2. Implement validator helper and integration.
3. Run focused tests, full unittest discovery, and catalog validation.

No browser/UI validation is needed because this is catalog and validator only.

## UI/UX Surface

No UI or user-visible Atlas runtime behavior changes. Current runtime readers ignore the additive collection.

## Predicted Next 3 Failures

1. Compact provenance schema missing a feature flag source.
2. Existing backend composite score tests failing because known backend validation became too strict.
3. Catalog JSON schema bump causing stale README examples or validator assumptions.

## Rollback Plan

If catalog validation, tests, or human catalog review rejects the inventory, revert the RAN-364 commit/PR. Because the change is additive and no runtime consumer reads `backends` yet, rollback is limited to removing the new collection and validator/doc/test additions.
