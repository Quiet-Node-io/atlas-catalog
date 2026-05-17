# Atlas Model Catalog

Curated model catalog for Atlas AI instances. This file is fetched by Atlas on startup to check for new models, updated recommendations, and superseded defaults.

## Usage

Atlas instances fetch `catalog.json` from the raw GitHub URL:

```
https://raw.githubusercontent.com/Quiet-Node-io/atlas-catalog/main/catalog.json
```

The catalog is checked periodically. When a new model is added or a default is changed, Atlas surfaces the update in the Local AI Models dashboard.

## Catalog Format

```jsonc
{
  "catalog_version": 5,        // Bump when schema changes
  "updated": "2026-05-17",     // Last edit date
  "backends": [                // Backend feature inventory — additive, ignored by current Atlas runtime
    {
      "backend_id": "vllm",
      "version_range": ">=0.11.0",
      "features": {
        "supports_streaming": true,
        "supports_non_streaming": true,
        "supports_embeddings": true,
        "supports_vision": true,
        "supports_json_mode": true,
        "supports_function_calling": true,
        "supports_continuous_batching": true,
        "max_batch_size": null,
        "supports_kv_cache_control": true,
        "supported_sampling_params": ["temperature", "top_p", "top_k", "repeat_penalty", "max_tokens", "stop", "seed"],
        "supports_unload": true,
        "supports_model_survey": true,
        "auth_mode": "api_key",
        "supports_leases": false
      },
      "notes": "Human-readable scope and caveats.",
      "provenance": {
        "sources": {
          "vllm_openai_server": {
            "source_kind": "upstream_docs",
            "source_url": "https://docs.vllm.ai/en/latest/serving/openai_compatible_server/",
            "retrieved_at": "2026-05-17T00:00:00+00:00"
          }
        },
        "feature_flags": {
          "supports_streaming": ["vllm_openai_server"]
          // ... one entry for every feature flag
        }
      }
    }
  ],
  "task_benchmark_weights": {  // Per-task benchmark portfolios — drives Atlas score composite (RAN-192)
    "vision_input": {
      "mmmu": 0.35, "ai2d": 0.20, "chartqa": 0.20,
      "docvqa": 0.15, "mathvista": 0.10
    },
    "code_generation": {
      "swe_bench_verified": 0.35, "livecodebench": 0.25,
      "bigcodebench": 0.20, "humaneval": 0.20
    }
    // ... one entry per task; each task's weights MUST sum to 1.0
  },
  "models": [
    {
      "id": "gemma4:31b",      // Ollama tag or HuggingFace model ID
      "name": "Gemma 4 31B",
      "description": "...",
      "category": "general",   // general, coding, reasoning, vision, image_gen
      "parameters": "31B",
      "ram": "20-24 GB",
      "capabilities": {        // 1-5 ratings
        "write": 5, "code": 4, "reason": 5,
        "chat": 5, "speed": 3, "vision": 4
      },
      "unrestricted": false,   // True = uncensored model
      "variant": "standard",   // standard or unrestricted content-safety variant
      "atlas_pick": true,      // Recommended by Atlas
      "default": true,         // Default model for new installs
      "registry": "ollama",    // ollama, huggingface, civitai, or cloud
      "benchmarks": {          // Raw 0-1 benchmark scores (RAN-192). Atlas computes per-task display score from these.
        "mmmu": 0.78,          //   Use null/omit when you do not have a cited public source — never invent.
        "humaneval": 0.92      //   Field names match keys in `task_benchmark_weights`.
      },
      "task_fitness": {        // Legacy per-task picker score 0-100. Computed score from benchmarks supersedes when coverage exists.
        "general_chat": 95,
        "vision_input": 90
      },
      "task_stance": {         // Per-model-per-task "Pick this when..." text. MUST be authored per row — no copy-paste.
        "general_chat": "Pick this when ...",
        "vision_input": "Pick this when ..."
      },
      "superseded_by": null,   // Model ID that replaces this one
      "update_policy": "optional" // optional, recommended, required
    }
  ]
}
```

### `benchmarks` field (RAN-192)

Each model row carries a `benchmarks` object with raw 0-1 scores:

- Field names are stable identifiers (e.g. `mmmu`, `swe_bench_verified`,
  `humaneval`, `gpqa_diamond`, `lmarena_normalized`, `mt_bench`,
  `ifeval`, `bfcl`, `mmlu_pro`, `flores_200`, etc.).
- Values are numeric in `[0, 1]`. Source benchmarks reported on a
  0-100 scale are divided by 100 before being recorded here. ELO and
  latency metrics are min-max normalized into 0-1; record those under
  the `_normalized` suffixed name (e.g. `lmarena_normalized`,
  `speed_score`).
- `null` or omitted means "no cited value" — the score aggregator is
  null-aware and renormalizes on the present weights.
- **Never invent a score.** If you cannot cite an official model card,
  vendor announcement, or reputable public leaderboard, omit the field.

See `knowledge/system/model-scoring-methodology.md` in the Atlas repo
for the full source-hierarchy and update-cadence rules.

### `task_benchmark_weights` (RAN-192)

Top-level `task_benchmark_weights` defines per-task benchmark portfolios.
Each task entry maps benchmark names to weights summing to `1.0`. Atlas
multiplies each model's `benchmarks` value by the task's weight, sums
present weights only (null-aware), then rounds to a 0-100 display score.
Update weights here — not in the Atlas codebase — when methodology shifts.

### `backends` collection (RAN-364)

Top-level `backends` publishes backend capability facts separately from model
rows. The collection is additive: current Atlas runtime consumers ignore it
until a future coordinated Atlas ticket reads these records.

Each backend entry must include:

- `backend_id`: stable ID used by model rows and backend-aware score records.
- `version_range`: upstream version, provider API marker, or Atlas adapter
  scope that the feature declaration applies to.
- `features`: the complete RAN-335 `BackendFeatureMatrix` shape:
  `supports_streaming`, `supports_non_streaming`, `supports_embeddings`,
  `supports_vision`, `supports_json_mode`, `supports_function_calling`,
  `supports_continuous_batching`, `max_batch_size`,
  `supports_kv_cache_control`, `supported_sampling_params`,
  `supports_unload`, `supports_model_survey`, `auth_mode`, and
  `supports_leases`.
- `notes`: human-readable maintainer notes and caveats.
- `provenance`: required for feature flags in this catalog. Use
  `sources` for cited documents and `feature_flags` to map every feature
  field to one or more source IDs.

Known sampling params are `temperature`, `top_p`, `top_k`,
`repeat_penalty`, `max_tokens`, `stop`, and `seed`. Known auth modes are
`none`, `backend_native`, `api_key`, `proxy_token`, and `mtls`.

When adding a backend:

1. Add a new `backends[]` entry with a unique `backend_id`.
2. Fill every `features` key, using `null` for `max_batch_size` only when the
   backend has no single static limit.
3. Cite public upstream/provider docs or Atlas source for every feature flag.
4. If model rows or `backend_composite_scores` reference the backend, use the
   same `backend_id`.
5. Run `python scripts/validate_catalog.py catalog.json`.

The validator rejects malformed backend entries, unknown feature fields,
unknown sampling params/auth modes, missing per-feature provenance, duplicate
backend IDs, model rows whose `backend_id` or `backend_ids` reference unknown
backends, and backend-aware composite score records whose `backend` is not in
the top-level backend inventory.

### `task_stance` authoring rules (RAN-192)

- One `task_stance` string per `(model_id, task_id)` pair.
- No copy-paste across rows. CI rejects identical placeholder strings.
- Lead with the task-specific reason a user picks THIS row over its
  neighbours: frontier benchmark gap, free-local cost trade, deprecated
  pointer to the replacement row, or specialty niche.

### Ollama structured variant fields (RAN-186)

Every row with `"registry": "ollama"` must use structured variant metadata:

- `name` and `display_name`: user-facing base name, without a trailing
  quantization token.
- `variant_label`: size or variant phrase such as `31B`, `4.5B`, or `567M`.
- `quantization`: explicit quant marker such as `Q4_K_M`, `Q8_0`, `BF16`, or
  `F16`.
- `family`, `publisher`, and `provider`: populated display metadata.
- `variant_group`: populated on every Ollama row. Swappable siblings share a
  group id; singleton rows use their own `id`.
- `ollama_pull_tag`: set only when the Atlas catalog id differs from the real
  Ollama registry tag. Omit it when `id` is the pullable tag.
- `aliases`: optional list of legacy catalog/provider identifiers that now
  resolve to this row. Use it for dedupes, not for adding separate duplicate
  rows.

Run `python scripts/validate_catalog.py catalog.json` before opening catalog
PRs. The GitHub workflow runs the same validator on catalog changes.

### Content-safety variant field (RAN-337)

Every model row must include `variant` with one of:

- `standard`: default safety-aligned model row.
- `unrestricted`: unrestricted model row. Rows with this value must also set
  `unrestricted: true`.

For system-slot alternatives, `variant_group` continues to group swappable
siblings by family/size, `quantization` continues to identify Q4/Q8/BF16, and
`variant` identifies the content-safety family used by Atlas's unrestricted
system-variant picker.

## Maintainer-side discovery worker

RAN-339 adds a maintainer-only discovery worker. The worker runs in this repo,
not inside Atlas runtime, so Atlas instances continue to read only the
published `catalog.json`.

Manual dry run:

```bash
python scripts/run_catalog_discovery.py \
  --catalog catalog.json \
  --offline-fixtures tests/fixtures \
  --output .atlas-review/test-run \
  --no-pr
```

Scheduled runs live in `.github/workflows/catalog-discovery.yml`. The workflow
queries configured provider/model registry sources, writes bounded review
artifacts under `.atlas-review/runs/<run-id>/`, and opens a draft PR for human
review. Draft PRs are the only automated publish path; maintainers must review
and merge catalog changes manually.

The worker stores review state in `review-state/` so ignored, reviewed, and
already-open discoveries are not repeatedly surfaced unless their source hash
changes. If repo-state JSON stops being enough, persistent storage belongs in
the RAN-144 infrastructure track.

### Discovery safety rules

Publish safety is enforced by `scripts/catalog_discovery/safety.py`.

Discovery reports separate review candidates from actual proposed catalog
edits. `removed` in a manifest/report means "catalog rows for scanned providers
that were not present in this provider scan"; those rows are
`removed_review_required` candidates for human review. They are not deleted
unless the generated `proposed-catalog.json` actually omits them.

Offline fixture runs often report large removed counts because the fixtures
cover only a small slice of the real catalog. For example, `removed: 116` with
`allowed: true` means the fixture scan did not see 116 catalog rows, but the
proposed catalog still retained them. It is not a proposal to delete 116 rows.

Default behavior blocks destructive or non-additive changes:

```bash
python scripts/catalog_discovery/safety.py \
  --base catalog.json \
  --proposed .atlas-review/test-run/proposed-catalog.json
```

Explicit override is required for destructive publishes:

```bash
python scripts/catalog_discovery/safety.py \
  --base catalog.json \
  --proposed .atlas-review/test-run/proposed-catalog.json \
  --allow-destructive
```

The safety guard compares the actual proposed catalog payload against the base
catalog. It blocks rows present in base but missing from proposed, removed
`default` flags, active rows changed to hidden/removed/deprecated, newly added
`superseded_by` links, and newly added rows without discovery evidence. If a
real discovery run writes removals into `proposed-catalog.json`, the guard
should fail unless an explicit destructive override is used.

Benchmark and provenance enrichment happens only during discovery / publish.
The worker records cited public benchmark values when the metric key is already
known to `task_benchmark_weights`; unknown or uncited values are recorded as
missing instead of invented.

RAN-347 uses the catalog-backward-compatible option B schema:

```jsonc
{
  "benchmarks": {
    "mmlu_pro": 0.82,
    "gpqa_diamond": null
  },
  "benchmarks_meta": {
    "mmlu_pro": {
      "source_url": "https://huggingface.co/spaces/example",
      "retrieved_at": "2026-05-16T00:00:00+00:00",
      "source_kind": "huggingface_leaderboard"
    },
    "gpqa_diamond": {
      "source_url": null,
      "retrieved_at": "2026-05-16T00:00:00+00:00",
      "missing_reason": "not_publicly_reported"
    }
  }
}
```

`benchmarks` remains the runtime value field and must stay flat numeric/null for
Atlas compatibility. `benchmarks_meta` carries source URL, retrieval timestamp,
source kind, and missing-data reason. Existing rows without `benchmarks_meta`
remain valid until refreshed.

When sources disagree for the same metric, discovery applies this priority:
HuggingFace leaderboard, then Artificial Analysis, then project README/model
card, then provider page. Every numeric score must have a public source URL and
retrieval timestamp. Missing values use `null` plus `missing_reason`.

### Backend-aware composite scores (RAN-351)

RAN-351 adds optional backend-aware scoring records under
`backend_composite_scores`. This field is additive: Atlas runtime readers that
only understand flat `benchmarks` continue to ignore it, and Atlas-side display
behavior is handled by a future coordinated consumer ticket.

Each composite record stores a structured tuple key instead of a packed string:

```jsonc
{
  "model_id": "openai:gpt-new",
  "backend": "openai",
  "node_class": "cloud",
  "hardware_class": "unknown",
  "quantization": "unknown",
  "context_tokens": 128000,
  "modality": "text",
  "task_id": "research_analysis",
  "score": 82,
  "coverage": 0.85,
  "components": {
    "benchmark_composite": {
      "score": 0.82,
      "weight": 0.6,
      "provenance": ["benchmarks_meta.mmlu_pro"]
    },
    "backend_capability": {
      "score": 1.0,
      "weight": 0.25,
      "features": ["structured_output", "tool_support"],
      "source_url": "https://example.com/backend-profile",
      "retrieved_at": "2026-05-16T00:00:00+00:00"
    },
    "runtime_profile": {
      "weight": 0.15,
      "missing_reason": "runtime_profile_not_reported"
    }
  }
}
```

The tuple fields are deliberately abstract. `node_class` and `hardware_class`
must use safe classes such as `local`, `cluster`, `cloud`, `basic`,
`standard`, `performance`, `high_performance`, `workstation`, or `unknown`.
Do not store private machine names, hostnames, raw profiler output, local
paths, tokens, or other operational identifiers in catalog scoring records.

Composite scores are derived only during discovery / publish. Atlas instances
must not fetch benchmark pages, backend docs, or hardware profiles at runtime.
Every benchmark-derived component references `benchmarks_meta.<metric>`.
Backend capability and runtime-profile components either carry a public
`source_url` plus `retrieved_at`, or carry a `missing_reason`. Missing facts
reduce `coverage`; they are never guessed.

The current component weights are:

| Component | Weight | Input |
| --- | ---: | --- |
| `benchmark_composite` | 0.60 | RAN-347 flat `benchmarks` plus `benchmarks_meta` provenance |
| `backend_capability` | 0.25 | backend feature facts such as continuous batching, KV cache control, sampling parameters, structured output, and tool support |
| `runtime_profile` | 0.15 | normalized throughput, TTFT, memory pressure, and context-capability signals |

Backend feature inventory remains a separate catalog extension. RAN-351 only
defines the scoring envelope and consumes backend facts when discovery fixtures
or cited research provide them.

## Current Catalog

241 models across 6 categories, including metadata-only cloud rows:

| Category | Count | Examples |
|----------|-------|---------|
| General | 24 | Gemma 4 31B, Llama 3.3, Dolphin 3, Qwen 2.5 |
| Coding | 4 | Qwen 2.5 Coder, Codestral, DeepSeek Coder |
| Reasoning | 3 | DeepSeek R1, QwQ |
| Vision | 28 | Claude, GPT, Gemini, Grok, Moondream, LLaVA, MiniCPM-V |
| Image Gen | 181 | Flux 2, SDXL, Hunyuan Video |
| Embedding | 1 | Nomic Embed |

## Contributing

Edit `catalog.json` and submit a PR. The schema is validated by Atlas on fetch — malformed entries are skipped gracefully.

## License

MIT
