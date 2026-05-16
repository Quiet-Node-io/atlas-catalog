"""Catalog diffing for maintainer review."""

from __future__ import annotations

from typing import Any


def _provider_name(value: Any) -> str:
    return str(value or "").lower().replace(" ", "").replace("-", "")


def _row_provider(row: dict[str, Any]) -> str:
    provider = row.get("provider")
    if provider:
        return _provider_name(provider)
    model_id = str(row.get("id", ""))
    if ":" in model_id:
        return _provider_name(model_id.split(":", 1)[0])
    return ""


def _row_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    row_id = row.get("id")
    if isinstance(row_id, str):
        keys.add(row_id)
    provider = _row_provider(row)
    for field in ("provider_model_ref", "provider_variant_ref", "ollama_pull_tag"):
        value = row.get(field)
        if isinstance(value, str) and value:
            keys.add(value)
            if provider:
                keys.add(f"{provider}:{value}")
    return keys


def diff_catalog(
    catalog: dict[str, Any],
    discoveries: list[dict[str, Any]],
    *,
    scanned_providers: set[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    scanned = {_provider_name(provider) for provider in scanned_providers or set()}
    existing_keys: set[str] = set()
    for row in catalog.get("models", []):
        if isinstance(row, dict):
            existing_keys.update(_row_keys(row))

    discovery_keys = {str(item.get("id")) for item in discoveries}
    discovery_keys.update(str(item.get("provider_model_id")) for item in discoveries)

    added = [item for item in discoveries if item.get("id") not in existing_keys and item.get("provider_model_id") not in existing_keys]
    removed: list[dict[str, Any]] = []
    for row in catalog.get("models", []):
        if not isinstance(row, dict):
            continue
        provider = _row_provider(row)
        if scanned and provider not in scanned:
            continue
        if _row_keys(row).isdisjoint(discovery_keys):
            removed.append(
                {
                    "id": row.get("id"),
                    "provider": provider,
                    "state": "removed_review_required",
                    "reason": "Catalog row was not present in this provider scan.",
                }
            )
    return {"added": added, "removed": removed, "changed": []}
