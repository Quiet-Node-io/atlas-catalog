import unittest

from scripts.catalog_discovery.benchmark_provenance import validate_benchmark_provenance


class BenchmarkProvenanceTests(unittest.TestCase):
    def test_accepts_flat_values_with_adjacent_metadata(self):
        row = {
            "id": "openai:gpt-new",
            "benchmarks": {"mmlu_pro": 0.82, "gpqa_diamond": None},
            "benchmarks_meta": {
                "mmlu_pro": {
                    "source_url": "https://huggingface.co/spaces/test",
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                    "source_kind": "huggingface_leaderboard",
                },
                "gpqa_diamond": {
                    "source_url": None,
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                    "missing_reason": "not_publicly_reported",
                },
            },
        }

        self.assertEqual(validate_benchmark_provenance(row), [])

    def test_rejects_numeric_value_without_citation_metadata(self):
        row = {
            "id": "openai:gpt-new",
            "benchmarks": {"mmlu_pro": 0.82},
            "benchmarks_meta": {},
        }

        errors = validate_benchmark_provenance(row)

        self.assertIn("openai:gpt-new: mmlu_pro missing benchmarks_meta", errors)

    def test_rejects_null_value_without_missing_reason(self):
        row = {
            "id": "openai:gpt-new",
            "benchmarks": {"gpqa_diamond": None},
            "benchmarks_meta": {
                "gpqa_diamond": {
                    "source_url": None,
                    "retrieved_at": "2026-05-16T00:00:00+00:00",
                }
            },
        }

        errors = validate_benchmark_provenance(row)

        self.assertIn("openai:gpt-new: gpqa_diamond null value missing missing_reason", errors)


if __name__ == "__main__":
    unittest.main()
