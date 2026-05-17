# RAN-350: Catalog rows for RAN-346 reranker options

## Linear Snapshot
- **Issue:** RAN-350
- **Title:** Catalog rows for RAN-346 reranker options
- **Status at ingest:** In Progress
- **Priority:** Medium
- **Project:** Atlas
- **Related:** RAN-346, RAN-341, RAN-338
- **URL:** https://linear.app/randhq/issue/RAN-350/catalog-rows-for-ran-346-reranker-options

## Scope
RAN-346 requires catalog-driven reranker options before merge. The
`Quiet-Node-io/atlas-catalog` repo needs four reranker entries:

1. BGE-Reranker-v2-m3 Q4_K_M from `gpustack/bge-reranker-v2-m3-GGUF`.
2. BGE-Reranker-v2-Gemma Q4_K_M from a verified public HuggingFace GGUF source.
3. BGE-Reranker-v2-Gemma Q8_0 from the same verified public source.
4. Small General Baseline virtual LLM-as-reranker row.

Cohere Rerank-v3 is explicitly out of scope.

## Acceptance Criteria
1. atlas-catalog has 4 reranker entries: BGE-Reranker-v2-m3, BGE-Reranker-v2-Gemma (Q4_K_M), BGE-Reranker-v2-Gemma (Q8_0), Small General Baseline (LLM-as-reranker).
2. Each entry includes:
   * Full display name + quantization metadata (RAN-341 naming compliance)
   * Backend identifier matching the RAN-335 RuntimeBackend Protocol (`llama_cpp_server` or `virtual`)
   * Verified upstream source URL (where applicable - virtual entry doesn't need one)
   * Verified file size + sha256 for downloadable GGUFs (RAN-347-style provenance)
   * Hardware recommendation metadata per RAN-338 capability tier
   * Modality field set to `reranking`
   * Category/model_type field set to `reranker`
   * If `benchmarks` field is included, follow RAN-347 option B schema (flat numeric/null + `benchmarks_meta` provenance sidecar)
3. Catalog validation passes (`python scripts/validate_catalog.py catalog.json`).
4. Catalog safety guard passes (`python scripts/catalog_discovery/safety.py`).
5. RAN-346 references RAN-350 as the atlas-catalog merge prerequisite.
6. Cohere Rerank-v3 is NOT in the catalog under this ticket.
7. Draft PR only; human catalog review (Ryan via Goose/Claude) before publish.

## Verified Source Notes
- `gpustack/bge-reranker-v2-m3-GGUF` is public and lists `bge-reranker-v2-m3-Q4_K_M.gguf`.
- `gpustack/bge-reranker-v2-gemma-GGUF` returned HTTP 401 during unauthenticated HF API and resolver checks.
- `mradermacher/bge-reranker-v2-gemma-GGUF` is public, Apache-2.0 tagged, and lists both `bge-reranker-v2-gemma.Q4_K_M.gguf` and `bge-reranker-v2-gemma.Q8_0.gguf`.
