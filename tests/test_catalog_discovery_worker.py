import json
import tempfile
import unittest
from pathlib import Path

from scripts.catalog_discovery.__main__ import run_discovery


class WorkerIntegrationTests(unittest.TestCase):
    def test_offline_run_writes_review_artifacts_and_proposed_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture_root = root / "fixtures"
            output = root / "out"
            provider_dir = fixture_root / "provider_payloads"
            research_dir = fixture_root / "research_payloads"
            provider_dir.mkdir(parents=True)
            research_dir.mkdir(parents=True)
            catalog = {
                "catalog_version": 4,
                "updated": "2026-05-16",
                "models": [],
                "task_benchmark_weights": {"research_analysis": {"mmlu_pro": 1.0}},
            }
            catalog_path = root / "catalog.json"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            (provider_dir / "openai.json").write_text(
                json.dumps({"data": [{"id": "gpt-new"}]}),
                encoding="utf-8",
            )
            (provider_dir / "huggingface.json").write_text(
                json.dumps([{"id": "org/model-a"}]),
                encoding="utf-8",
            )
            (research_dir / "openai_gpt-new.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "kind": "huggingface_leaderboard",
                                "url": "https://huggingface.co/spaces/test",
                                "retrieved_at": "2026-05-16T00:00:00+00:00",
                                "benchmarks": {
                                    "mmlu_pro": {
                                        "value": 0.82,
                                        "source_url": "https://huggingface.co/spaces/test",
                                    }
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_discovery(
                catalog_path=catalog_path,
                output_dir=output,
                offline_fixtures=fixture_root,
                create_pr=False,
            )

            self.assertEqual(result["summary"]["added"], 2)
            proposed = json.loads((output / "proposed-catalog.json").read_text(encoding="utf-8"))
            by_id = {row["id"]: row for row in proposed["models"]}
            self.assertIn("openai:gpt-new", by_id)
            self.assertIn("huggingface:org/model-a", by_id)
            self.assertEqual(by_id["openai:gpt-new"]["benchmarks"]["mmlu_pro"], 0.82)
            self.assertEqual(
                by_id["openai:gpt-new"]["benchmarks_meta"]["mmlu_pro"]["source_url"],
                "https://huggingface.co/spaces/test",
            )
            self.assertEqual(
                by_id["openai:gpt-new"]["benchmarks_meta"]["mmlu_pro"]["retrieved_at"],
                "2026-05-16T00:00:00+00:00",
            )
            self.assertIsNone(by_id["huggingface:org/model-a"]["benchmarks"]["mmlu_pro"])
            self.assertEqual(
                by_id["huggingface:org/model-a"]["benchmarks_meta"]["mmlu_pro"]["missing_reason"],
                "not_publicly_reported",
            )
            self.assertIn("discovery_evidence", by_id["openai:gpt-new"])
            self.assertTrue((output / "catalog-review-report.md").exists())
            self.assertTrue((output / "manifest.json").exists())
            self.assertTrue((output / "provider-evidence" / "discoveries.json").exists())


if __name__ == "__main__":
    unittest.main()
