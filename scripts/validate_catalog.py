#!/usr/bin/env python3
"""Validate the published Atlas catalog JSON.

RAN-186 locks the Ollama-row structured schema so Atlas surfaces no
variant metadata by frontend string inference.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.catalog_discovery.benchmark_provenance import validate_benchmark_provenance
from scripts.catalog_discovery.backend_inventory_schema import validate_backend_inventory
from scripts.catalog_discovery.backend_score_schema import validate_backend_composite_scores

KNOWN_QUANT_MARKERS = {
    "Q2_K",
    "Q3_K_S",
    "Q3_K_M",
    "Q3_K_L",
    "Q4_K_S",
    "Q4_K_M",
    "Q4_0",
    "Q4_1",
    "Q5_K_S",
    "Q5_K_M",
    "Q5_0",
    "Q5_1",
    "Q6_K",
    "Q8_0",
    "F16",
    "FP16",
    "BF16",
    "F32",
}

NAME_QUANT_TAIL = re.compile(
    r"\s+(Q4_K_M|Q4_K_S|Q5_K_M|Q5_K_S|Q6_K|Q8_0|BF16|F16|FP16|Q4|Q5|Q6|Q8)$",
    re.IGNORECASE,
)

REQUIRED_OLLAMA_FIELDS = (
    "id",
    "name",
    "display_name",
    "variant_label",
    "quantization",
    "family",
    "publisher",
    "provider",
    "variant_group",
)

KNOWN_VARIANTS = {"standard", "unrestricted"}


def _nonempty_string(row: dict[str, Any], field: str) -> bool:
    value = row.get(field)
    return isinstance(value, str) and bool(value.strip())


def validate_catalog(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = payload.get("models")
    if not isinstance(models, list):
        return ["catalog.json must contain a top-level models array"]

    backend_ids, errors = validate_backend_inventory(payload)
    seen_ids: set[str] = set()
    task_ids = {
        str(task_id)
        for task_id, weights in dict(payload.get("task_benchmark_weights", {})).items()
        if isinstance(weights, dict)
    }
    for idx, row in enumerate(models):
        if not isinstance(row, dict):
            errors.append(f"models[{idx}] is not an object")
            continue
        model_id = str(row.get("id") or f"models[{idx}]")
        if model_id in seen_ids:
            errors.append(f"{model_id}: duplicate model id")
        seen_ids.add(model_id)

        variant = row.get("variant")
        if variant not in KNOWN_VARIANTS:
            errors.append(f"{model_id}: variant must be one of standard, unrestricted")
        if variant == "unrestricted" and row.get("unrestricted") is not True:
            errors.append(f"{model_id}: variant=unrestricted requires unrestricted=true")
        if row.get("unrestricted") is True and variant != "unrestricted":
            errors.append(f"{model_id}: unrestricted=true requires variant=unrestricted")

        if "benchmarks_meta" in row:
            errors.extend(validate_benchmark_provenance(row))
        errors.extend(
            validate_backend_composite_scores(
                row,
                known_backends=backend_ids or None,
                task_ids=task_ids,
            )
        )

        backend_id = row.get("backend_id")
        if backend_id is not None and backend_id not in backend_ids:
            errors.append(f"{model_id}: backend_id references unknown backend {backend_id}")

        backend_id_list = row.get("backend_ids")
        if backend_id_list is not None:
            if not isinstance(backend_id_list, list):
                errors.append(f"{model_id}: backend_ids must be an array")
            else:
                for item in backend_id_list:
                    if item not in backend_ids:
                        errors.append(f"{model_id}: backend_ids references unknown backend {item}")

        if row.get("registry") != "ollama":
            continue

        for field in REQUIRED_OLLAMA_FIELDS:
            if not _nonempty_string(row, field):
                errors.append(f"{model_id}: missing non-empty {field}")

        quant = str(row.get("quantization") or "").upper()
        if quant and quant not in KNOWN_QUANT_MARKERS:
            errors.append(f"{model_id}: unknown quantization {row.get('quantization')!r}")

        name = str(row.get("name") or "")
        if NAME_QUANT_TAIL.search(name):
            errors.append(f"{model_id}: name must not end with a quantization token")

        pull_tag = row.get("ollama_pull_tag")
        if pull_tag is not None and (not isinstance(pull_tag, str) or not pull_tag.strip()):
            errors.append(
                f"{model_id}: omit ollama_pull_tag unless it names a real alternate pull tag"
            )

    return errors


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "catalog.json")
    errors = validate_catalog(path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"{path}: catalog validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
