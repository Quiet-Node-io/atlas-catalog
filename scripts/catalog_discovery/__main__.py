"""Command line entry point for maintainer-side catalog discovery."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from .catalog_io import benchmark_keys, load_json, write_json
from .diff import diff_catalog
from .providers import fetch_configured_sources, load_offline_provider_payloads
from .report import render_report, utc_now_iso
from .research import collect_research_for_models
from .review_state import filter_previously_reviewed, load_review_state, update_open_pr_state
from .safety import evaluate_catalog_publish


def _registry_for_provider(provider: str) -> str:
    if provider in {"huggingface", "ollama", "civitai"}:
        return provider
    return "cloud"


def _provider_display(provider: str) -> str:
    names = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google",
        "xai": "xAI",
        "huggingface": "HuggingFace",
        "ollama": "Ollama",
    }
    return names.get(provider, provider)


def _catalog_row(discovery: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    provider = str(discovery["provider"])
    row = {
        "id": discovery["id"],
        "name": discovery.get("name") or discovery["provider_model_id"],
        "description": "Review required: discovered by maintainer-side catalog automation.",
        "category": "general",
        "registry": _registry_for_provider(provider),
        "provider": _provider_display(provider),
        "provider_model_ref": discovery["provider_model_id"],
        "status": "review_required",
        "default": False,
        "atlas_pick": False,
        "unrestricted": False,
        "variant": "standard",
        "update_policy": "optional",
        "benchmarks": {
            key: metric["value"]
            for key, metric in sorted(research.get("benchmarks", {}).items())
        },
        "benchmarks_meta": {
            key: value
            for key, value in sorted(research.get("benchmarks_meta", {}).items())
        },
        "discovery_evidence": {
            "source_url": discovery.get("source_url"),
            "source_hash": discovery.get("source_hash"),
            "sources": research.get("sources", [])
            or [{"kind": "provider_model_list", "url": discovery.get("source_url")}],
        },
    }
    backend_scores = research.get("backend_composite_scores")
    if isinstance(backend_scores, list) and backend_scores:
        row["backend_composite_scores"] = backend_scores
    return row


def _proposed_catalog(
    catalog: dict[str, Any],
    added: list[dict[str, Any]],
    research_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    proposed = copy.deepcopy(catalog)
    rows = proposed.setdefault("models", [])
    for discovery in added:
        rows.append(_catalog_row(discovery, research_by_id.get(discovery["id"], {})))
    proposed["updated"] = utc_now_iso()[:10]
    return proposed


def run_discovery(
    *,
    catalog_path: Path,
    output_dir: Path,
    offline_fixtures: Path | None = None,
    sources_path: Path | None = None,
    create_pr: bool = False,
    allow_destructive: bool = False,
) -> dict[str, Any]:
    catalog = load_json(catalog_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = Path("review-state/discoveries.json")
    review_state = load_review_state(state_path)

    provider_errors: list[dict[str, Any]] = []
    if offline_fixtures is not None:
        discoveries = load_offline_provider_payloads(offline_fixtures)
    elif sources_path is not None:
        discoveries, provider_errors = fetch_configured_sources(sources_path)
    else:
        discoveries = []

    visible_discoveries = filter_previously_reviewed(discoveries, review_state)
    scanned_providers = {str(item.get("provider")) for item in discoveries}
    diff_result = diff_catalog(catalog, visible_discoveries, scanned_providers=scanned_providers)
    fixture_root = offline_fixtures or Path(".")
    research_by_id = collect_research_for_models(
        diff_result["added"],
        fixture_root,
        benchmark_keys(catalog),
        catalog.get("task_benchmark_weights", {}),
    )
    proposed = _proposed_catalog(catalog, diff_result["added"], research_by_id)
    safety_result = evaluate_catalog_publish(
        catalog,
        proposed,
        allow_destructive=allow_destructive,
    )

    provider_evidence_dir = output_dir / "provider-evidence"
    write_json(provider_evidence_dir / "discoveries.json", discoveries)
    write_json(output_dir / "proposed-catalog.json", proposed)
    manifest = {
        "run_id": output_dir.name,
        "generated_at": utc_now_iso(),
        "summary": {
            "added": len(diff_result["added"]),
            "removed": len(diff_result["removed"]),
            "changed": len(diff_result["changed"]),
        },
        "provider_errors": provider_errors,
        "create_pr_requested": create_pr,
        "safety": safety_result.to_dict(),
    }
    write_json(output_dir / "manifest.json", manifest)
    report = render_report(
        run_id=output_dir.name,
        diff_result=diff_result,
        provider_errors=provider_errors,
        safety=safety_result.to_dict(),
    )
    (output_dir / "catalog-review-report.md").write_text(report, encoding="utf-8")
    if create_pr and diff_result["added"]:
        updated = update_open_pr_state(review_state, diff_result["added"])
        write_json(state_path, updated)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Atlas catalog discovery.")
    parser.add_argument("--catalog", type=Path, default=Path("catalog.json"))
    parser.add_argument("--offline-fixtures", type=Path)
    parser.add_argument("--sources", type=Path, default=Path("scripts/catalog_discovery/sources.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-pr", action="store_true")
    parser.add_argument("--allow-destructive", action="store_true")
    args = parser.parse_args()
    sources_path = None if args.offline_fixtures else args.sources
    result = run_discovery(
        catalog_path=args.catalog,
        output_dir=args.output,
        offline_fixtures=args.offline_fixtures,
        sources_path=sources_path,
        create_pr=not args.no_pr,
        allow_destructive=args.allow_destructive,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
