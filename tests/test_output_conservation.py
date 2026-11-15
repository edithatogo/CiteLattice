"""Independent E09 audit: known answers, semantic tampering and disclosure.

These tests qualify the fixture auditor, not a production producer or release.
The full reader suite requires verification/outputs/requirements.txt.
"""

import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from verification.outputs import audit

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "verification/outputs/fixtures"


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n").encode()


class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.source = audit.load_authority(FIXTURES / "source-mixed.json")

    def test_independent_known_answers_and_distinct_missingness(self):
        self.assertEqual(self.source.metadata["counts"], {
            "source_rows": 24, "exported_rows": 22, "withheld_rows": 2,
            "missing_counts": 1, "withheld_counts": 1, "undated_rows": 1,
            "known_publications": "180",
        })
        self.assertEqual(self.source.rows[0]["publications"], 0)
        self.assertIsNone(self.source.rows[5]["publications"])
        self.assertIsNone(self.source.rows[10]["publications"])
        self.assertNotEqual(self.source.rows[5]["availability"],
                            self.source.rows[10]["availability"])

    def test_integer_authority_exceeds_u64_total_without_float_coercion(self):
        source = audit.load_authority(FIXTURES / "source-integers.json")
        self.assertEqual(source.rows[6]["publications"], 2**64 - 1)
        self.assertEqual(source.metadata["counts"]["known_publications"],
                         "18473765680063709182")

    def test_source_duplicate_keys_and_rows_fail_closed(self):
        raw = (FIXTURES / "source-mixed.json").read_bytes()
        with self.assertRaises(audit.AuditError):
            audit.authority_from_bytes(raw.replace(b'"id": "mixed"',
                                                   b'"id": "mixed", "id": "other"'))
        data = json.loads(raw)
        data["rows"][1]["row_key"] = data["rows"][0]["row_key"]
        with self.assertRaises(audit.AuditError):
            audit.authority_from_bytes(encoded(data))

    def test_unapproved_or_unknown_rights_fail_closed(self):
        data = json.loads((FIXTURES / "source-mixed.json").read_bytes())
        data["policy"]["export_allowed"] = False
        with self.assertRaises(audit.AuditError):
            audit.authority_from_bytes(encoded(data))
        data["policy"]["export_allowed"] = True
        data["rows"][0]["rights"] = "probably-public"
        with self.assertRaises(audit.AuditError):
            audit.authority_from_bytes(encoded(data))

    def test_unknown_withheld_count_is_not_reported_as_zero(self):
        data = json.loads((FIXTURES / "source-mixed.json").read_bytes())
        data["policy"]["disclose_withheld_count"] = False
        source = audit.authority_from_bytes(encoded(data))
        self.assertIsNone(source.metadata["counts"]["withheld_rows"])
        self.assertIsNone(source.metadata["counts"]["source_rows"])


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.source = audit.load_authority(FIXTURES / "source-mixed.json")
        self.bundle = FIXTURES / "mixed"

    def check(self, kind, name):
        audit.audit_artifact(self.source, kind, (self.bundle / name).read_bytes())

    def test_text_formats_agree_with_source(self):
        for kind, name in [("json", "table.json"), ("csv", "table.csv"),
                           ("html", "table.html"), ("typst_source", "table.typ"),
                           ("scene", "scene.json"), ("vega_lite", "chart.vl.json"),
                           ("svg", "chart.svg"), ("disclosure", "disclosure.json")]:
            with self.subTest(format=kind):
                self.check(kind, name)

    def test_json_tamper_matrix(self):
        original = json.loads((self.bundle / "table.json").read_bytes())
        changes = {
            "null-to-zero": lambda v: v["rows"][5].update(publications=0),
            "missing-to-withheld": lambda v: v["rows"][5].update(availability="withheld"),
            "bool-as-integer": lambda v: v["rows"][1].update(publications=True),
            "float-as-integer": lambda v: v["rows"][1].update(publications=1.0),
            "string-as-integer": lambda v: v["rows"][1].update(publications="1"),
            "row-loss": lambda v: v["rows"].pop(),
            "row-duplication": lambda v: v["rows"].append(v["rows"][0]),
            "wrong-rights": lambda v: v["rows"][0].update(rights="withhold"),
            "withheld-count": lambda v: v["metadata"]["counts"].update(withheld_rows=0),
            "units": lambda v: v["metadata"]["columns"][2].update(unit="citations"),
            "source-substitution": lambda v: v["metadata"].update(source_sha256="0"*64),
            "hidden-payload": lambda v: v.update(hidden="E09_RESTRICTED_PAYLOAD_A"),
        }
        for name, change in changes.items():
            value = copy.deepcopy(original)
            change(value)
            with self.subTest(case=name), self.assertRaises(audit.AuditError):
                audit.audit_artifact(self.source, "json", encoded(value))

    def test_safe_formula_literal_and_unescaped_csv_formula(self):
        raw = (self.bundle / "table.csv").read_bytes()
        self.assertIn(b"'=1+1", raw)
        with self.assertRaises(audit.AuditError):
            audit.audit_artifact(self.source, "csv", raw.replace(b"'=1+1", b"=1+1"))

    def test_scene_and_vega_reject_hidden_layers_and_inexact_values(self):
        for kind, name, field in [("scene", "scene.json", "hidden"),
                                  ("vega_lite", "chart.vl.json", "layer")]:
            data = json.loads((self.bundle / name).read_bytes())
            data[field] = [{"tooltip": "E09_RESTRICTED_PAYLOAD_A"}]
            with self.subTest(kind=kind), self.assertRaises(audit.AuditError):
                audit.audit_artifact(self.source, kind, encoded(data))
        data = json.loads((self.bundle / "scene.json").read_bytes())
        data["marks"][1]["value"] = 1.0
        with self.assertRaises(audit.AuditError):
            audit.audit_artifact(self.source, "scene", encoded(data))

    def test_svg_geometry_and_disclosure_mutations(self):
        raw = (self.bundle / "chart.svg").read_bytes()
        mutations = [
            raw.replace(b'height="280"', b'height="279"', 1),
            raw.replace(b'width="26"', b'width="27"', 1),
            raw.replace(b'<svg ', b'<svg onload="alert(1)" ', 1),
            raw.replace(b'</svg>', b'<script>alert(1)</script></svg>'),
            raw.replace(b'</svg>', b'<g display="none">E09_RESTRICTED_PAYLOAD_A</g></svg>'),
            raw.replace(b'</svg>', b'<!-- E09_RESTRICTED_PAYLOAD_A --></svg>'),
        ]
        for i, data in enumerate(mutations):
            self.assertNotEqual(data, raw)
            with self.subTest(case=i), self.assertRaises(audit.AuditError):
                audit.audit_artifact(self.source, "svg", data)

    def test_html_and_typst_never_execute_extra_content(self):
        for kind, name, suffix in [
            ("html", "table.html", b'<script>fetch("https://example.invalid")</script>'),
            ("html", "table.html", b'<div hidden>E09_RESTRICTED_PAYLOAD_A</div>'),
            ("typst_source", "table.typ", b'\n#read("secret.txt")\n'),
        ]:
            with self.subTest(kind=kind), self.assertRaises(audit.AuditError):
                audit.audit_artifact(self.source, kind, (self.bundle / name).read_bytes()+suffix)


def full_readers_available():
    try:
        return all(importlib.metadata.version(name) == version
                   for name, version in audit.READER_PINS.items())
    except importlib.metadata.PackageNotFoundError:
        return False


@unittest.skipUnless(full_readers_available(),
                     "Full E09 readers unavailable; install verification/outputs/requirements.txt")
class FullBundleTests(unittest.TestCase):
    def test_all_formats_and_integer_boundary_package(self):
        for case in ("mixed", "integers"):
            source = audit.load_authority(FIXTURES / f"source-{case}.json")
            result = audit.audit_bundle(source, FIXTURES / case)
            self.assertEqual(result["status"], "passed")
            self.assertFalse(result["release_qualified"])
            self.assertEqual(result["claim"], "synthetic-fixture-auditor-only")

    def test_rehashed_corruption_is_not_semantic_proof(self):
        source = audit.load_authority(FIXTURES / "source-mixed.json")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "bundle"
            shutil.copytree(FIXTURES / "mixed", dest)
            path = dest / "table.json"
            value = json.loads(path.read_bytes())
            value["rows"][0]["publications"] = 100
            path.write_bytes(encoded(value))
            manifest = json.loads((dest / "manifest.json").read_bytes())
            for item in manifest["artifacts"]:
                if item["path"] == path.name:
                    item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            (dest / "manifest.json").write_bytes(encoded(manifest))
            with self.assertRaises(audit.AuditError):
                audit.audit_bundle(source, dest)


if __name__ == "__main__":
    unittest.main()
