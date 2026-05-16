"""Provider and registry discovery adapters.

The worker treats upstream results as review evidence, not publish-ready truth.
Provider APIs differ wildly, so this module normalizes only the stable minimum:
provider, provider model id, display name, source URL, and bounded metadata.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _items_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "models", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _provider_model_id(provider: str, item: dict[str, Any]) -> str | None:
    raw = item.get("id") or item.get("modelId") or item.get("name") or item.get("model")
    if raw is None:
        return None
    model_id = str(raw).strip()
    if provider == "google" and model_id.startswith("models/"):
        model_id = model_id.removeprefix("models/")
    return model_id or None


def _display_name(provider_model_id: str, item: dict[str, Any]) -> str:
    raw = item.get("display_name") or item.get("displayName") or item.get("name") or provider_model_id
    name = str(raw).strip()
    if name.startswith("models/"):
        return provider_model_id
    return name or provider_model_id


def _bounded_metadata(item: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    allowed = {
        "created",
        "createdAt",
        "downloads",
        "likes",
        "pipeline_tag",
        "library_name",
        "owned_by",
        "type",
        "availability",
        "supportsGeneration",
    }
    for key in allowed:
        if key in item:
            metadata[key] = item[key]
    return metadata


def normalize_provider_payload(
    provider: str,
    payload: Any,
    *,
    source_url: str,
) -> list[dict[str, Any]]:
    normalized_provider = provider.lower().strip()
    discoveries: list[dict[str, Any]] = []
    for item in _items_from_payload(payload):
        provider_model_id = _provider_model_id(normalized_provider, item)
        if not provider_model_id:
            continue
        discovery = {
            "id": f"{normalized_provider}:{provider_model_id}",
            "provider": normalized_provider,
            "provider_model_id": provider_model_id,
            "name": _display_name(provider_model_id, item),
            "status": "review_required",
            "source_url": source_url,
            "source_hash": _stable_hash(item),
            "metadata": _bounded_metadata(item),
        }
        discoveries.append(discovery)
    return discoveries


def normalize_ollama_library_html(html: str, *, source_url: str) -> list[dict[str, Any]]:
    names = sorted(set(re.findall(r'href="/library/([^"#?]+)"', html)))
    return [
        {
            "id": f"ollama:{name}",
            "provider": "ollama",
            "provider_model_id": name,
            "name": name,
            "status": "review_required",
            "source_url": source_url,
            "source_hash": hashlib.sha256(name.encode("utf-8")).hexdigest(),
            "metadata": {"source_format": "ollama_library_html"},
        }
        for name in names
    ]


def load_offline_provider_payloads(fixture_root: Path) -> list[dict[str, Any]]:
    payload_dir = fixture_root / "provider_payloads"
    if not payload_dir.exists():
        return []
    discoveries: list[dict[str, Any]] = []
    for path in sorted(payload_dir.glob("*.json")):
        provider = path.stem
        payload = json.loads(path.read_text(encoding="utf-8"))
        discoveries.extend(
            normalize_provider_payload(
                provider,
                payload,
                source_url=f"offline-fixture://provider_payloads/{path.name}",
            )
        )
    return discoveries


def fetch_text(url: str, *, headers: dict[str, str] | None = None) -> str:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        raw = response.read()
    return raw.decode("utf-8", "replace")


def fetch_json(url: str, *, headers: dict[str, str] | None = None) -> dict[str, Any] | list[Any]:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def _auth_headers(source: dict[str, Any]) -> dict[str, str]:
    headers = {str(k): str(v) for k, v in source.get("headers", {}).items()}
    env_name = source.get("token_env")
    auth_scheme = source.get("auth_scheme", "Bearer")
    if isinstance(env_name, str) and env_name:
        token = os.environ.get(env_name)
        if token:
            header_name = str(source.get("auth_header", "Authorization"))
            headers[header_name] = f"{auth_scheme} {token}" if auth_scheme else token
    return headers


def fetch_configured_sources(sources_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config = json.loads(sources_path.read_text(encoding="utf-8"))
    discoveries: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for source in config.get("providers", []):
        provider = str(source["id"])
        url = str(source["url"])
        try:
            if source.get("format") == "ollama_library_html":
                html = fetch_text(url, headers=_auth_headers(source))
                discoveries.extend(normalize_ollama_library_html(html, source_url=url))
                continue
            payload = fetch_json(url, headers=_auth_headers(source))
        except (OSError, urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as exc:
            errors.append({"provider": provider, "status": "unavailable", "error": exc.__class__.__name__})
            continue
        discoveries.extend(normalize_provider_payload(provider, payload, source_url=url))
    return discoveries, errors
