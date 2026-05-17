# RAN-364: Model System v2 §2.6: Backend feature inventory in atlas-catalog

- **Linear:** https://linear.app/randhq/issue/RAN-364/model-system-v2-26-backend-feature-inventory-in-atlas-catalog
- **Status at ingest:** Backlog
- **Status after ingest:** In Progress
- **Parent:** RAN-190
- **Repository:** Quiet-Node-io/atlas-catalog

## Scope

Implementation in atlas-catalog repo. Add a top-level `backends` collection alongside the existing `models` collection.

Entries required:

- `ollama`
- `mlx_lm`
- `llama_cpp_server`
- `vllm`
- `openai`
- `anthropic`
- `google`
- `xai`

Each entry must include `backend_id`, `version_range`, full `features` matrix matching RAN-335 `BackendFeatureMatrix`, `notes`, and optionally `provenance`.

Catalog validator must check that:

- Each backend entry is well-formed.
- Models that declare a backend reference an existing `backend_id`.
- Feature flags use a known schema extending or coexisting with RAN-335 `BackendFeatureMatrix`.

## Acceptance Criteria

1. atlas-catalog `catalog.json` contains a `backends` collection with entries for: `ollama`, `mlx_lm`, `llama_cpp_server`, `vllm`, `openai`, `anthropic`, `google`, `xai`
2. Each entry includes: `backend_id`, `version_range`, full `features` matrix matching RAN-335 `BackendFeatureMatrix` fields, `notes`, and optionally `provenance` (citing where each feature flag was verified)
3. Catalog validator rejects malformed backend entries
4. Catalog validator rejects models referencing unknown `backend_id`
5. README documents the new collection and how to add a new backend
6. Atlas runtime continues to consume the catalog unchanged (the new `backends` collection is additive; runtime ignores it until a future ticket reads it)
7. Draft PR; human catalog review before publish

## Out Of Scope

- Atlas application-code changes to consume the new `backends` collection.
- Live backend probing at catalog publish time.
- Per-model-per-backend feature override.

## Notes

The requested Atlas path `docs/dev/current/ran-190-v2/EPIC_ARCHITECTURE.md` was not present in the main Atlas checkout. I searched `docs/`, `knowledge/`, and `src/` for the cited section and used the Linear RAN-364 issue body plus the RAN-335/RAN-336/RAN-345/RAN-352 source files as the frozen scope.
