"""Benchmark value and provenance validation helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _valid_score(value: Any) -> bool:
    if value is None:
        return True
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and float("-inf") < float(value) < float("inf")
        and 0.0 <= float(value) <= 1.0
    )


def validate_benchmark_provenance(row: dict[str, Any]) -> list[str]:
    """Validate option-B benchmark provenance on one catalog row."""

    model_id = str(row.get("id") or "<unknown>")
    benchmarks = row.get("benchmarks", {})
    if not isinstance(benchmarks, dict):
        return [f"{model_id}: benchmarks must be an object"]
    meta = row.get("benchmarks_meta", {})
    if not isinstance(meta, dict):
        return [f"{model_id}: benchmarks_meta must be an object"]

    errors: list[str] = []
    for metric, value in benchmarks.items():
        metric_id = str(metric)
        if isinstance(value, dict):
            errors.append(f"{model_id}: {metric_id} must be flat numeric/null, not object")
            continue
        if not _valid_score(value):
            errors.append(f"{model_id}: {metric_id} benchmark value must be numeric 0-1 or null")
            continue

        metric_meta = meta.get(metric_id)
        if not isinstance(metric_meta, dict):
            errors.append(f"{model_id}: {metric_id} missing benchmarks_meta")
            continue
        if not _valid_timestamp(metric_meta.get("retrieved_at")):
            errors.append(f"{model_id}: {metric_id} missing valid retrieved_at")

        if value is None:
            reason = metric_meta.get("missing_reason")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{model_id}: {metric_id} null value missing missing_reason")
            continue

        source_url = metric_meta.get("source_url")
        if not isinstance(source_url, str) or not source_url.strip():
            errors.append(f"{model_id}: {metric_id} numeric value missing source_url")
        source_kind = metric_meta.get("source_kind")
        if not isinstance(source_kind, str) or not source_kind.strip():
            errors.append(f"{model_id}: {metric_id} numeric value missing source_kind")

    return errors
