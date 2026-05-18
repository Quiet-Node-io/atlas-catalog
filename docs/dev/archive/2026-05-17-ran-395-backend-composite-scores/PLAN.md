# RAN-395: Atlas-catalog Backend Composite Score Population

## Context Assembly

- **Files to read (mandatory):**
  - Atlas main `/Users/atlas-dev-rr/Documents/GitHub/atlas/docs/dev/ATLAS_DEV_WORKFLOW.md`
  - Atlas main `/Users/atlas-dev-rr/Documents/GitHub/atlas/knowledge/system/model-scoring-methodology.md`
  - atlas-catalog `README.md`
  - atlas-catalog `catalog.json`
  - atlas-catalog `scripts/validate_catalog.py`
  - atlas-catalog `scripts/catalog_discovery/backend_score_schema.py`
  - atlas-catalog `scripts/catalog_discovery/backend_scoring.py`
  - atlas-catalog `scripts/catalog_discovery/backend_inventory_schema.py`
  - atlas-catalog `scripts/catalog_discovery/benchmark_provenance.py`
  - atlas-catalog `scripts/catalog_discovery/safety.py`
  - atlas-catalog `tests/test_catalog_discovery_backend_scoring.py`
  - atlas-catalog `docs/dev/archive/2026-05-17-ran-364-backend-feature-inventory/PLAN.md`
  - atlas-catalog `docs/dev/archive/2026-05-17-ran-350-reranker-catalog-rows/PLAN.md`
- **Systems impacted:** atlas-catalog static JSON payload, catalog validation, catalog discovery safety guard, RAN-366 Terry onboarding data prerequisite.
- **Known constraints:**
  - RAN-347 hard rule: no invented benchmark values. If a cited public source is missing, omit the value or use `missing_reason`.
  - RAN-351 schema: score records live under each model row as `backend_composite_scores`; benchmark components reference `benchmarks_meta.<metric>`, while backend and runtime components require `source_url` plus `retrieved_at` when scored.
  - RAN-364 schema: backend IDs must match the top-level `backends` collection. The present catalog has `ollama`, `mlx_lm`, `llama_cpp_server`, `vllm`, `openai`, `anthropic`, `google`, and `xai`.
  - Current `backend_score_schema.py` accepts `text`, `vision`, `embedding`, `multimodal`, `image`, and `audio` modalities, but target reranker rows currently use `modality: "reranking"`. This needs either a validator extension or score records using an accepted modality; see assumptions.
  - Current `catalog.json` target rows mostly have empty `benchmarks` and no `benchmarks_meta`. Any scored benchmark component therefore requires adding properly sourced `benchmarks_meta`; otherwise `benchmark_composite` must carry `missing_reason`.
  - Infrastructure details, hostnames, tokens, local paths, and raw private profiler output must not be written into catalog rows or docs.
- **Assumptions:**
  - This task is data-only and additive; `catalog_version` remains `5` because no schema change is planned unless the reranker modality validator needs extension.
  - Hardware tiers will use existing safe schema classes: local Apple Silicon as `node_class: "local"` and `hardware_class: "performance"` for 96GB/workstation-class Macs; local NVIDIA/vLLM as `node_class: "cluster"` and `hardware_class: "high_performance"`; cloud as `node_class: "cloud"` and `hardware_class: "unknown"`.
  - For all benchmark components, use only benchmark metrics already present or newly sourced with `benchmarks_meta`; do not backfill broad model benchmarks unless they are needed for RAN-395 scoring.
  - For reranker score records, prefer adding `"reranking"` to `KNOWN_MODALITIES` because the rows already declare that modality and the score tuples should remain semantically accurate.

## Approach

Add additive `backend_composite_scores` arrays to the target model rows. For every applicable backend tuple, compute components with the RAN-351 weights: `benchmark_composite` `0.60`, `backend_capability` `0.25`, and `runtime_profile` `0.15`.

Use the top-level RAN-364 backend inventory as the source of backend feature truth. Because the helper in `backend_scoring.py` expects discovery-style profile keys that differ from the published `backends[].features` names, implementation should either adapt the data in a small test-covered helper or explicitly generate the JSON records from a local mapping that preserves the same scoring rules. The resulting records must remain plain catalog data; Atlas runtime should not fetch sources or compute scores dynamically.

For benchmark values, inspect each target row first. Where catalog benchmark coverage exists and provenance can be added or already exists, include a benchmark component. Where no cited value exists, keep `benchmark_composite` unscored with a clear `missing_reason`. For runtime profile, use public throughput/latency pages only when a source provides enough model/backend/hardware-specific detail; otherwise use `runtime_profile_not_reported` or a more specific missing reason.

## Execution Contract

- **Files allowed to edit:**
  - `catalog.json`
  - `scripts/catalog_discovery/backend_score_schema.py` only if needed to add `reranking` as a known modality
  - `tests/test_ran395_backend_composite_scores.py`
  - `docs/dev/current/ran-395/LINEAR_ISSUE.md`
  - `docs/dev/current/ran-395/PLAN.md`
  - `docs/dev/current/ran-395/CODEX_REPORT.md`
  - `docs/dev/current/ran-395/VALIDATION.md`
- **Files explicitly forbidden:**
  - Atlas main application code
  - GitHub workflow files
  - Existing unrelated model rows outside the RAN-395 target set
  - Existing backend inventory values unless a cited source review proves they must change and Goose/Claude approves a plan revision
  - Any file containing infrastructure access details, secrets, hostnames, tokens, or private operational paths
- **Acceptance criteria:**
  1. atlas-catalog `catalog.json` contains `backend_composite_scores` for the 15+ models above across applicable (backend x hardware x quant) tuples.
  2. Each score has source provenance per RAN-351 schema.
  3. Catalog validator passes with new score data.
  4. Safety guard passes.
  5. RAN-366 reference dependency satisfied; Terry onboarding can now consume scores.
  6. Draft PR; human catalog review before publish.
- **Required validation commands:**
  - `python -m unittest tests.test_ran395_backend_composite_scores`
  - `python scripts/validate_catalog.py catalog.json`
  - `git show origin/main:catalog.json > /tmp/ran395-base-catalog.json && python scripts/catalog_discovery/safety.py --base /tmp/ran395-base-catalog.json --proposed catalog.json`
  - `python -m unittest discover -s tests`
  - If a PR is opened: `gh pr checks <pr-number> --watch`
- **Verification targets:**
  - Every RAN-395 target row has at least one `backend_composite_scores` record for each applicable backend/quant tuple listed in Linear.
  - Every score record validates against known backend IDs, safe node/hardware classes, known quantizations, known task IDs, valid context token counts, and allowed modality values.
  - Scored benchmark components reference existing `benchmarks_meta.<metric>` entries; unscored components include `missing_reason`.
  - Backend capability and runtime profile components either carry public `source_url` plus valid ISO `retrieved_at`, or carry `missing_reason`.
  - Safety guard reports additive/no destructive changes.
- **Definition of done:**
  - Focused RAN-395 assertions pass.
  - Catalog validator passes.
  - Safety guard passes against `origin/main:catalog.json`.
  - Full unittest discovery passes.
  - `CODEX_REPORT.md` and `VALIDATION.md` list exact files changed and real command output/exit status.
  - Draft PR is opened for human catalog review.
  - Linear RAN-395 receives an implementation comment with PR link and validation evidence.
  - No Linear RAN-366 update until after merge confirms the prerequisite is satisfied.

## Architecture

This remains a static catalog-data change. `backend_composite_scores` are published records inside model rows and are not computed at Atlas runtime. Atlas consumers can use tuple keys `(model_id, backend, node_class, hardware_class, quantization, task_id)` directly after catalog refresh.

Do not break:

- Existing model row schema and validation.
- Existing RAN-192 benchmark scoring behavior.
- Existing RAN-347 benchmark provenance validation.
- Existing RAN-364 backend inventory validation.
- Discovery worker compatibility.
- Safety guard destructive-change protections.

Integration points:

- `catalog.json` target model rows receive score arrays.
- `scripts/validate_catalog.py` invokes `validate_backend_composite_scores` for each row.
- RAN-366 will read the published data after this PR is merged and catalog refresh occurs.

## Risk & Mitigation

- **Risk:** Public benchmark coverage is absent for several target rows. **Mitigation:** leave `benchmark_composite` unscored with `missing_reason`; do not infer from capability ratings or neighboring quantizations.
- **Risk:** Runtime throughput sources are sparse or hardware-specific. **Mitigation:** score runtime only where the source matches the tuple closely enough; otherwise record missing reason and let coverage reflect the gap.
- **Risk:** Backend capability scoring overstates non-generation backends such as rerankers or embedding rows. **Mitigation:** score only applicable feature facts and ensure task/modality assertions cover embedding/reranking cases.
- **Risk:** Manual JSON edits introduce duplicate or malformed records. **Mitigation:** add focused assertions for tuple uniqueness and required RAN-395 coverage before editing catalog data.
- **Risk:** Safety guard command in the handoff was written without args, but the current script requires `--base` and `--proposed`. **Mitigation:** run the parameterized command above and document the exact script behavior in `VALIDATION.md`.

## Test Strategy

Use TDD for the catalog data contract:

1. Add `tests/test_ran395_backend_composite_scores.py` with failing assertions for target coverage, tuple uniqueness, provenance/missing-reason behavior, backend IDs, and no out-of-scope target modifications.
2. Run `python -m unittest tests.test_ran395_backend_composite_scores` and confirm it fails because the score records do not yet exist.
3. Add the `catalog.json` score data and any minimal validator change needed for `reranking` modality.
4. Re-run the focused test until it passes.
5. Run catalog validator, safety guard, and full unittest discovery.

No browser/UI validation is required because this repo change is catalog data only and introduces no frontend or direct user interaction.

## UI/UX Surface

Not applicable. RAN-395 edits atlas-catalog data only. It does not modify frontend files, routes, screens, modals, forms, toasts, buttons, role-based views, destructive flows, or accessibility behavior.

## Predicted Next 3 Failures

1. Validator rejects reranker score records because `"reranking"` is not in `KNOWN_MODALITIES`.
2. Focused tests catch missing `benchmarks_meta` references if benchmark components are scored from flat `benchmarks` without provenance.
3. Safety guard fails if any target row is accidentally removed, marked superseded, or otherwise changed beyond additive score/provenance fields.

## Rollback Plan

If validation or human catalog review rejects the change, revert the additive `backend_composite_scores` arrays, any RAN-395-specific `benchmarks_meta` additions, and the optional `KNOWN_MODALITIES` `"reranking"` validator extension. Because the change is catalog-data-only and no runtime code is modified, rollback is limited to restoring `catalog.json` and the focused test/validator files to their pre-RAN-395 state.

