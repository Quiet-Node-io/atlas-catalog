# RAN-350 VALIDATION

## Validation Summary
- **Catalog JSON syntax:** pass
- **Catalog validator:** pass
- **Catalog safety guard:** pass
- **Targeted semantic assertions:** pass
- **Browser/UI validation:** not applicable; catalog data only
- **Live Atlas smoke:** not applicable; catalog data only
- **Draft PR:** https://github.com/Quiet-Node-io/atlas-catalog/pull/11

## Evidence

### JSON Syntax
Command:
```bash
python -m json.tool catalog.json >/dev/null
```
Result: exit 0.

### Catalog Validator
Command:
```bash
python scripts/validate_catalog.py catalog.json
```
Result: exit 0.
Output:
```text
catalog.json: catalog validation passed
```

### Catalog Safety Guard
Command:
```bash
python scripts/catalog_discovery/safety.py --base <(git show main:catalog.json) --proposed catalog.json
```
Result: exit 0.
Output:
```json
{
  "allowed": true,
  "issues": [],
  "override_used": false
}
```

### Targeted RAN-350 Assertions
Command:
```bash
python - <<'PY'
# Assert four RAN-350 rows, backend/modality/category/model_type values,
# verified byte sizes and sha256 hashes, hardware tiers, discovery evidence,
# catalog updated date, and Cohere exclusion.
PY
```
Result: exit 0.
Output:
```text
RAN-350 semantic catalog assertions passed
```

## Source Verification Evidence
- `gpustack/bge-reranker-v2-m3-GGUF` HF API listed `bge-reranker-v2-m3-Q4_K_M.gguf`.
- `bge-reranker-v2-m3-Q4_K_M.gguf` resolver headers: size `438376864`, sha256 `e186a244ed455b4ab66ec64339ce7427a6ae13f5c0b5e544de96e50f0f8b3673`.
- `gpustack/bge-reranker-v2-gemma-GGUF` returned HTTP 401 and was not used.
- `mradermacher/bge-reranker-v2-gemma-GGUF` HF API listed `bge-reranker-v2-gemma.Q4_K_M.gguf` and `bge-reranker-v2-gemma.Q8_0.gguf`.
- `bge-reranker-v2-gemma.Q4_K_M.gguf` resolver headers: size `1630263328`, sha256 `b1735f899bd1e238aa90d27ce24a58680d67ba037ff66ee70fe441050b38c257`.
- `bge-reranker-v2-gemma.Q8_0.gguf` resolver headers: size `2669070368`, sha256 `e40e4f2269ec2271c2cf7512f85de7cd7a16ca3e8f689fe2b945cc98fe28b44b`.

## Acceptance Criteria
1. **Pass** - Four reranker entries exist.
2. **Pass** - Required metadata is present on all rows; virtual row has no download URL, no HF file, and zero file size.
3. **Pass** - Catalog validation passed.
4. **Pass** - Catalog safety guard passed.
5. **Pass** - RAN-346 Linear relation includes RAN-350.
6. **Pass** - Cohere Rerank-v3 was not added.
7. **Pass** - Draft PR opened for human catalog review: https://github.com/Quiet-Node-io/atlas-catalog/pull/11
