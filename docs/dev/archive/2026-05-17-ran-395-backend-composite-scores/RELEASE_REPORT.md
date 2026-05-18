# RAN-395 RELEASE REPORT

## What Shipped

RAN-395 shipped atlas-catalog backend-aware composite score population in PR #14:

- PR: https://github.com/Quiet-Node-io/atlas-catalog/pull/14
- Squash merge commit: `6049aa410caf84a3fd9bd72f05fb2549a801affb`
- Archive commit: `1d96e30`

The catalog now includes 23 `backend_composite_scores` records across 16 priority model rows:

- Gemma 4 4.5B variants for Ollama and MLX-LM.
- Gemma 4 31B Q4/Q8 variants for Ollama and MLX-LM.
- BGE-M3 embedding for Ollama.
- BGE-Reranker-v2-m3 and BGE-Reranker-v2-Gemma variants for llama.cpp-server.
- DeepSeek R1 70B and Qwen 2.5 Coder 32B for Ollama and vLLM.
- Llama 3.2 Vision 11B for Ollama.
- GPT-5.4 Mini, Claude Haiku 4.5, Gemini 2.5 Flash-Lite, and Grok 4.1 Fast for their cloud provider backends.

## Validation

- Focused RAN-395 tests: 4 passed.
- Full unittest discovery: 30 passed.
- Catalog validator: passed.
- Safety guard: passed with no issues.
- GitHub `validate` check: passed.

## Risks And Caveats

Many tuples have low coverage (`0.25`) because only backend capability is currently sourced. This is intentional and approved: benchmark/runtime data is not invented, and missing benchmark/runtime components carry `missing_reason`.

Llama 3.2 Vision has higher coverage (`0.85`) because existing catalog benchmark values are present and now have provenance metadata.

## Follow-Ups

- RAN-366 can consume `backend_composite_scores` for Terry onboarding.
- Future work should ratchet score coverage upward after real Mac Studio cluster and DGX Spark measurements are available.

