"""Backend-aware composite scoring for catalog discovery review rows."""

from __future__ import annotations

from typing import Any

from .report import utc_now_iso

COMPONENT_WEIGHTS = {
    "benchmark_composite": 0.60,
    "backend_capability": 0.25,
    "runtime_profile": 0.15,
}

SAMPLING_PARAMS = ("temperature", "top_p", "top_k")


def _score_value(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    score = float(value)
    if 0.0 <= score <= 1.0:
        return score
    return None


def _benchmark_component(
    *,
    benchmarks: dict[str, Any],
    benchmarks_meta: dict[str, Any],
    task_weights: dict[str, Any],
) -> dict[str, Any]:
    weighted_sum = 0.0
    present_weight = 0.0
    provenance: list[str] = []

    for metric_key, weight in task_weights.items():
        if isinstance(weight, bool) or not isinstance(weight, int | float) or float(weight) < 0:
            continue
        metric = benchmarks.get(str(metric_key))
        if not isinstance(metric, dict):
            continue
        value = _score_value(metric.get("value"))
        if value is None or str(metric_key) not in benchmarks_meta:
            continue
        weighted_sum += value * float(weight)
        present_weight += float(weight)
        provenance.append(f"benchmarks_meta.{metric_key}")

    if present_weight <= 0:
        return {
            "weight": COMPONENT_WEIGHTS["benchmark_composite"],
            "missing_reason": "benchmark_coverage_not_reported",
        }

    return {
        "score": round(weighted_sum / present_weight, 4),
        "weight": COMPONENT_WEIGHTS["benchmark_composite"],
        "provenance": provenance,
    }


def _sampling_score(params: Any) -> float | None:
    if not isinstance(params, list):
        return None
    supported = {str(param) for param in params}
    return len(set(SAMPLING_PARAMS) & supported) / len(SAMPLING_PARAMS)


def _backend_capability_component(profile: dict[str, Any]) -> dict[str, Any]:
    features = profile.get("features")
    if not isinstance(features, dict):
        return {
            "weight": COMPONENT_WEIGHTS["backend_capability"],
            "missing_reason": "backend_features_not_reported",
        }

    feature_scores: dict[str, float] = {}
    if isinstance(features.get("continuous_batching"), bool):
        feature_scores["continuous_batching"] = 1.0 if features["continuous_batching"] else 0.0
    kv_cache = features.get("kv_cache_control")
    if isinstance(kv_cache, str):
        feature_scores["kv_cache_control"] = {
            "explicit": 1.0,
            "configurable": 1.0,
            "limited": 0.5,
            "implicit": 0.25,
            "none": 0.0,
        }.get(kv_cache, 0.0)
    sampling = _sampling_score(features.get("sampling_param_support"))
    if sampling is not None:
        feature_scores["sampling_param_support"] = sampling
    if isinstance(features.get("structured_output"), bool):
        feature_scores["structured_output"] = 1.0 if features["structured_output"] else 0.0
    if isinstance(features.get("tool_support"), bool):
        feature_scores["tool_support"] = 1.0 if features["tool_support"] else 0.0

    if not feature_scores:
        return {
            "weight": COMPONENT_WEIGHTS["backend_capability"],
            "missing_reason": "backend_features_not_reported",
        }
    if not isinstance(profile.get("source_url"), str) or not profile.get("source_url"):
        return {
            "weight": COMPONENT_WEIGHTS["backend_capability"],
            "missing_reason": "backend_profile_source_not_reported",
        }

    return {
        "score": round(sum(feature_scores.values()) / len(feature_scores), 4),
        "weight": COMPONENT_WEIGHTS["backend_capability"],
        "features": sorted(feature_scores),
        "source_url": profile.get("source_url"),
        "retrieved_at": profile.get("retrieved_at") or utc_now_iso(),
    }


def _runtime_profile_component(profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile.get("source_url"), str) or not profile.get("source_url"):
        return {
            "weight": COMPONENT_WEIGHTS["runtime_profile"],
            "missing_reason": "backend_profile_source_not_reported",
        }

    runtime_profile = profile.get("runtime_profile")
    if not isinstance(runtime_profile, dict):
        runtime_profile = {}

    metric_scores: dict[str, float] = {}
    for key in ("throughput_score", "ttft_score", "memory_pressure_score"):
        value = _score_value(runtime_profile.get(key))
        if value is not None:
            metric_scores[key] = value

    context_tokens = profile.get("context_tokens")
    if isinstance(context_tokens, int) and context_tokens > 0:
        metric_scores["context_tokens"] = min(context_tokens / 131072, 1.0)

    if not metric_scores:
        return {
            "weight": COMPONENT_WEIGHTS["runtime_profile"],
            "missing_reason": "runtime_profile_not_reported",
        }

    return {
        "score": round(sum(metric_scores.values()) / len(metric_scores), 4),
        "weight": COMPONENT_WEIGHTS["runtime_profile"],
        "metrics": sorted(metric_scores),
        "source_url": profile.get("source_url"),
        "retrieved_at": profile.get("retrieved_at") or utc_now_iso(),
    }


def _record_score(components: dict[str, dict[str, Any]]) -> tuple[int, float]:
    weighted_sum = 0.0
    present_weight = 0.0
    intended_weight = sum(COMPONENT_WEIGHTS.values())

    for component in components.values():
        if "score" not in component:
            continue
        score = _score_value(component.get("score"))
        weight = _score_value(component.get("weight"))
        if score is None or weight is None:
            continue
        weighted_sum += score * weight
        present_weight += weight

    if present_weight <= 0 or intended_weight <= 0:
        return 0, 0.0
    return round((weighted_sum / present_weight) * 100), round(present_weight / intended_weight, 4)


def build_backend_composite_scores(
    *,
    model_id: str,
    benchmarks: dict[str, Any],
    benchmarks_meta: dict[str, Any],
    task_benchmark_weights: dict[str, Any],
    backend_profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build additive backend-aware score records for one catalog row."""

    if not backend_profiles or not isinstance(task_benchmark_weights, dict):
        return []

    records: list[dict[str, Any]] = []
    for profile in backend_profiles:
        if not isinstance(profile, dict):
            continue
        for task_id, task_weights in sorted(task_benchmark_weights.items()):
            if not isinstance(task_weights, dict):
                continue
            components = {
                "benchmark_composite": _benchmark_component(
                    benchmarks=benchmarks,
                    benchmarks_meta=benchmarks_meta,
                    task_weights=task_weights,
                ),
                "backend_capability": _backend_capability_component(profile),
                "runtime_profile": _runtime_profile_component(profile),
            }
            score, coverage = _record_score(components)
            records.append(
                {
                    "model_id": model_id,
                    "backend": profile.get("backend", "unknown"),
                    "node_class": profile.get("node_class", "unknown"),
                    "hardware_class": profile.get("hardware_class", "unknown"),
                    "quantization": profile.get("quantization", "unknown"),
                    "context_tokens": profile.get("context_tokens", 0),
                    "modality": profile.get("modality", "text"),
                    "task_id": str(task_id),
                    "score": score,
                    "coverage": coverage,
                    "components": components,
                }
            )
    return records
