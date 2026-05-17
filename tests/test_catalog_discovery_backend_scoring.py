import unittest

from scripts.catalog_discovery.backend_score_schema import validate_backend_composite_scores
from scripts.catalog_discovery.backend_scoring import build_backend_composite_scores


class BackendCompositeScoringTests(unittest.TestCase):
    def test_builds_tuple_keyed_scores_from_benchmarks_and_backend_profile(self):
        scores = build_backend_composite_scores(
            model_id="openai:gpt-new",
            benchmarks={"mmlu_pro": {"value": 0.8}, "gpqa_diamond": {"value": 0.6}},
            benchmarks_meta={
                "mmlu_pro": {
                    "source_url": "https://hf.example/mmlu",
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                    "source_kind": "huggingface_leaderboard",
                },
                "gpqa_diamond": {
                    "source_url": "https://aa.example/gpqa",
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                    "source_kind": "artificial_analysis",
                },
            },
            task_benchmark_weights={"research_analysis": {"mmlu_pro": 0.6, "gpqa_diamond": 0.4}},
            backend_profiles=[
                {
                    "backend": "ollama",
                    "node_class": "local",
                    "hardware_class": "standard",
                    "quantization": "Q4_K_M",
                    "context_tokens": 32768,
                    "modality": "text",
                    "source_url": "https://example.com/backend-profile",
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                    "features": {
                        "continuous_batching": True,
                        "kv_cache_control": "explicit",
                        "sampling_param_support": ["temperature", "top_p", "top_k"],
                        "structured_output": True,
                        "tool_support": True,
                    },
                    "runtime_profile": {
                        "throughput_score": 0.7,
                        "ttft_score": 0.8,
                        "memory_pressure_score": 0.6,
                    },
                }
            ],
        )

        self.assertEqual(len(scores), 1)
        score = scores[0]
        self.assertEqual(score["model_id"], "openai:gpt-new")
        self.assertEqual(score["backend"], "ollama")
        self.assertEqual(score["node_class"], "local")
        self.assertEqual(score["hardware_class"], "standard")
        self.assertEqual(score["quantization"], "Q4_K_M")
        self.assertEqual(score["context_tokens"], 32768)
        self.assertEqual(score["modality"], "text")
        self.assertEqual(score["task_id"], "research_analysis")
        self.assertGreaterEqual(score["score"], 0)
        self.assertLessEqual(score["score"], 100)
        self.assertEqual(score["coverage"], 1.0)
        self.assertEqual(
            score["components"]["benchmark_composite"]["provenance"],
            ["benchmarks_meta.mmlu_pro", "benchmarks_meta.gpqa_diamond"],
        )
        self.assertEqual(
            set(score["components"]["backend_capability"]["features"]),
            {
                "continuous_batching",
                "kv_cache_control",
                "sampling_param_support",
                "structured_output",
                "tool_support",
            },
        )

    def test_missing_backend_facts_reduce_coverage_without_guessing(self):
        scores = build_backend_composite_scores(
            model_id="openai:gpt-new",
            benchmarks={"mmlu_pro": {"value": 0.8}},
            benchmarks_meta={
                "mmlu_pro": {
                    "source_url": "https://hf.example/mmlu",
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                    "source_kind": "huggingface_leaderboard",
                }
            },
            task_benchmark_weights={"research_analysis": {"mmlu_pro": 1.0}},
            backend_profiles=[
                {
                    "backend": "mlx_lm",
                    "node_class": "local",
                    "hardware_class": "performance",
                    "quantization": "BF16",
                    "context_tokens": 65536,
                    "modality": "text",
                }
            ],
        )

        score = scores[0]
        self.assertLess(score["coverage"], 1.0)
        self.assertIn("backend_capability", score["components"])
        self.assertEqual(
            score["components"]["backend_capability"]["missing_reason"],
            "backend_features_not_reported",
        )
        self.assertNotIn("score", score["components"]["backend_capability"])

    def test_validator_rejects_unknown_tuple_values_and_bad_provenance(self):
        row = {
            "id": "openai:gpt-new",
            "benchmarks": {"mmlu_pro": 0.82},
            "benchmarks_meta": {
                "mmlu_pro": {
                    "source_url": "https://hf.example/mmlu",
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                    "source_kind": "huggingface_leaderboard",
                }
            },
            "backend_composite_scores": [
                {
                    "model_id": "openai:gpt-new",
                    "backend": "made_up_backend",
                    "node_class": "laptop",
                    "hardware_class": "giant",
                    "quantization": "Q4_K_M",
                    "context_tokens": 32768,
                    "modality": "text",
                    "task_id": "research_analysis",
                    "score": 101,
                    "coverage": 1.2,
                    "components": {
                        "benchmark_composite": {
                            "score": 0.8,
                            "weight": 0.6,
                            "provenance": ["benchmarks_meta.not_here"],
                        }
                    },
                }
            ],
        }

        errors = validate_backend_composite_scores(
            row,
            task_ids={"research_analysis"},
        )

        self.assertIn("openai:gpt-new backend_composite_scores[0]: unknown backend made_up_backend", errors)
        self.assertIn("openai:gpt-new backend_composite_scores[0]: unknown node_class laptop", errors)
        self.assertIn("openai:gpt-new backend_composite_scores[0]: unknown hardware_class giant", errors)
        self.assertIn("openai:gpt-new backend_composite_scores[0]: score must be 0-100", errors)
        self.assertIn("openai:gpt-new backend_composite_scores[0]: coverage must be 0-1", errors)
        self.assertIn(
            "openai:gpt-new backend_composite_scores[0].components.benchmark_composite: provenance benchmarks_meta.not_here missing from benchmarks_meta",
            errors,
        )

    def test_validator_accepts_generated_score_records(self):
        row = {
            "id": "openai:gpt-new",
            "benchmarks": {"mmlu_pro": 0.82},
            "benchmarks_meta": {
                "mmlu_pro": {
                    "source_url": "https://hf.example/mmlu",
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                    "source_kind": "huggingface_leaderboard",
                }
            },
            "backend_composite_scores": build_backend_composite_scores(
                model_id="openai:gpt-new",
                benchmarks={"mmlu_pro": {"value": 0.82}},
                benchmarks_meta={
                    "mmlu_pro": {
                        "source_url": "https://hf.example/mmlu",
                        "retrieved_at": "2026-05-16T00:00:00+00:00",
                        "source_kind": "huggingface_leaderboard",
                    }
                },
                task_benchmark_weights={"research_analysis": {"mmlu_pro": 1.0}},
                backend_profiles=[
                    {
                        "backend": "openai",
                        "node_class": "cloud",
                        "hardware_class": "unknown",
                        "quantization": "unknown",
                        "context_tokens": 128000,
                        "modality": "text",
                        "source_url": "https://example.com/backend-profile",
                        "retrieved_at": "2026-05-16T00:00:00+00:00",
                        "features": {"structured_output": True, "tool_support": True},
                    }
                ],
            ),
        }

        self.assertEqual(
            validate_backend_composite_scores(row, task_ids={"research_analysis"}),
            [],
        )


if __name__ == "__main__":
    unittest.main()
