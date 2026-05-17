import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_catalog import validate_catalog


BACKEND_FEATURES = {
    "supports_streaming": True,
    "supports_non_streaming": True,
    "supports_embeddings": False,
    "supports_vision": False,
    "supports_json_mode": True,
    "supports_function_calling": True,
    "supports_continuous_batching": False,
    "max_batch_size": 1,
    "supports_kv_cache_control": False,
    "supported_sampling_params": ["temperature", "top_p", "max_tokens", "stop"],
    "supports_unload": False,
    "supports_model_survey": True,
    "auth_mode": "api_key",
    "supports_leases": False,
}


def _catalog_payload(**overrides):
    payload = {
        "catalog_version": 4,
        "updated": "2026-05-17",
        "backends": [
            {
                "backend_id": "openai",
                "version_range": "api-current",
                "features": dict(BACKEND_FEATURES),
                "notes": "Cloud provider exposed through Atlas's LiteLLM-backed cloud adapter.",
                "provenance": {
                    field: [
                        {
                            "source_kind": "atlas_source",
                            "source_url": "https://github.com/Quiet-Node-io/atlas/blob/main/src/inference/backends/cloud.py",
                            "retrieved_at": "2026-05-17T00:00:00+00:00",
                        }
                    ]
                    for field in BACKEND_FEATURES
                },
            }
        ],
        "models": [{"id": "openai:gpt-test", "variant": "standard", "backend_id": "openai"}],
        "task_benchmark_weights": {"research_analysis": {"mmlu_pro": 1.0}},
    }
    payload.update(overrides)
    return payload


def _validate(payload):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "catalog.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return validate_catalog(path)


class BackendInventorySchemaTests(unittest.TestCase):
    def test_accepts_well_formed_backend_inventory_and_model_reference(self):
        self.assertEqual(_validate(_catalog_payload()), [])

    def test_rejects_malformed_backend_entries(self):
        payload = _catalog_payload(
            backends=[
                {
                    "backend_id": "openai",
                    "version_range": "",
                    "features": {"supports_streaming": True},
                    "notes": "",
                }
            ]
        )

        errors = _validate(payload)

        self.assertIn("backends[0]: version_range must be a non-empty string", errors)
        self.assertIn("backends[0]: notes must be a non-empty string", errors)
        self.assertIn("backends[0].features: missing supports_non_streaming", errors)
        self.assertIn("backends[0].features: missing supported_sampling_params", errors)

    def test_rejects_model_backend_reference_when_backend_id_is_unknown(self):
        payload = _catalog_payload(models=[{"id": "local:test", "variant": "standard", "backend_id": "missing"}])

        errors = _validate(payload)

        self.assertIn("local:test: backend_id references unknown backend missing", errors)

    def test_rejects_backend_composite_score_for_unknown_catalog_backend(self):
        payload = _catalog_payload(
            models=[
                {
                    "id": "openai:gpt-test",
                    "variant": "standard",
                    "benchmarks_meta": {},
                    "backend_composite_scores": [
                        {
                            "model_id": "openai:gpt-test",
                            "backend": "missing",
                            "node_class": "cloud",
                            "hardware_class": "unknown",
                            "quantization": "unknown",
                            "context_tokens": 128000,
                            "modality": "text",
                            "task_id": "research_analysis",
                            "score": 80,
                            "coverage": 0.5,
                            "components": {
                                "backend_capability": {
                                    "score": 1.0,
                                    "weight": 0.25,
                                    "source_url": "https://example.com/backend-profile",
                                    "retrieved_at": "2026-05-17T00:00:00+00:00",
                                }
                            },
                        }
                    ],
                }
            ]
        )

        errors = _validate(payload)

        self.assertIn("openai:gpt-test backend_composite_scores[0]: unknown backend missing", errors)


if __name__ == "__main__":
    unittest.main()
