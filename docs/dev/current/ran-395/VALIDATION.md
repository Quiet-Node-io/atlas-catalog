# RAN-395 VALIDATION

## Validation Summary

Local validation is green for the implemented catalog data change. GitHub PR validation is also green.

## Commands And Evidence

### Focused RAN-395 Test

Command:

```bash
python -m unittest tests.test_ran395_backend_composite_scores
```

Result:

```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.005s

OK
```

### Catalog Validator

Command:

```bash
python scripts/validate_catalog.py catalog.json
```

Result:

```text
catalog.json: catalog validation passed
```

### Safety Guard

Command:

```bash
git show origin/main:catalog.json > /tmp/ran395-base-catalog.json && python scripts/catalog_discovery/safety.py --base /tmp/ran395-base-catalog.json --proposed catalog.json
```

Result:

```json
{
  "allowed": true,
  "deduped": [],
  "issues": [],
  "override_used": false
}
```

### Full Unittest Discovery

Command:

```bash
python -m unittest discover -s tests
```

Result:

```text
..............................
----------------------------------------------------------------------
Ran 30 tests in 0.014s

OK
```

### Whitespace Check

Command:

```bash
git diff --check
```

Result: exit 0, no output.

### Draft PR Check

Command:

```bash
gh pr checks 14
```

First result:

```text
validate	pending	0	https://github.com/Quiet-Node-io/atlas-catalog/actions/runs/26001643826/job/76425825123
```

Final command:

```bash
gh pr checks 14 --watch
```

Final result:

```text
validate	pass	9s	https://github.com/Quiet-Node-io/atlas-catalog/actions/runs/26001643826/job/76425825123
validate	pass	9s	https://github.com/Quiet-Node-io/atlas-catalog/actions/runs/26001643826/job/76425825123
```

## Score Coverage

- Apple Silicon local rows: Gemma 4 4.5B and 31B variants have Ollama and MLX-LM score records for requested quantizations.
- Embedding/reranker rows: BGE-M3 and both BGE reranker families have Ollama or llama.cpp-server records as scoped.
- NVIDIA-forward rows: DeepSeek R1 70B and Qwen 2.5 Coder 32B have Ollama and vLLM records.
- Vision row: Llama 3.2 Vision 11B has an Ollama record with benchmark and backend coverage.
- Cloud rows: GPT-5.4 Mini, Claude Haiku 4.5, Gemini 2.5 Flash-Lite, and Grok 4.1 Fast have provider backend records.

## Acceptance Criteria

1. `backend_composite_scores` for target tuples: pass.
2. Source provenance or missing reason per component: pass.
3. Catalog validator passes: pass.
4. Safety guard passes: pass.
5. RAN-366 dependency satisfied: partial until PR merge; data exists in draft PR #14.
6. Draft PR for human catalog review: pass.

## Not Done

- RAN-395 is not moved to Done and RAN-366 is not commented yet; those are post-merge closeout steps per the handoff.
