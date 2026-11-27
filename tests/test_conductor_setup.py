"""Repository context and historical catalogue conservation checks."""
import json
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONDUCTOR = ROOT / "conductor"


class ConductorSetupTests(unittest.TestCase):
    def test_setup_artifacts_and_links(self):
        index = (CONDUCTOR / "index.md").read_text(encoding="utf-8")
        for name in ("product.md", "product-guidelines.md", "tech-stack.md",
                     "workflow.md", "setup.md", "tracks.md"):
            self.assertIn(name, index)
            self.assertTrue((CONDUCTOR / name).is_file(), name)
        for name in ("general.md", "python.md"):
            self.assertTrue((CONDUCTOR / "code_styleguides" / name).is_file())
        self.assertIn("code_styleguides/", index)

    def test_repository_local_plugin_link(self):
        link = ROOT / ".agents" / "plugins" / "conductor"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "../../vendor/gemini-conductor")
        modules = (ROOT / ".gitmodules").read_text(encoding="utf-8")
        self.assertIn("path = vendor/gemini-conductor", modules)
        self.assertIn("https://github.com/gemini-cli-extensions/conductor.git",
                      modules)
        # Actual initialized checkout and pin are checked by the migration suite.

    def test_registered_tracks_have_executable_plans(self):
        registry = (CONDUCTOR / "tracks.md").read_text(encoding="utf-8")
        links = re.findall(
            r"^- \[[ x~]\] \*\*Track:.*?\]\((tracks/[^)]+/index\.md)\)",
            registry, flags=re.MULTILINE)
        self.assertEqual(len(links), len(set(links)))
        self.assertIn("tracks/00-bibx-migration/index.md", links)
        for track in ("00", "01", "07", "12"):
            self.assertRegex(registry, rf"(?m)^- \[[~x]\] \*\*Track: {track} —")
        self.assertGreaterEqual(len(links), 4)
        for relative in links:
            with self.subTest(track=relative):
                track = (CONDUCTOR / relative).parent
                self.assertTrue((track / "index.md").is_file())
                self.assertTrue((track / "spec.md").is_file())
                self.assertRegex((track / "plan.md").read_text(encoding="utf-8"),
                                 r"\[[ x~]\]")

    def test_design2_inventory_identity_conserved(self):
        original = json.loads((CONDUCTOR / "tracks/00-bibx-migration"
                               / "baseline-capability-coverage.json")
                              .read_text(encoding="utf-8"))
        current = json.loads((ROOT / "contracts/methods/catalog.json")
                             .read_text(encoding="utf-8"))
        old_ids = [item["id"] for item in original["outcomes"]]
        new_ids = [item["id"] for item in current["outcomes"]]
        self.assertEqual(len(old_ids), 147)
        self.assertEqual(len(set(old_ids)), 147)
        self.assertEqual(len(new_ids), len(set(new_ids)))
        self.assertEqual(set(old_ids), set(new_ids))
        self.assertEqual(original["version"], "1.0.0-design.2")
        for item in original["outcomes"]:
            self.assertIn("acceptance", item)
            self.assertIn("sources", item)


if __name__ == "__main__":
    unittest.main()
