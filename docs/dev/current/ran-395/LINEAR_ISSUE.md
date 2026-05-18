# RAN-395: Atlas-catalog: populate backend_composite_scores for top ~15 models (unblocks RAN-366 Terry onboarding)

- **Linear:** https://linear.app/randhq/issue/RAN-395/atlas-catalog-populate-backend-composite-scores-for-top-15-models
- **Status at ingest:** In Progress
- **Repository:** `Quiet-Node-io/atlas-catalog`
- **Branch:** `codex/ran-395-backend-composite-scores`

## Frozen Scope

RAN-395 fills the data gap left after RAN-351 shipped the `backend_composite_scores` schema and RAN-364 shipped the `backends` collection. RAN-366 Terry onboarding requires recommendations sourced from `backend_composite_scores` keyed by `(model, backend, hardware-tier, quant)`.

Add `backend_composite_scores` rows in `catalog.json` for the target priority models:

### Local Apple Silicon family

- Gemma 4 4.5B (`Q4_K_M`, `Q8_0`, `BF16`) with Ollama and MLX-LM scoring.
- Gemma 4 31B (`Q4_K_M`, `Q8_0`) with Ollama and MLX-LM scoring.
- BGE-M3 embedding with Ollama scoring only.
- BGE-Reranker-v2-m3 `Q4_K_M` with llama.cpp-server scoring only.
- BGE-Reranker-v2-Gemma (`Q4_K_M`, `Q8_0`) with llama.cpp-server scoring.

### Local NVIDIA family

- DeepSeek R1 70B `Q4_K_M` with Ollama and vLLM scoring.
- Qwen 2.5 Coder 32B `Q4_K_M` with Ollama and vLLM scoring.

### Vision

- Llama 3.2 Vision 11B `Q4_K_M` with Ollama scoring.

### Cloud

- `gpt-5.4-mini` with OpenAI scoring.
- `claude-haiku-4-5-20251001` with Anthropic scoring.
- `gemini-2.5-flash-lite` with Google scoring.
- `grok-4-1-fast-non-reasoning` with xAI scoring.

## Score Components

For each applicable `(model x backend x hardware-tier x quant)` tuple:

1. `benchmark_composite` from RAN-347 benchmark data already in the catalog where present (`MMLU`, `GPQA`, `HumanEval`, `MATH` where present).
2. `backend_capability` from the RAN-364 `backends` collection.
3. `runtime_profile` best-effort from published throughput/latency data.
4. Final `score` as a 0-100 integer plus `coverage` as a 0-1 float.
5. Source provenance for each component.

Missing data must be represented as `null`/missing component score plus `missing_reason`. No invented scores.

## Sources To Consult

- HuggingFace leaderboards for benchmark data.
- Provider published throughput/latency pages for Anthropic, OpenAI, Google, and xAI.
- Apple Silicon community benchmarks for MLX-LM tokens/sec.
- Ollama community benchmarks.
- llama.cpp benchmarks for reranker tokens/sec.
- Existing RAN-364 backend inventory provenance in `catalog.json`.

## Acceptance Criteria

1. atlas-catalog `catalog.json` contains `backend_composite_scores` for the 15+ models above across applicable (backend x hardware x quant) tuples.
2. Each score has source provenance per RAN-351 schema.
3. Catalog validator passes with new score data.
4. Safety guard passes.
5. RAN-366 reference dependency satisfied; Terry onboarding can now consume scores.
6. Draft PR; human catalog review before publish.

## Out Of Scope

- Live measured scores from Atlas's actual runtime.
- vLLM scores from actual NVIDIA validation hardware.
- Cross-model qualitative ranking; Terry onboarding handles ranking logic.

