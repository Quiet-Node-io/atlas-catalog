"""Bounded benchmark and provenance aggregation for catalog discoveries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MAX_SNIPPET_CHARS = 500


def _research_path(discovery: dict[str, Any], fixture_root: Path) -> Path:
    filename = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(discovery["id"])) + ".json"
    return fixture_root / "research_payloads" / filename


def _snippet(text: str | None) -> str:
    if not text:
        return ""
    compact = " ".join(text.split())
    if len(compact) <= MAX_SNIPPET_CHARS:
        return compact
    return compact[:MAX_SNIPPET_CHARS].rstrip() + "..."


def _valid_metric(value: Any) -> bool:
    return isinstance(value, int | float) and 0 <= float(value) <= 1


def collect_research_for_model(
    discovery: dict[str, Any],
    fixture_root: Path,
    allowed_benchmarks: set[str],
) -> dict[str, Any]:
    path = _research_path(discovery, fixture_root)
    if not path.exists():
        return {"benchmarks": {}, "sources": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    benchmarks: dict[str, dict[str, Any]] = {}
    sources: list[dict[str, Any]] = []
    for source in payload.get("sources", []):
        if not isinstance(source, dict):
            continue
        source_entry = {
            "kind": str(source.get("kind", "unknown")),
            "url": str(source.get("url", "")),
            "snippet": _snippet(source.get("text")),
        }
        source_metrics: list[str] = []
        raw_benchmarks = source.get("benchmarks", {})
        if isinstance(raw_benchmarks, dict):
            for key, metric in raw_benchmarks.items():
                if key not in allowed_benchmarks or not isinstance(metric, dict):
                    continue
                source_url = metric.get("source_url") or source.get("url")
                value = metric.get("value")
                if not source_url or not _valid_metric(value):
                    continue
                benchmarks[str(key)] = {
                    "value": float(value),
                    "source_url": str(source_url),
                    "source_kind": source_entry["kind"],
                }
                source_metrics.append(str(key))
        if source_metrics:
            source_entry["benchmark_keys"] = sorted(source_metrics)
        sources.append(source_entry)
    return {"benchmarks": benchmarks, "sources": sources}


def collect_research_for_models(
    discoveries: list[dict[str, Any]],
    fixture_root: Path,
    allowed_benchmarks: set[str],
) -> dict[str, dict[str, Any]]:
    return {
        discovery["id"]: collect_research_for_model(discovery, fixture_root, allowed_benchmarks)
        for discovery in discoveries
    }
