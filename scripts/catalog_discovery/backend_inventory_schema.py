"""Validation helpers for top-level backend feature inventory records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

FEATURE_FIELDS = (
    "supports_streaming",
    "supports_non_streaming",
    "supports_embeddings",
    "supports_vision",
    "supports_json_mode",
    "supports_function_calling",
    "supports_continuous_batching",
    "max_batch_size",
    "supports_kv_cache_control",
    "supported_sampling_params",
    "supports_unload",
    "supports_model_survey",
    "auth_mode",
    "supports_leases",
)

BOOLEAN_FEATURE_FIELDS = {
    "supports_streaming",
    "supports_non_streaming",
    "supports_embeddings",
    "supports_vision",
    "supports_json_mode",
    "supports_function_calling",
    "supports_continuous_batching",
    "supports_kv_cache_control",
    "supports_unload",
    "supports_model_survey",
    "supports_leases",
}

KNOWN_AUTH_MODES = {"none", "backend_native", "api_key", "proxy_token", "mtls"}

KNOWN_SAMPLING_PARAMS = {
    "temperature",
    "top_p",
    "top_k",
    "repeat_penalty",
    "max_tokens",
    "stop",
    "seed",
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


def _validate_provenance(
    provenance: Any,
    *,
    backend_id: str,
    feature_fields: set[str],
) -> list[str]:
    prefix = f"{backend_id}.provenance"
    if provenance is None:
        return [f"{backend_id}: provenance is required for backend feature flags"]
    if not isinstance(provenance, dict):
        return [f"{prefix}: must be an object keyed by feature field"]

    errors: list[str] = []
    if "sources" in provenance or "feature_flags" in provenance:
        sources = provenance.get("sources")
        feature_flags = provenance.get("feature_flags")
        if not isinstance(sources, dict) or not sources:
            errors.append(f"{prefix}.sources: must be a non-empty object")
            sources = {}
        if not isinstance(feature_flags, dict):
            errors.append(f"{prefix}.feature_flags: must be an object keyed by feature field")
            feature_flags = {}

        for source_id, source in sources.items():
            source_prefix = f"{prefix}.sources.{source_id}"
            if not _nonempty_string(source_id):
                errors.append(f"{prefix}.sources: source id must be a non-empty string")
            if not isinstance(source, dict):
                errors.append(f"{source_prefix}: source must be an object")
                continue
            if not _nonempty_string(source.get("source_url")):
                errors.append(f"{source_prefix}: source_url must be a non-empty string")
            if not _valid_timestamp(source.get("retrieved_at")):
                errors.append(f"{source_prefix}: retrieved_at must be a valid ISO timestamp")
            if not _nonempty_string(source.get("source_kind")):
                errors.append(f"{source_prefix}: source_kind must be a non-empty string")

        for field in feature_fields:
            refs = feature_flags.get(field)
            field_prefix = f"{prefix}.feature_flags.{field}"
            if not isinstance(refs, list) or not refs:
                errors.append(f"{field_prefix}: must cite at least one source")
                continue
            for ref in refs:
                if ref not in sources:
                    errors.append(f"{field_prefix}: unknown source reference {ref}")
        for field in feature_flags:
            if field not in feature_fields:
                errors.append(f"{prefix}.feature_flags: unknown feature provenance {field}")
        for field in provenance:
            if field not in {"sources", "feature_flags"}:
                errors.append(f"{prefix}: unknown provenance key {field}")
        return errors

    for field in feature_fields:
        entries = provenance.get(field)
        field_prefix = f"{prefix}.{field}"
        if not isinstance(entries, list) or not entries:
            errors.append(f"{field_prefix}: must cite at least one source")
            continue
        for index, entry in enumerate(entries):
            entry_prefix = f"{field_prefix}[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{entry_prefix}: source must be an object")
                continue
            if not _nonempty_string(entry.get("source_url")):
                errors.append(f"{entry_prefix}: source_url must be a non-empty string")
            if not _valid_timestamp(entry.get("retrieved_at")):
                errors.append(f"{entry_prefix}: retrieved_at must be a valid ISO timestamp")
            if not _nonempty_string(entry.get("source_kind")):
                errors.append(f"{entry_prefix}: source_kind must be a non-empty string")

    for field in provenance:
        if field not in feature_fields:
            errors.append(f"{prefix}: unknown feature provenance {field}")
    return errors


def validate_backend_inventory(payload: dict[str, Any]) -> tuple[set[str], list[str]]:
    """Validate top-level ``backends`` entries and return known backend IDs."""

    records = payload.get("backends")
    if records is None:
        return set(), []
    if not isinstance(records, list):
        return set(), ["catalog.json backends must be an array"]

    errors: list[str] = []
    backend_ids: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"backends[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix}: backend entry must be an object")
            continue

        backend_id = record.get("backend_id")
        if not _nonempty_string(backend_id):
            errors.append(f"{prefix}: backend_id must be a non-empty string")
            backend_id_str = prefix
        else:
            backend_id_str = str(backend_id)
            if backend_id_str in backend_ids:
                errors.append(f"{prefix}: duplicate backend_id {backend_id_str}")
            backend_ids.add(backend_id_str)

        if not _nonempty_string(record.get("version_range")):
            errors.append(f"{prefix}: version_range must be a non-empty string")
        if not _nonempty_string(record.get("notes")):
            errors.append(f"{prefix}: notes must be a non-empty string")

        features = record.get("features")
        if not isinstance(features, dict):
            errors.append(f"{prefix}: features must be an object")
            continue

        feature_keys = set(features)
        required_fields = set(FEATURE_FIELDS)
        for field in FEATURE_FIELDS:
            if field not in features:
                errors.append(f"{prefix}.features: missing {field}")
        for field in sorted(feature_keys - required_fields):
            errors.append(f"{prefix}.features: unknown {field}")

        for field in BOOLEAN_FEATURE_FIELDS:
            if field in features and not isinstance(features[field], bool):
                errors.append(f"{prefix}.features.{field}: must be a boolean")

        max_batch_size = features.get("max_batch_size")
        if max_batch_size is not None and (
            isinstance(max_batch_size, bool)
            or not isinstance(max_batch_size, int)
            or max_batch_size < 1
        ):
            errors.append(f"{prefix}.features.max_batch_size: must be a positive integer or null")

        sampling_params = features.get("supported_sampling_params")
        if not isinstance(sampling_params, list):
            errors.append(f"{prefix}.features.supported_sampling_params: must be an array")
        else:
            seen_sampling_params: set[str] = set()
            for value in sampling_params:
                if value not in KNOWN_SAMPLING_PARAMS:
                    errors.append(
                        f"{prefix}.features.supported_sampling_params: unknown sampling param {value}"
                    )
                    continue
                if value in seen_sampling_params:
                    errors.append(
                        f"{prefix}.features.supported_sampling_params: duplicate sampling param {value}"
                    )
                seen_sampling_params.add(str(value))

        auth_mode = features.get("auth_mode")
        if auth_mode not in KNOWN_AUTH_MODES:
            errors.append(f"{prefix}.features.auth_mode: unknown auth_mode {auth_mode}")

        errors.extend(
            _validate_provenance(
                record.get("provenance"),
                backend_id=backend_id_str,
                feature_fields=required_fields,
            )
        )

    return backend_ids, errors
