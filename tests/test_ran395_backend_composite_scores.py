import json
import unittest
from pathlib import Path

from scripts.catalog_discovery.backend_score_schema import validate_backend_composite_scores


CATALOG_PATH = Path(__file__).resolve().parents[1] / "catalog.json"


EXPECTED_TUPLES = {
    "gemma4:4.5b": {
        ("ollama", "local", "performance", "Q4_K_M", "vision_input"),
        ("mlx_lm", "local", "performance", "Q4_K_M", "vision_input"),
    },
    "gemma4:e4b-it-q8_0": {
        ("ollama", "local", "performance", "Q8_0", "vision_input"),
        ("mlx_lm", "local", "performance", "Q8_0", "vision_input"),
    },
    "gemma4:e4b-it-bf16": {
        ("ollama", "local", "performance", "BF16", "vision_input"),
        ("mlx_lm", "local", "performance", "BF16", "vision_input"),
    },
    "gemma4:31b": {
        ("ollama", "local", "performance", "Q4_K_M", "vision_input"),
        ("mlx_lm", "local", "performance", "Q4_K_M", "vision_input"),
    },
    "gemma4:31b-it-q8_0": {
        ("ollama", "local", "performance", "Q8_0", "vision_input"),
        ("mlx_lm", "local", "performance", "Q8_0", "vision_input"),
    },
    "bge-m3:f16": {
        ("ollama", "local", "performance", "F16", "data_parsing"),
    },
    "gpustack/bge-reranker-v2-m3-GGUF:q4_k_m": {
        ("llama_cpp_server", "local", "performance", "Q4_K_M", "data_parsing"),
    },
    "mradermacher/bge-reranker-v2-gemma-GGUF:q4_k_m": {
        ("llama_cpp_server", "local", "performance", "Q4_K_M", "data_parsing"),
    },
    "mradermacher/bge-reranker-v2-gemma-GGUF:q8_0": {
        ("llama_cpp_server", "local", "performance", "Q8_0", "data_parsing"),
    },
    "deepseek-r1:70b": {
        ("ollama", "local", "high_performance", "Q4_K_M", "research_analysis"),
        ("vllm", "cluster", "high_performance", "Q4_K_M", "research_analysis"),
    },
    "qwen2.5-coder:32b": {
        ("ollama", "local", "high_performance", "Q4_K_M", "code_generation"),
        ("vllm", "cluster", "high_performance", "Q4_K_M", "code_generation"),
    },
    "llama3.2-vision:11b": {
        ("ollama", "local", "performance", "Q4_K_M", "vision_input"),
    },
    "gpt-5.4-mini": {
        ("openai", "cloud", "unknown", "unknown", "vision_input"),
    },
    "claude-haiku-4-5-20251001": {
        ("anthropic", "cloud", "unknown", "unknown", "vision_input"),
    },
    "gemini-2.5-flash-lite": {
        ("google", "cloud", "unknown", "unknown", "vision_input"),
    },
    "grok-4-1-fast-non-reasoning": {
        ("xai", "cloud", "unknown", "unknown", "vision_input"),
    },
}

GEMMA4_VISION_BENCHMARKS = {
    "gemma4:e2b": {
        "mmmu": 0.442,
        "mmmu_pro": 0.442,
        "math_vision": 0.524,
        "medxpertqa_mm": 0.235,
    },
    "gemma4:4.5b": {
        "mmmu": 0.526,
        "mmmu_pro": 0.526,
        "math_vision": 0.595,
        "medxpertqa_mm": 0.287,
    },
    "gemma4:26b": {
        "mmmu": 0.738,
        "mmmu_pro": 0.738,
        "math_vision": 0.824,
        "medxpertqa_mm": 0.581,
    },
    "gemma4:31b": {
        "mmmu": 0.769,
        "mmmu_pro": 0.769,
        "math_vision": 0.856,
        "medxpertqa_mm": 0.613,
    },
}

GEMMA4_UNMEASURED_VISION_BENCHMARKS = {
    "ai2d",
    "docvqa",
    "chartqa",
    "mathvista",
    "omnidocbench_1_5",
}


class RAN395BackendCompositeScoresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.rows = {row["id"]: row for row in cls.catalog["models"]}
        cls.task_ids = set(cls.catalog["task_benchmark_weights"])
        cls.backend_ids = {backend["backend_id"] for backend in cls.catalog["backends"]}

    def test_target_models_have_required_backend_score_tuples(self):
        for model_id, expected_tuples in EXPECTED_TUPLES.items():
            with self.subTest(model_id=model_id):
                records = self.rows[model_id].get("backend_composite_scores")
                self.assertIsInstance(records, list)
                actual_tuples = {
                    (
                        record["backend"],
                        record["node_class"],
                        record["hardware_class"],
                        record["quantization"],
                        record["task_id"],
                    )
                    for record in records
                }
                self.assertEqual(expected_tuples, actual_tuples)

    def test_backend_score_records_are_unique_and_valid(self):
        for model_id in EXPECTED_TUPLES:
            with self.subTest(model_id=model_id):
                row = self.rows[model_id]
                records = row["backend_composite_scores"]
                tuple_keys = [
                    (
                        record["backend"],
                        record["node_class"],
                        record["hardware_class"],
                        record["quantization"],
                        record["task_id"],
                    )
                    for record in records
                ]
                self.assertEqual(len(tuple_keys), len(set(tuple_keys)))
                self.assertEqual(
                    validate_backend_composite_scores(
                        row,
                        known_backends=self.backend_ids,
                        task_ids=self.task_ids,
                    ),
                    [],
                )

    def test_every_component_is_scored_with_provenance_or_missing_reason(self):
        for model_id in EXPECTED_TUPLES:
            for record in self.rows[model_id]["backend_composite_scores"]:
                with self.subTest(model_id=model_id, backend=record["backend"]):
                    self.assertIsInstance(record["score"], int)
                    self.assertGreaterEqual(record["score"], 0)
                    self.assertLessEqual(record["score"], 100)
                    self.assertGreater(record["coverage"], 0)
                    self.assertLessEqual(record["coverage"], 1)
                    self.assertGreater(record["context_tokens"], 0)

                    components = record["components"]
                    self.assertEqual(
                        {"benchmark_composite", "backend_capability", "runtime_profile"},
                        set(components),
                    )
                    for component_name, component in components.items():
                        self.assertIn("weight", component)
                        if "score" in component:
                            self.assertGreaterEqual(component["score"], 0)
                            self.assertLessEqual(component["score"], 1)
                            if component_name == "benchmark_composite":
                                self.assertTrue(component["provenance"])
                                self.assertTrue(
                                    all(
                                        reference.startswith("benchmarks_meta.")
                                        for reference in component["provenance"]
                                    )
                                )
                            else:
                                self.assertIn("https://", component["source_url"])
                                self.assertIn("retrieved_at", component)
                        else:
                            self.assertIn("missing_reason", component)

    def test_llama_vision_benchmark_component_uses_existing_benchmark_meta(self):
        row = self.rows["llama3.2-vision:11b"]
        self.assertTrue(row.get("benchmarks_meta"))
        record = row["backend_composite_scores"][0]
        benchmark_component = record["components"]["benchmark_composite"]
        self.assertEqual(
            [
                "benchmarks_meta.mmmu",
                "benchmarks_meta.ai2d",
                "benchmarks_meta.chartqa",
                "benchmarks_meta.docvqa",
                "benchmarks_meta.mathvista",
            ],
            benchmark_component["provenance"],
        )
        self.assertEqual(0.7106, benchmark_component["score"])
        self.assertEqual(62, record["score"])
        self.assertEqual(0.85, record["coverage"])

    def test_gemma4_family_has_vision_support_and_cited_benchmark_metadata(self):
        for model_id, expected in GEMMA4_VISION_BENCHMARKS.items():
            with self.subTest(model_id=model_id):
                row = self.rows[model_id]
                self.assertIs(row.get("has_vision"), True)
                self.assertIs(row.get("supports_vision"), True)

                benchmarks = row.get("benchmarks")
                meta = row.get("benchmarks_meta")
                self.assertIsInstance(benchmarks, dict)
                self.assertIsInstance(meta, dict)

                for metric, value in expected.items():
                    self.assertEqual(value, benchmarks.get(metric))
                    self.assertEqual(
                        "official_model_card",
                        meta[metric]["source_kind"],
                    )
                    self.assertIn(
                        "ai.google.dev/gemma/docs/core/model_card_4",
                        meta[metric]["source_url"],
                    )

                for metric in GEMMA4_UNMEASURED_VISION_BENCHMARKS:
                    self.assertIsNone(benchmarks.get(metric))
                    expected_reason = (
                        "lower_is_better_transform_pending"
                        if metric == "omnidocbench_1_5"
                        else "not_publicly_reported"
                    )
                    if metric == "mathvista":
                        expected_reason = "proxy_rejected_not_equivalent_to_math_vision"
                    self.assertEqual(expected_reason, meta[metric]["missing_reason"])

    def test_gemma4_backend_composite_uses_only_approved_mmmu_proxy(self):
        for model_id, expected in GEMMA4_VISION_BENCHMARKS.items():
            with self.subTest(model_id=model_id):
                row = self.rows[model_id]
                record = next(
                    record
                    for record in row["backend_composite_scores"]
                    if record["backend"] == "ollama" and record["task_id"] == "vision_input"
                )
                component = record["components"]["benchmark_composite"]
                self.assertEqual(expected["mmmu"], component["score"])
                self.assertEqual(["benchmarks_meta.mmmu"], component["provenance"])


if __name__ == "__main__":
    unittest.main()
