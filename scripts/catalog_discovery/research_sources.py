"""Research source normalization for benchmark discovery."""

from __future__ import annotations

import re
from typing import Any

DEFAULT_SOURCE_KINDS = (
    "huggingface_leaderboard",
    "artificial_analysis",
    "project_readme",
    "provider_page",
)

SOURCE_PRIORITY = {
    "huggingface_leaderboard": 0,
    "artificial_analysis": 1,
    "project_readme": 2,
    "model_card": 2,
    "provider_page": 3,
}

METRIC_ALIASES = {
    "mmlu": "mmlu",
    "mmlu_pro": "mmlu_pro",
    "mmlu pro": "mmlu_pro",
    "gpqa": "gpqa_diamond",
    "gpqa_diamond": "gpqa_diamond",
    "gpqa diamond": "gpqa_diamond",
    "humaneval": "humaneval",
    "human eval": "humaneval",
    "math": "math",
    "speed_score": "speed_score",
    "speed score": "speed_score",
}


def source_priority(kind: str) -> int:
    return SOURCE_PRIORITY.get(kind, 99)


def normalize_metric_key(raw: Any) -> str:
    key = str(raw).strip().lower().replace("-", "_")
    key = re.sub(r"\s+", " ", key)
    return METRIC_ALIASES.get(key, key.replace(" ", "_"))


def parse_score(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        score = float(value)
    elif isinstance(value, str):
        text = value.strip()
        is_percent = text.endswith("%")
        text = text.rstrip("%").strip()
        try:
            score = float(text)
        except ValueError:
            return None
        if is_percent or score > 1.0:
            score = score / 100.0
    else:
        return None
    if 0.0 <= score <= 1.0:
        return score
    return None


def markdown_table_metrics(text: str, allowed_metrics: set[str]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= {"-"}:
            continue
        metric = normalize_metric_key(cells[0])
        if metric not in allowed_metrics:
            continue
        score = parse_score(cells[1])
        if score is not None:
            metrics[metric] = score
    return metrics


def metric_observations_from_source(
    source: dict[str, Any],
    *,
    allowed_metrics: set[str],
    fallback_retrieved_at: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    kind = str(source.get("kind", "unknown"))
    source_url = str(source.get("url", ""))
    retrieved_at = str(source.get("retrieved_at") or fallback_retrieved_at)
    observations: list[dict[str, Any]] = []

    raw_benchmarks = source.get("benchmarks", {})
    if isinstance(raw_benchmarks, dict):
        for raw_key, metric in raw_benchmarks.items():
            metric_key = normalize_metric_key(raw_key)
            if metric_key not in allowed_metrics or not isinstance(metric, dict):
                continue
            value = parse_score(metric.get("value"))
            cited_url = metric.get("source_url") or source_url
            if value is None or not cited_url:
                continue
            observations.append(
                {
                    "metric": metric_key,
                    "value": value,
                    "source_url": str(cited_url),
                    "retrieved_at": retrieved_at,
                    "source_kind": kind,
                }
            )

    text = source.get("text")
    if isinstance(text, str) and text:
        for metric_key, value in markdown_table_metrics(text, allowed_metrics).items():
            if source_url:
                observations.append(
                    {
                        "metric": metric_key,
                        "value": value,
                        "source_url": source_url,
                        "retrieved_at": retrieved_at,
                        "source_kind": kind,
                    }
                )

    source_entry = {
        "kind": kind,
        "url": source_url,
        "retrieved_at": retrieved_at,
    }
    if observations:
        source_entry["benchmark_keys"] = sorted({str(item["metric"]) for item in observations})
    return source_entry, observations
