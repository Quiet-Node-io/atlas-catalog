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
            (research_dir / "openai_gpt-new.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "kind": "huggingface_leaderboard",
                                "url": "https://huggingface.co/spaces/test",
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

            self.assertEqual(result["summary"]["added"], 1)
            proposed = json.loads((output / "proposed-catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(proposed["models"][0]["id"], "openai:gpt-new")
            self.assertIn("discovery_evidence", proposed["models"][0])
            self.assertTrue((output / "catalog-review-report.md").exists())
            self.assertTrue((output / "manifest.json").exists())
            self.assertTrue((output / "provider-evidence" / "discoveries.json").exists())


if __name__ == "__main__":
    unittest.main()
