import json
import tempfile
import unittest
from pathlib import Path

from scripts.catalog_discovery.providers import (
    load_offline_provider_payloads,
    normalize_ollama_library_html,
    normalize_provider_payload,
)


class ProviderNormalizationTests(unittest.TestCase):
    def test_normalizes_provider_model_list_shapes(self):
        openai = normalize_provider_payload(
            "openai",
            {"data": [{"id": "gpt-test-1", "created": 1}]},
            source_url="https://api.openai.com/v1/models",
        )
        anthropic = normalize_provider_payload(
            "anthropic",
            {"data": [{"id": "claude-test-1", "display_name": "Claude Test"}]},
            source_url="https://api.anthropic.com/v1/models",
        )
        gemini = normalize_provider_payload(
            "google",
            {"models": [{"name": "models/gemini-test", "displayName": "Gemini Test"}]},
            source_url="https://generativelanguage.googleapis.com/v1beta/models",
        )

        self.assertEqual(openai[0]["id"], "openai:gpt-test-1")
        self.assertEqual(openai[0]["provider_model_id"], "gpt-test-1")
        self.assertEqual(anthropic[0]["name"], "Claude Test")
        self.assertEqual(gemini[0]["provider_model_id"], "gemini-test")
        self.assertTrue(all(item["status"] == "review_required" for item in openai + anthropic + gemini))

    def test_loads_offline_fixture_payloads_and_normalizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture_root = Path(tmp)
            payload_dir = fixture_root / "provider_payloads"
            payload_dir.mkdir()
            (payload_dir / "huggingface.json").write_text(
                json.dumps(
                    {
                        "models": [
                            {
                                "id": "org/model-a",
                                "downloads": 10,
                                "likes": 5,
                                "pipeline_tag": "text-generation",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            discoveries = load_offline_provider_payloads(fixture_root)

        self.assertEqual(len(discoveries), 1)
        self.assertEqual(discoveries[0]["id"], "huggingface:org/model-a")
        self.assertEqual(discoveries[0]["metadata"]["pipeline_tag"], "text-generation")

    def test_normalizes_ollama_library_html_links(self):
        discoveries = normalize_ollama_library_html(
            '<a href="/library/gemma3">Gemma 3</a><a href="/library/qwen3:8b">Qwen 3 8B</a>',
            source_url="https://ollama.com/library",
        )

        self.assertEqual([entry["id"] for entry in discoveries], ["ollama:gemma3", "ollama:qwen3:8b"])
        self.assertEqual(discoveries[0]["provider"], "ollama")


if __name__ == "__main__":
    unittest.main()
