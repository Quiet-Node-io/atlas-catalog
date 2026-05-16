"""JSON helpers for the catalog discovery worker."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def catalog_model_keys(catalog: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for row in catalog.get("models", []):
        if not isinstance(row, dict):
            continue
        for field in ("id", "provider_model_ref", "provider_variant_ref", "ollama_pull_tag"):
            value = row.get(field)
            if isinstance(value, str) and value.strip():
                keys.add(value.strip())
    return keys


def benchmark_keys(catalog: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    weights = catalog.get("task_benchmark_weights", {})
    if not isinstance(weights, dict):
        return keys
    for task_weights in weights.values():
        if isinstance(task_weights, dict):
            keys.update(str(key) for key in task_weights)
    return keys
