"""Validation helpers for backend-aware composite scoring records."""

from __future__ import annotations

from datetime import datetime
from typing import Any


KNOWN_BACKENDS = {
    "anthropic",
    "civitai",
    "google",
    "huggingface",
    "llama_cpp",
    "litellm",
    "mlx_lm",
    "ollama",
    "openai",
    "vllm",
    "xai",
}

KNOWN_NODE_CLASSES = {"cloud", "cluster", "local", "unknown"}

KNOWN_HARDWARE_CLASSES = {
    "basic",
    "standard",
    "performance",
    "high_performance",
    "workstation",
    "unknown",
}

KNOWN_MODALITIES = {"audio", "embedding", "image", "multimodal", "text", "vision"}

KNOWN_QUANTIZATIONS = {
    "BF16",
    "F16",
    "F32",
    "FP16",
    "Q2_K",
    "Q3_K_L",
    "Q3_K_M",
    "Q3_K_S",
    "Q4_0",
    "Q4_1",
    "Q4_K_M",
    "Q4_K_S",
    "Q5_0",
    "Q5_1",
    "Q5_K_M",
    "Q5_K_S",
    "Q6_K",
    "Q8_0",
    "unknown",
}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_timestamp(value: Any) -> bool:
    if not _nonempty_string(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _valid_number(value: Any, minimum: float, maximum: float) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    number = float(value)
    return float("-inf") < number < float("inf") and minimum <= number <= maximum


def _validate_component(
    *,
    model_id: str,
    record_index: int,
    component_name: str,
    component: Any,
    benchmarks_meta: dict[str, Any],
) -> list[str]:
    prefix = f"{model_id} backend_composite_scores[{record_index}].components.{component_name}"
    if not isinstance(component, dict):
        return [f"{prefix}: component must be an object"]

    errors: list[str] = []
    if not _valid_number(component.get("weight"), 0.0, 1.0):
        errors.append(f"{prefix}: weight must be 0-1")

    has_score = "score" in component
    if has_score and not _valid_number(component.get("score"), 0.0, 1.0):
        errors.append(f"{prefix}: score must be 0-1")

    missing_reason = component.get("missing_reason")
    if not has_score:
        if not _nonempty_string(missing_reason):
            errors.append(f"{prefix}: missing score requires missing_reason")
        return errors

    if component_name == "benchmark_composite":
        provenance = component.get("provenance")
        if not isinstance(provenance, list) or not provenance:
            errors.append(f"{prefix}: benchmark score requires provenance")
            return errors
        for reference in provenance:
            if not _nonempty_string(reference) or not str(reference).startswith("benchmarks_meta."):
                errors.append(f"{prefix}: invalid provenance reference {reference!r}")
                continue
            metric_key = str(reference).split(".", 1)[1]
            if metric_key not in benchmarks_meta:
                errors.append(f"{prefix}: provenance {reference} missing from benchmarks_meta")
        return errors

    source_url = component.get("source_url")
    if not _nonempty_string(source_url):
        errors.append(f"{prefix}: scored component requires source_url")
    if not _valid_timestamp(component.get("retrieved_at")):
        errors.append(f"{prefix}: scored component requires valid retrieved_at")
    return errors


def validate_backend_composite_scores(
    row: dict[str, Any],
    *,
    task_ids: set[str] | None = None,
) -> list[str]:
    """Validate optional backend-aware score records on one catalog row."""

    model_id = str(row.get("id") or "<unknown>")
    records = row.get("backend_composite_scores")
    if records is None:
        return []
    if not isinstance(records, list):
        return [f"{model_id}: backend_composite_scores must be an array"]

    benchmarks_meta = row.get("benchmarks_meta", {})
    if not isinstance(benchmarks_meta, dict):
        benchmarks_meta = {}

    errors: list[str] = []
    for index, record in enumerate(records):
        prefix = f"{model_id} backend_composite_scores[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix}: record must be an object")
            continue

        record_model_id = record.get("model_id")
        if record_model_id != model_id:
            errors.append(f"{prefix}: model_id must match row id")

        backend = record.get("backend")
        if backend not in KNOWN_BACKENDS:
            errors.append(f"{prefix}: unknown backend {backend}")

        node_class = record.get("node_class")
        if node_class not in KNOWN_NODE_CLASSES:
            errors.append(f"{prefix}: unknown node_class {node_class}")

        hardware_class = record.get("hardware_class")
        if hardware_class not in KNOWN_HARDWARE_CLASSES:
            errors.append(f"{prefix}: unknown hardware_class {hardware_class}")

        quantization = record.get("quantization")
        if quantization not in KNOWN_QUANTIZATIONS:
            errors.append(f"{prefix}: unknown quantization {quantization}")

        if not isinstance(record.get("context_tokens"), int) or record.get("context_tokens") <= 0:
            errors.append(f"{prefix}: context_tokens must be a positive integer")

        modality = record.get("modality")
        if modality not in KNOWN_MODALITIES:
            errors.append(f"{prefix}: unknown modality {modality}")

        task_id = record.get("task_id")
        if not _nonempty_string(task_id):
            errors.append(f"{prefix}: task_id is required")
        elif task_ids is not None and str(task_id) not in task_ids:
            errors.append(f"{prefix}: unknown task_id {task_id}")

        if not _valid_number(record.get("score"), 0.0, 100.0):
            errors.append(f"{prefix}: score must be 0-100")
        if not _valid_number(record.get("coverage"), 0.0, 1.0):
            errors.append(f"{prefix}: coverage must be 0-1")

        components = record.get("components")
        if not isinstance(components, dict) or not components:
            errors.append(f"{prefix}: components must be a non-empty object")
            continue

        for component_name, component in components.items():
            if not _nonempty_string(component_name):
                errors.append(f"{prefix}: component name must be non-empty")
                continue
            errors.extend(
                _validate_component(
                    model_id=model_id,
                    record_index=index,
                    component_name=str(component_name),
                    component=component,
                    benchmarks_meta=benchmarks_meta,
                )
            )

    return errors
