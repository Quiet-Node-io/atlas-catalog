# RAN-364 VALIDATION

## Validation Commands

```bash
python scripts/validate_catalog.py catalog.json
```

Exit 0:

```text
catalog.json: catalog validation passed
```

```bash
python -m unittest tests.test_backend_inventory_schema
```

Exit 0:

```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.002s

OK
```

```bash
python -m unittest discover -s tests
```

Exit 0:

```text
.........................
----------------------------------------------------------------------
Ran 25 tests in 0.014s

OK
```

```bash
python -m py_compile scripts/validate_catalog.py scripts/catalog_discovery/backend_inventory_schema.py scripts/catalog_discovery/backend_score_schema.py
```

Exit 0, no output.

## Live Smoke

Not applicable. This is a static atlas-catalog schema/validator/docs change. Current Atlas runtime readers ignore the new top-level `backends` collection.

## Browser/UI Validation

Not applicable. No browser, frontend, or UI-facing runtime behavior changed.

## Acceptance Criteria

1. `catalog.json` contains a `backends` collection with `ollama`, `mlx_lm`, `llama_cpp_server`, `vllm`, `openai`, `anthropic`, `google`, `xai` — pass.
2. Each entry includes `backend_id`, `version_range`, full RAN-335 feature matrix, `notes`, and provenance — pass.
3. Validator rejects malformed backend entries — pass, covered by `test_rejects_malformed_backend_entries`.
4. Validator rejects models referencing unknown `backend_id` — pass, covered by `test_rejects_model_backend_reference_when_backend_id_is_unknown`.
5. README documents the new collection and how to add a backend — pass.
6. Atlas runtime continues unchanged — pass, no Atlas runtime code changed; `backends` is additive.
7. Draft PR; human catalog review before publish — pending after final commit/push/PR.

## Required Review

Human catalog review should pay special attention to MLX-LM and vLLM feature declarations, since these are forward-declared from upstream/community documentation rather than current Atlas adapters.
