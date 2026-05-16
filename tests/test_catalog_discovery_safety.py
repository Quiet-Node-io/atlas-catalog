import json
import tempfile
import unittest
from pathlib import Path

from scripts.catalog_discovery.safety import evaluate_catalog_publish


class SafetyGuardTests(unittest.TestCase):
    def test_blocks_destructive_changes_without_override(self):
        base = {
            "models": [
                {"id": "openai:gpt-existing", "default": True, "status": "active", "registry": "cloud"}
            ]
        }
        proposed = {"models": []}

        result = evaluate_catalog_publish(base, proposed)

        self.assertFalse(result.allowed)
        self.assertTrue(any("removed" in issue for issue in result.issues))

    def test_explicit_override_allows_destructive_changes_and_reports_it(self):
        base = {"models": [{"id": "openai:gpt-existing", "default": True, "registry": "cloud"}]}
        proposed = {"models": []}

        result = evaluate_catalog_publish(base, proposed, allow_destructive=True)

        self.assertTrue(result.allowed)
        self.assertTrue(result.override_used)

    def test_requires_evidence_for_added_rows(self):
        base = {"models": []}
        proposed = {"models": [{"id": "openai:gpt-new", "registry": "cloud"}]}

        result = evaluate_catalog_publish(base, proposed)

        self.assertFalse(result.allowed)
        self.assertTrue(any("missing discovery evidence" in issue for issue in result.issues))

    def test_safety_result_can_be_written_as_json(self):
        base = {"models": [{"id": "openai:gpt-existing", "registry": "cloud"}]}
        proposed = {"models": []}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            result = evaluate_catalog_publish(base, proposed)
            path.write_text(json.dumps(result.to_dict()), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))

        self.assertFalse(loaded["allowed"])

    def test_catalog_discovery_workflow_creates_draft_prs_only(self):
        workflow = Path(".github/workflows/catalog-discovery.yml").read_text(encoding="utf-8")

        self.assertIn("draft: true", workflow)
        self.assertNotIn("draft: false", workflow)


if __name__ == "__main__":
    unittest.main()
