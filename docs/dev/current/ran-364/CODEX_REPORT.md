# RAN-364 CODEX Report

## Issue

- **ID:** RAN-364
- **Title:** Model System v2 §2.6: Backend feature inventory in atlas-catalog
- **Branch:** `codex/ran-364-backend-feature-inventory`
- **Commit range:** `origin/main..HEAD`
- **Draft PR:** https://github.com/Quiet-Node-io/atlas-catalog/pull/12

## Files Changed

- `catalog.json` — bumps schema to version 5 and adds top-level `backends` inventory for `ollama`, `mlx_lm`, `llama_cpp_server`, `vllm`, `openai`, `anthropic`, `google`, and `xai`.
- `README.md` — documents the new `backends` collection, full feature schema, provenance requirements, and validator behavior.
- `scripts/catalog_discovery/backend_inventory_schema.py` — adds validation for backend inventory entries, RAN-335 feature fields, sampling params, auth modes, and per-feature provenance.
- `scripts/catalog_discovery/backend_score_schema.py` — allows catalog-level backend IDs to constrain backend-aware composite score records.
- `scripts/validate_catalog.py` — wires backend inventory validation into catalog validation and rejects unknown model `backend_id` / `backend_ids`.
- `tests/test_backend_inventory_schema.py` — adds focused regression coverage for valid inventory, malformed entries, unknown model backend IDs, and unknown backend score references.
- `docs/dev/current/ran-364/LINEAR_ISSUE.md` — frozen Linear scope snapshot.
- `docs/dev/current/ran-364/PLAN.md` — one-pass implementation plan under Ryan's explicit instruction.
- `docs/dev/current/ran-364/CODEX_REPORT.md` — this implementation report.
- `docs/dev/current/ran-364/VALIDATION.md` — validation evidence and acceptance check.

## Summary

Added a catalog-native backend feature inventory that mirrors RAN-335 `BackendFeatureMatrix` field names and keeps runtime compatibility by leaving all existing model rows unchanged. The validator now checks malformed backend entries and unknown backend references when rows declare `backend_id`, `backend_ids`, or backend-aware composite score records.

MLX-LM and vLLM flags were verified against current upstream docs. Implemented Atlas backends mirror current Atlas adapter declarations, with provider/upstream docs included as provenance context where relevant.

## Commands Run

- `git fetch origin main` — exit 0
- `python scripts/validate_catalog.py catalog.json` — exit 0, `catalog.json: catalog validation passed`
- `python -m unittest tests.test_backend_inventory_schema` — exit 0, 4 tests passed
- `python -m unittest discover -s tests` — exit 0, 25 tests passed
- `python -m py_compile scripts/validate_catalog.py scripts/catalog_discovery/backend_inventory_schema.py scripts/catalog_discovery/backend_score_schema.py` — exit 0

## Test Results

- Focused backend inventory tests: 4 passed, 0 failed.
- Full unittest discovery: 25 passed, 0 failed.
- Catalog validation: passed.
- Python compile check for touched validator modules: passed.

## Live Smoke Results

Not applicable. This is a static catalog/validator change. No Atlas runtime consumer reads the new `backends` collection until a future ticket.

## Browser/UI Validation

Not applicable. No UI files or user-visible runtime behavior changed.

## Deviations From PLAN.md

The requested Atlas path `docs/dev/current/ran-190-v2/EPIC_ARCHITECTURE.md` did not exist in the main Atlas checkout. I searched `docs/`, `knowledge/`, and `src/`; implementation used the Linear RAN-364 scope plus current RAN-335/RAN-336/RAN-345/RAN-352 source declarations and upstream docs.

## Open Questions / Follow-Ups

- Human catalog review should confirm the conservative values for forward-declared MLX-LM and vLLM before publish.
- A future Atlas runtime ticket still needs to consume the `backends` collection.

## Acceptance Criteria Check

1. `catalog.json` contains required `backends` entries — pass; validator passed with all eight required IDs present.
2. Each entry includes `backend_id`, `version_range`, full RAN-335 feature matrix, `notes`, and provenance — pass; validator enforces all feature fields and per-feature provenance.
3. Validator rejects malformed backend entries — pass; `tests.test_backend_inventory_schema` covers missing/invalid backend fields.
4. Validator rejects models referencing unknown `backend_id` — pass; focused test covers unknown `backend_id`; implementation also supports `backend_ids`.
5. README documents the collection and how to add a backend — pass.
6. Atlas runtime unchanged — pass; no Atlas application code changed and existing model rows remain compatible.
7. Draft PR and human review before publish — pass; draft PR opened at https://github.com/Quiet-Node-io/atlas-catalog/pull/12.
