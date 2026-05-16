import json
import tempfile
import unittest
from pathlib import Path

from scripts.catalog_discovery.research import collect_research_for_model


class ResearchAggregationTests(unittest.TestCase):
    def test_collects_cited_metrics_from_multiple_sources_and_bounds_notes(self):
        discovery = {"id": "openai:gpt-new", "provider_model_id": "gpt-new"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            research_dir = root / "research_payloads"
            research_dir.mkdir()
            (research_dir / "openai_gpt-new.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "kind": "huggingface_leaderboard",
                                "url": "https://huggingface.co/spaces/test",
                                "benchmarks": {
                                    "mmlu_pro": {"value": 0.82, "source_url": "https://hf.example/mmlu"}
                                },
                            },
                            {
                                "kind": "artificial_analysis",
                                "url": "https://artificialanalysis.ai/models/gpt-new",
                                "benchmarks": {
                                    "speed_score": {"value": 0.7, "source_url": "https://aa.example/speed"},
                                    "made_up_metric": {"value": 1.0, "source_url": "https://aa.example/bad"},
                                },
                            },
                            {
                                "kind": "project_readme",
                                "url": "https://example.com/readme",
                                "text": "x" * 2000,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            research = collect_research_for_model(discovery, root, {"mmlu_pro", "speed_score"})

        self.assertEqual(research["benchmarks"]["mmlu_pro"]["value"], 0.82)
        self.assertEqual(research["benchmarks"]["speed_score"]["value"], 0.7)
        self.assertNotIn("made_up_metric", research["benchmarks"])
        self.assertEqual(len(research["sources"]), 3)
        self.assertLessEqual(len(research["sources"][2]["snippet"]), 520)

    def test_uncited_metric_is_not_recorded(self):
        discovery = {"id": "openai:gpt-new", "provider_model_id": "gpt-new"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            research_dir = root / "research_payloads"
            research_dir.mkdir()
            (research_dir / "openai_gpt-new.json").write_text(
                json.dumps({"sources": [{"benchmarks": {"mmlu_pro": {"value": 0.8}}}]}),
                encoding="utf-8",
            )

            research = collect_research_for_model(discovery, root, {"mmlu_pro"})

        self.assertEqual(research["benchmarks"], {})


if __name__ == "__main__":
    unittest.main()
