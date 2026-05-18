# RAN-395 CODEX Report

## 1. Linear Issue

- **ID:** RAN-395
- **Title:** Atlas-catalog: populate backend_composite_scores for top ~15 models (unblocks RAN-366 Terry onboarding)
- **Linear:** https://linear.app/randhq/issue/RAN-395/atlas-catalog-populate-backend-composite-scores-for-top-15-models
- **Draft PR:** https://github.com/Quiet-Node-io/atlas-catalog/pull/14

## 2. Branch And Commit Range

- **Branch:** `codex/ran-395-backend-composite-scores`
- **Base:** `origin/main`
- **Implementation commit:** `9d7b8f8`
- **Range for review:** `origin/main..codex/ran-395-backend-composite-scores`

## 3. Files Changed

- `catalog.json` — adds `backend_composite_scores` to the RAN-395 target model rows and adds `benchmarks_meta` provenance for existing Llama 3.2 Vision benchmark values.
- `scripts/catalog_discovery/backend_score_schema.py` — allows `reranking` as a backend score modality so reranker rows can use their existing semantic modality.
- `tests/test_ran395_backend_composite_scores.py` — focused RAN-395 assertions for tuple coverage, uniqueness, component provenance/missing reasons, validator acceptance, and Llama Vision score math.
- `docs/dev/current/ran-395/LINEAR_ISSUE.md` — frozen Linear scope snapshot.
- `docs/dev/current/ran-395/PLAN.md` — approved implementation plan.
- `docs/dev/current/ran-395/CODEX_REPORT.md` — this report.
- `docs/dev/current/ran-395/VALIDATION.md` — validation evidence.

## 4. Summary Of Changes

Populated 23 backend-aware composite score records across 16 priority catalog rows. The records cover the requested Apple Silicon, NVIDIA/vLLM, vision, embedding/reranker, and cloud tuples. Missing benchmark or runtime data is explicit via `missing_reason`; no synthetic benchmark/runtime values were added.

Backend capability components are scored from the existing RAN-364 `backends` inventory. Llama 3.2 Vision uses existing catalog benchmark values with added official HuggingFace model-card provenance. Runtime profile components remain unscored where no tuple-specific public throughput/latency source was available.

Sample scores:

| Model | Backend | Task | Score | Coverage |
| --- | --- | --- | ---: | ---: |
| `llama3.2-vision:11b` | `ollama` | `vision_input` | 62 | 0.85 |
| `qwen2.5-coder:32b` | `ollama` | `code_generation` | 40 | 0.25 |
| `qwen2.5-coder:32b` | `vllm` | `code_generation` | 100 | 0.25 |
| `gemma4:4.5b` | `ollama` | `vision_input` | 40 | 0.25 |
| `gemma4:4.5b` | `mlx_lm` | `vision_input` | 20 | 0.25 |
| `claude-haiku-4-5-20251001` | `anthropic` | `vision_input` | 60 | 0.25 |

## 5. Commands Run

- `python scripts/validate_catalog.py catalog.json` — exit 0 before implementation; baseline validator passed.
- `python -m unittest discover -s tests` — exit 0 before implementation; 26 tests passed.
- `python -m unittest tests.test_ran395_backend_composite_scores` — exit 1 after writing the focused test; failed because score rows and Llama benchmark provenance were not yet populated.
- `python -m unittest tests.test_ran395_backend_composite_scores` — exit 0 after implementation; 4 tests passed.
- `python scripts/validate_catalog.py catalog.json` — exit 0 after implementation; catalog validation passed.
- `git show origin/main:catalog.json > /tmp/ran395-base-catalog.json && python scripts/catalog_discovery/safety.py --base /tmp/ran395-base-catalog.json --proposed catalog.json` — exit 0; allowed true, no issues, no override.
- `python -m unittest discover -s tests` — exit 0 after implementation; 30 tests passed.
- `git diff --check` — exit 0; no whitespace errors.
- `gh pr create --draft ...` — exit 0; created PR #14.
- `gh pr checks 14` — exit 8 while GitHub validation was pending at first check.
- `gh pr checks 14 --watch` — exit 0; GitHub `validate` check passed in 9s.

## 6. Test Results

- Focused RAN-395 tests: 4 passed, 0 failed.
- Full unittest discovery: 30 passed, 0 failed.
- Catalog validator: passed.
- Safety guard: passed with no issues and no destructive override.
- GitHub PR validation: passed.

## 7. Live Smoke Results

Not done. This is an atlas-catalog static data change. No Atlas runtime service was changed or restarted.

## 8. Browser/UI Validation

Not applicable. RAN-395 does not change frontend files or direct user-visible UI behavior.

## 9. Deviations From PLAN.md

No implementation scope deviation. The plan anticipated a small validator change for `reranking`; that change was required and limited to `KNOWN_MODALITIES`.

Runtime profile values were not scored because no tuple-specific public throughput/latency sources were available during implementation. Those components carry `missing_reason: "published_runtime_profile_not_reported_for_tuple"`.

## 10. Open Questions / Follow-Ups

- Human catalog review should decide whether low-coverage backend-capability-only scores are sufficient for RAN-366's first pass or whether a future ticket should gather measured runtime profiles.
- RAN-366 should consume these records after merge and catalog refresh.

## 11. Acceptance Criteria Check

1. **Catalog contains backend_composite_scores for target models:** pass. 23 records across 16 target rows.
2. **Each score has source provenance per RAN-351 schema:** pass. Scored benchmark/backend components cite provenance; missing benchmark/runtime components carry `missing_reason`.
3. **Catalog validator passes:** pass. `catalog.json: catalog validation passed`.
4. **Safety guard passes:** pass. `allowed: true`, `issues: []`, `override_used: false`.
5. **RAN-366 reference dependency satisfied:** partial until merge. Data is present in PR #14; RAN-366 can consume it after the PR is merged and the catalog is refreshed.
6. **Draft PR; human catalog review before publish:** pass. Draft PR #14 is open for review.
