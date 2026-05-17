"""Bounded benchmark and provenance aggregation for catalog discoveries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .report import utc_now_iso
from .research_sources import (
    DEFAULT_SOURCE_KINDS,
    metric_observations_from_source,
    source_priority,
)

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


def collect_research_for_model(
    discovery: dict[str, Any],
    fixture_root: Path,
    allowed_benchmarks: set[str],
) -> dict[str, Any]:
    path = _research_path(discovery, fixture_root)
    if not path.exists():
        retrieved_at = utc_now_iso()
        return {
            "benchmarks": {
                metric_key: {"value": None}
                for metric_key in sorted(allowed_benchmarks)
            },
            "benchmarks_meta": {
                metric_key: {
                    "source_url": None,
                    "retrieved_at": retrieved_at,
                    "missing_reason": "not_publicly_reported",
                }
                for metric_key in sorted(allowed_benchmarks)
            },
            "sources": [
                {
                    "kind": kind,
                    "url": "",
                    "retrieved_at": retrieved_at,
                    "status": "not_configured_for_fixture",
                }
                for kind in DEFAULT_SOURCE_KINDS
            ],
            "conflicts": {},
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    benchmarks: dict[str, dict[str, Any]] = {}
    benchmarks_meta: dict[str, dict[str, Any]] = {}
    sources: list[dict[str, Any]] = []
    observations_by_metric: dict[str, list[dict[str, Any]]] = {}
    retrieved_at = str(payload.get("retrieved_at") or utc_now_iso())

    for source in payload.get("sources", []):
        if not isinstance(source, dict):
            continue
        source_entry, observations = metric_observations_from_source(
            source,
            allowed_metrics=allowed_benchmarks,
            fallback_retrieved_at=retrieved_at,
        )
        source_entry["snippet"] = _snippet(source.get("text"))
        for observation in observations:
            observations_by_metric.setdefault(str(observation["metric"]), []).append(observation)
        sources.append(source_entry)

    seen_kinds = {str(source.get("kind")) for source in sources}
    for kind in DEFAULT_SOURCE_KINDS:
        if kind not in seen_kinds:
            sources.append(
                {
                    "kind": kind,
                    "url": "",
                    "retrieved_at": retrieved_at,
                    "status": "not_configured_for_fixture",
                }
            )

    conflicts: dict[str, list[dict[str, Any]]] = {}
    for metric_key, observations in observations_by_metric.items():
        ordered = sorted(observations, key=lambda item: source_priority(str(item["source_kind"])))
        selected = ordered[0]
        benchmarks[metric_key] = {
            "value": float(selected["value"]),
            "source_url": str(selected["source_url"]),
            "source_kind": str(selected["source_kind"]),
            "retrieved_at": str(selected["retrieved_at"]),
        }
        benchmarks_meta[metric_key] = {
            "source_url": str(selected["source_url"]),
            "retrieved_at": str(selected["retrieved_at"]),
            "source_kind": str(selected["source_kind"]),
        }
        if len(ordered) > 1:
            conflicts[metric_key] = [
                {
                    "value": float(item["value"]),
                    "source_url": str(item["source_url"]),
                    "source_kind": str(item["source_kind"]),
                    "retrieved_at": str(item["retrieved_at"]),
                }
                for item in ordered[1:]
            ]

    for metric_key in sorted(allowed_benchmarks):
        if metric_key in benchmarks:
            continue
        benchmarks[metric_key] = {"value": None}
        benchmarks_meta[metric_key] = {
            "source_url": None,
            "retrieved_at": retrieved_at,
            "missing_reason": "not_publicly_reported",
        }

    return {
        "benchmarks": benchmarks,
        "benchmarks_meta": benchmarks_meta,
        "sources": sources,
        "conflicts": conflicts,
    }


def collect_research_for_models(
    discoveries: list[dict[str, Any]],
    fixture_root: Path,
    allowed_benchmarks: set[str],
) -> dict[str, dict[str, Any]]:
    return {
        discovery["id"]: collect_research_for_model(discovery, fixture_root, allowed_benchmarks)
        for discovery in discoveries
    }
