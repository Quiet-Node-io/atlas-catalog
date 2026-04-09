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
  "catalog_version": 1,        // Bump when schema changes
  "updated": "2026-04-08",     // Last edit date
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
      "registry": "ollama",    // ollama or huggingface
      "superseded_by": null,   // Model ID that replaces this one
      "update_policy": "optional" // optional, recommended, required
    }
  ]
}
```

## Current Catalog

37 models across 5 categories:

| Category | Count | Examples |
|----------|-------|---------|
| General | 19 | Gemma 4 31B, Llama 3.3, Dolphin 3, Qwen 2.5 |
| Coding | 4 | Qwen 2.5 Coder, Codestral, DeepSeek Coder |
| Reasoning | 3 | DeepSeek R1, QwQ |
| Vision | 5 | Moondream, LLaVA, MiniCPM-V |
| Image Gen | 6 | Flux 2, SDXL, Hunyuan Video |

## Contributing

Edit `catalog.json` and submit a PR. The schema is validated by Atlas on fetch — malformed entries are skipped gracefully.

## License

MIT
