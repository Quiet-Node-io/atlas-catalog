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
  "catalog_version": 4,        // Bump when schema changes
  "updated": "2026-05-02",     // Last edit date
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

Run `python scripts/validate_catalog.py catalog.json` before opening catalog
PRs. The GitHub workflow runs the same validator on catalog changes.

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
