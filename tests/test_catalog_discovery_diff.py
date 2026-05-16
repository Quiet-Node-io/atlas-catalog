import unittest

from scripts.catalog_discovery.diff import diff_catalog
from scripts.catalog_discovery.review_state import filter_previously_reviewed


class CatalogDiffTests(unittest.TestCase):
    def test_additions_and_removed_review_candidates_do_not_mutate_catalog(self):
        catalog = {
            "models": [
                {
                    "id": "openai:gpt-existing",
                    "registry": "cloud",
                    "provider": "OpenAI",
                    "provider_model_ref": "gpt-existing",
                    "status": "active",
                }
            ]
        }
        discoveries = [
            {
                "id": "openai:gpt-new",
                "provider": "openai",
                "provider_model_id": "gpt-new",
                "source_hash": "hash-new",
            }
        ]

        result = diff_catalog(catalog, discoveries, scanned_providers={"openai"})

        self.assertEqual([entry["id"] for entry in result["added"]], ["openai:gpt-new"])
        self.assertEqual([entry["id"] for entry in result["removed"]], ["openai:gpt-existing"])
        self.assertEqual(catalog["models"][0]["id"], "openai:gpt-existing")

    def test_review_state_suppresses_previously_ignored_discovery(self):
        discoveries = [
            {"id": "openai:gpt-new", "source_hash": "same-hash"},
            {"id": "openai:gpt-updated", "source_hash": "new-hash"},
        ]
        state = {
            "discoveries": {
                "openai:gpt-new": {"state": "ignored", "source_hash": "same-hash"},
                "openai:gpt-updated": {"state": "ignored", "source_hash": "old-hash"},
            }
        }

        visible = filter_previously_reviewed(discoveries, state)

        self.assertEqual([entry["id"] for entry in visible], ["openai:gpt-updated"])


if __name__ == "__main__":
    unittest.main()
