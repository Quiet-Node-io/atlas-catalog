# RAN-350: Catalog rows for RAN-346 reranker options

## Context Assembly
- **Files to read (mandatory):** `README.md`, `catalog.json`, `scripts/validate_catalog.py`, `scripts/catalog_discovery/safety.py`, `scripts/catalog_discovery/backend_score_schema.py`, `docs/dev/current/ran-350/LINEAR_ISSUE.md`.
- **Systems impacted:** Atlas model catalog data, catalog discovery safety guard, RAN-346 reranker picker inputs.
- **Known constraints:** Added catalog rows must have discovery evidence for safety guard approval; downloadable model claims must be verified against upstream HuggingFace before publishing; Cohere is out of scope; no infrastructure access details belong in docs.
- **Assumptions:** RAN-350's "plan + impl in one pass" instruction authorizes this straightforward catalog data change without a separate Goose/Claude plan approval pause. The Gemma filename may differ from the issue suggestion if the chosen verified upstream repo uses a different exact filename.

## Approach
- Add four catalog rows to `catalog.json` with category/model_type `reranker`, reranking-only modality, RuntimeBackend identifiers, hardware-tier metadata, and discovery evidence.
- Use `gpustack/bge-reranker-v2-m3-GGUF` for the default m3 row because the HF API and resolver headers verify the requested file and the RAN-358 hash.
- Use `mradermacher/bge-reranker-v2-gemma-GGUF` for both Gemma variants because the expected gpustack Gemma repo returned HTTP 401, while this public repo lists both requested quantizations in one Apache-2.0 tagged source.
- Use a virtual `atlas/llm-as-reranker:small-general` row for the Small General fallback with no download URL, no GGUF file, and zero extra RAM.

## Execution Contract
- **Files allowed to edit:** `catalog.json`, `docs/dev/current/ran-350/LINEAR_ISSUE.md`, `docs/dev/current/ran-350/PLAN.md`, `docs/dev/current/ran-350/CODEX_REPORT.md`, `docs/dev/current/ran-350/VALIDATION.md`.
- **Files explicitly forbidden:** Application code, discovery worker code, existing unrelated untracked files, Atlas main repo files, GitHub workflow files.
- **Acceptance criteria:** Copied in `docs/dev/current/ran-350/LINEAR_ISSUE.md`.
- **Required validation commands:**
  - `python -m json.tool catalog.json >/dev/null`
  - `python scripts/validate_catalog.py catalog.json`
  - `python scripts/catalog_discovery/safety.py --base <(git show main:catalog.json) --proposed catalog.json`
  - Targeted catalog assertions for row count, Cohere exclusion, backend/modality/category/model_type, file sizes, sha256 values, and hardware tiers.
- **Verification targets:** Four new reranker rows exist; three downloadable rows carry verified HuggingFace URLs, byte sizes, and sha256 values; virtual row carries no source/download/GGUF file; Cohere rerank is absent.
- **Definition of done:** All validation commands exit 0, report files list exact evidence and changed files, RAN-350 receives an implementation comment, and a draft PR is opened for human catalog review.

## Architecture
- The catalog remains a single JSON payload consumed by Atlas.
- The new rows are additive and do not alter existing model rows except the top-level `updated` date.
- Runtime integration uses explicit `backend` and `runtime_backend` values: `llama_cpp_server` for GGUF rerankers and `virtual` for the Small General baseline.
- Do not add benchmark scores without cited public benchmark provenance.

## Risk & Mitigation
- **Wrong upstream file claim:** Use HF API plus resolver headers and record exact evidence.
- **Safety guard blocks added rows:** Include `discovery_evidence.sources` on every added row.
- **Gemma source mismatch:** Document the gpustack 401 and chosen public fallback source in CODEX_REPORT.md.
- **Atlas consumer expects specific fields:** Include both conservative existing fields (`hf_repo`, `hf_filename`, `variant_group`, `quantization`) and explicit RAN-346 fields (`backend`, `runtime_backend`, `modality`, `modalities`, hardware tiers).

## Test Strategy
- Run JSON syntax validation.
- Run the catalog validator.
- Run safety guard against `main:catalog.json`.
- Run targeted semantic assertions over the four new rows.
- No browser/UI validation is required because this repo change is catalog data only.

## UI/UX Surface
- Not applicable. This ticket edits catalog data only and does not modify frontend files or introduce direct user interactions in this repository.

## Predicted Next 3 Failures
1. Safety guard rejects new rows if any lacks `discovery_evidence.sources`.
2. Reviewer asks whether Gemma dot-separated filenames are acceptable versus the issue's suggested hyphenated filenames.
3. Atlas-side RAN-346 consumer may need to confirm whether it reads `backend`, `runtime_backend`, or both.

## Rollback Plan
- Revert the additive `catalog.json` rows and restore the previous top-level `updated` date.
- Remove RAN-350 report files if Ryan asks to abandon the branch before merge.
