# RAN-350 RELEASE_REPORT

## What Shipped
- Merged atlas-catalog PR #11: https://github.com/Quiet-Node-io/atlas-catalog/pull/11
- Squash merge commit: `cdc72f75d479ff03976a5aa75896d12c585b3c3a`
- Added four RAN-350 reranker catalog rows for RAN-346:
  - `gpustack/bge-reranker-v2-m3-GGUF:q4_k_m`
  - `mradermacher/bge-reranker-v2-gemma-GGUF:q4_k_m`
  - `mradermacher/bge-reranker-v2-gemma-GGUF:q8_0`
  - `atlas/llm-as-reranker:small-general`
- Cohere Rerank-v3 remains out of scope and was not added.

## Validation
- `python -m json.tool catalog.json >/dev/null` passed before merge.
- `python scripts/validate_catalog.py catalog.json` passed before merge.
- `python scripts/catalog_discovery/safety.py --base <(git show main:catalog.json) --proposed catalog.json` passed before merge.
- Targeted RAN-350 semantic catalog assertions passed before merge.
- PR #11 was merged and local `main` was fast-forwarded to `cdc72f75d479ff03976a5aa75896d12c585b3c3a`.

## Notes
- GitHub rejected `gh pr review --approve` because the authenticated token owned the PR. Ryan's approval was provided explicitly in the closeout prompt, then the PR was marked ready and squash-merged.
- `gpustack/bge-reranker-v2-gemma-GGUF` returned HTTP 401. The merged Gemma rows use verified public fallback `mradermacher/bge-reranker-v2-gemma-GGUF`.

## Follow-Ups
- RAN-346 can treat the catalog dependency as satisfied and rebase/pull the merged catalog if needed.
- RAN-364 should rebase or refresh against the landed catalog rows if it depends on reranker catalog state.
