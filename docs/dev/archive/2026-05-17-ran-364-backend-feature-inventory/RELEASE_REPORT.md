# RAN-364 RELEASE REPORT

## Shipped

RAN-364 shipped atlas-catalog backend feature inventory in PR #12:

- Added top-level `backends` collection with entries for `ollama`, `mlx_lm`, `llama_cpp_server`, `vllm`, `openai`, `anthropic`, `google`, and `xai`.
- Mirrored RAN-335 `BackendFeatureMatrix` field names in catalog data.
- Added per-feature provenance for backend flags.
- Added validator checks for malformed backend inventory, unknown model `backend_id` / `backend_ids`, and backend-aware composite score references.
- Documented maintainer workflow in `README.md`.

## Validation

Before merge, after rebasing on RAN-350 / PR #11:

- `python scripts/validate_catalog.py catalog.json` — pass.
- `python -m unittest tests.test_backend_inventory_schema` — 4 passed.
- `python -m unittest discover -s tests` — 25 passed.
- `python -m py_compile scripts/validate_catalog.py scripts/catalog_discovery/backend_inventory_schema.py scripts/catalog_discovery/backend_score_schema.py` — pass.
- GitHub Catalog validation CI — pass.

## PR

- PR: https://github.com/Quiet-Node-io/atlas-catalog/pull/12
- Merge commit: `8ec416ebf073b2e6964249e721b2403e23f7fdea`
- Merge method: squash merge.

## Risks / Follow-Ups

- MLX-LM and vLLM backend flags are forward-declared from upstream documentation and should be revisited when Atlas runtime adapters land.
- Backend-aware composite score population for top models is not part of this PR. RAN-366 needs that data later; file a separate atlas-catalog ticket when RAN-366 is ready to fire.
- Atlas runtime still ignores `backends` until a future consumer ticket reads the collection.
