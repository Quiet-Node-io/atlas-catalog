# RAN-350 CODEX_REPORT

## 1. Linear Issue
- **ID:** RAN-350
- **Title:** Catalog rows for RAN-346 reranker options

## 2. Branch and Commit Range
- **Branch:** `codex/ran-350-reranker-catalog`
- **Commit range:** `main..codex/ran-350-reranker-catalog`

## 3. Files Changed
- `catalog.json` - Added four RAN-350 reranker entries and updated the catalog date.
- `docs/dev/current/ran-350/LINEAR_ISSUE.md` - Captured the Linear scope and acceptance criteria.
- `docs/dev/current/ran-350/PLAN.md` - Documented implementation approach, file scope, risks, and validation.
- `docs/dev/current/ran-350/CODEX_REPORT.md` - Implementation report.
- `docs/dev/current/ran-350/VALIDATION.md` - Validation evidence and acceptance check.

## 4. Summary of Changes
- Added default `BGE-Reranker-v2-m3 Q4_K_M` from `gpustack/bge-reranker-v2-m3-GGUF`.
- Added `BGE-Reranker-v2-Gemma Q4_K_M` and `BGE-Reranker-v2-Gemma Q8_0` from `mradermacher/bge-reranker-v2-gemma-GGUF`.
- Added virtual `Small General Baseline (LLM-as-reranker)` as `atlas/llm-as-reranker:small-general`.
- Set all four rows to `category: reranker`, `model_type: reranker`, `modality: reranking`, and `modalities: ["reranking"]`.
- Added `backend` and `runtime_backend` as `llama_cpp_server` for GGUF rows and `virtual` for the Small General baseline.
- Added hardware-tier recommendations, quantization metadata, provenance fields, and `discovery_evidence.sources` for safety guard compatibility.

## 5. Commands Run
- `curl -fsSL https://huggingface.co/api/models/gpustack/bge-reranker-v2-m3-GGUF` - exit 0; HF API listed `bge-reranker-v2-m3-Q4_K_M.gguf`.
- `curl -fsSI -L https://huggingface.co/gpustack/bge-reranker-v2-m3-GGUF/resolve/main/bge-reranker-v2-m3-Q4_K_M.gguf` - exit 0; headers showed `x-linked-size: 438376864` and `x-linked-etag: "e186a244ed455b4ab66ec64339ce7427a6ae13f5c0b5e544de96e50f0f8b3673"`.
- `curl -fsSL https://huggingface.co/api/models/gpustack/bge-reranker-v2-gemma-GGUF` - exit 56; HF returned HTTP 401, so this source was not used.
- `curl -fsSL 'https://huggingface.co/api/models?search=bge-reranker-v2-gemma-GGUF&limit=20'` - exit 0; found public alternatives.
- `curl -fsSL https://huggingface.co/api/models/mradermacher/bge-reranker-v2-gemma-GGUF` - exit 0; HF API listed both `bge-reranker-v2-gemma.Q4_K_M.gguf` and `bge-reranker-v2-gemma.Q8_0.gguf`.
- `curl -fsSI -L https://huggingface.co/mradermacher/bge-reranker-v2-gemma-GGUF/resolve/main/bge-reranker-v2-gemma.Q4_K_M.gguf` - exit 0; headers showed `x-linked-size: 1630263328` and `x-linked-etag: "b1735f899bd1e238aa90d27ce24a58680d67ba037ff66ee70fe441050b38c257"`.
- `curl -fsSI -L https://huggingface.co/mradermacher/bge-reranker-v2-gemma-GGUF/resolve/main/bge-reranker-v2-gemma.Q8_0.gguf` - exit 0; headers showed `x-linked-size: 2669070368` and `x-linked-etag: "e40e4f2269ec2271c2cf7512f85de7cd7a16ca3e8f689fe2b945cc98fe28b44b"`.
- `python -m json.tool catalog.json >/dev/null` - exit 0.
- `python scripts/validate_catalog.py catalog.json` - exit 0; output: `catalog.json: catalog validation passed`.
- `python scripts/catalog_discovery/safety.py --base <(git show main:catalog.json) --proposed catalog.json` - exit 0; output: `{ "allowed": true, "issues": [], "override_used": false }`.
- Targeted RAN-350 semantic assertion script - exit 0; output: `RAN-350 semantic catalog assertions passed`.

## 6. Test Results
- Catalog JSON syntax: passed.
- Catalog validator: passed.
- Discovery safety guard: passed.
- Targeted semantic assertions: passed.

## 7. Live Smoke Results
- Not applicable. atlas-catalog is a data repository; no Atlas runtime smoke was required for this catalog-only PR.

## 8. Browser/UI Validation
- Not applicable. No frontend files or user-visible UI code changed in this repository.

## 9. Deviations from PLAN.md
- None after the plan was written.
- Deviation from the issue's likely Gemma source/filename suggestion: `gpustack/bge-reranker-v2-gemma-GGUF` returned HTTP 401. The selected public fallback is `mradermacher/bge-reranker-v2-gemma-GGUF`, whose exact upstream filenames are dot-separated: `bge-reranker-v2-gemma.Q4_K_M.gguf` and `bge-reranker-v2-gemma.Q8_0.gguf`.

## 10. Open Questions / Follow-Ups
- Human catalog review should confirm the fallback Gemma source and dot-separated filenames are acceptable for RAN-346.
- RAN-346 implementation should confirm which of `backend` or `runtime_backend` it consumes; both are present in these rows.

## 11. Acceptance Criteria Check
1. **Pass** - Four reranker entries exist.
2. **Pass** - Each row includes display/quantization metadata, backend, source/provenance where applicable, hardware tiers, reranking modality, and reranker category/model_type. `benchmarks` is empty, so no benchmark provenance sidecar is required.
3. **Pass** - `python scripts/validate_catalog.py catalog.json` passed.
4. **Pass** - Safety guard passed with explicit base/proposed arguments.
5. **Pass** - RAN-346 Linear relations include RAN-350 as related work.
6. **Pass** - Targeted assertion confirmed no Cohere rerank catalog row was added.
7. **Pending until PR creation** - Draft PR will be opened for human catalog review.
