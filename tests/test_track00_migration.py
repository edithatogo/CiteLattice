"""Historical reference preservation, not scientific or Rust API certification."""
import gzip
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
TRACK = ROOT / "conductor/tracks/00-bibx-migration"

def git_blob_id(raw):
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((TRACK / "source-manifest.json").read_text())
        self.bundle_raw = (TRACK / "baseline-contracts.json.gz").read_bytes()
        self.bundle = json.loads(gzip.decompress(self.bundle_raw))

    def test_inventory_and_exact_historical_bytes(self):
        m = self.manifest
        self.assertEqual(len(m["source_files"]), 147)
        self.assertEqual(len({f["source"] for f in m["source_files"]}), 147)
        self.assertEqual(len(m["vendor_paths"]), 28)
        self.assertEqual(hashlib.sha256(self.bundle_raw).hexdigest(),
                         m["historical_contract_bundle_sha256"])
        self.assertEqual(git_blob_id((TRACK / "baseline-capability-coverage.json").read_bytes()),
                         m["baseline_catalogue_git_blob_sha1"])
        contracts = {f["source"]: f["git_blob_sha1"] for f in m["source_files"]
                     if "git_blob_sha1" in f}
        self.assertEqual(len(contracts), 14)
        self.assertEqual(set(self.bundle), set(contracts))
        for path, blob_id in contracts.items():
            with self.subTest(path=path):
                self.assertEqual(git_blob_id(self.bundle[path].encode()), blob_id)

    def test_original_schema_and_fixture_pairs(self):
        for name in ("analysis-run", "document-bundle", "evidence-scene",
                     "method", "render-receipt", "scholarly-stream", "table"):
            with self.subTest(name=name):
                schema = json.loads(self.bundle[f"contracts/proposals/{name}.v1.schema.json"])
                fixture_name = "scholarly-stream-upsert" if name == "scholarly-stream" else f"{name}-example"
                fixture = json.loads(self.bundle[f"contracts/proposals/fixtures/{fixture_name}.json"])
                Draft202012Validator.check_schema(schema)
                Draft202012Validator(schema, format_checker=FormatChecker()).validate(fixture)

    def test_upstream_setup_resume(self):
        script = ROOT / "vendor/gemini-conductor/skills/conductor-setup/scripts/resume.py"
        if not script.is_file() and not os.environ.get("CI"):
            self.skipTest("initialize the pinned submodule for native setup verification")
        self.assertTrue(script.is_file(), "CI must initialize the pinned submodule")
        result = json.loads(subprocess.check_output([sys.executable, str(script)], cwd=ROOT))
        self.assertTrue(result["setup_complete"])
        self.assertEqual(set(result["checklist"]), {"product.md", "product-guidelines.md",
                         "tech-stack.md", "code_styleguides", "workflow.md"})
        self.assertTrue(all(result["checklist"].values()))
        self.assertIsNone(result["next_step"])
        self.assertTrue((ROOT / ".agents/plugins/conductor/plugin.json").is_file())
        actual = subprocess.check_output(["git", "-C", str(ROOT / "vendor/gemini-conductor"),
                                          "rev-parse", "HEAD"], text=True).strip()
        self.assertEqual(actual, self.manifest["upstream_pin"])
        for name in ("general.md", "python.md"):
            self.assertEqual((ROOT / "conductor/code_styleguides" / name).read_bytes(),
                             (script.parents[1] / "assets/code_styleguides" / name).read_bytes())
