"""Independent E09 audit: known answers, semantic tampering and disclosure.

These tests qualify the fixture auditor, not a production producer or release.
The full reader suite requires verification/outputs/requirements.txt.
"""

import copy
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

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
        artifact = {"rows": source.rows, "metadata": source.metadata}
        audit.audit_artifact(source, "json", encoded(artifact))
        for key, value in (("withheld_rows", 2), ("withheld_rows", 0), ("source_rows", 24)):
            tampered = copy.deepcopy(artifact)
            tampered["metadata"]["counts"][key] = value
            with self.subTest(statistic=key, value=value), self.assertRaises(audit.AuditError):
                audit.audit_artifact(source, "json", encoded(tampered))

    def test_reference_fixture_and_auditor_pins(self):
        manifest = json.loads((ROOT / "verification/outputs/roundtrip-manifest.json").read_bytes())
        self.assertFalse(manifest["release_qualified"])
        for item in manifest["local_pins"]:
            with self.subTest(path=item["path"]):
                self.assertEqual(hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest(),
                                 item["sha256"])

    def test_source_count_type_and_null_status_matrix(self):
        original = json.loads((FIXTURES / "source-mixed.json").read_bytes())
        for value in (True, 0.0, "0", -1, 2**64, None):
            data = copy.deepcopy(original)
            data["rows"][0]["publications"] = value
            with self.subTest(value=value), self.assertRaises(audit.AuditError):
                audit.authority_from_bytes(encoded(data))

    def test_empty_and_all_null_authorities(self):
        original = json.loads((FIXTURES / "source-mixed.json").read_bytes())
        for rows, counts in [
            ([], {"source_rows": 0, "exported_rows": 0, "withheld_rows": 0,
                  "missing_counts": 0, "withheld_counts": 0, "undated_rows": 0,
                  "known_publications": "0"}),
            ([original["rows"][5], original["rows"][10]], {
                "source_rows": 2, "exported_rows": 2, "withheld_rows": 0,
                "missing_counts": 1, "withheld_counts": 1, "undated_rows": 0,
                "known_publications": "0"}),
        ]:
            data = copy.deepcopy(original)
            data.update(rows=rows, expected=counts)
            source = audit.authority_from_bytes(encoded(data))
            self.assertEqual(source.metadata["counts"], counts)

    def test_missing_or_wrong_reader_version_fails_closed(self):
        with mock.patch.object(importlib.metadata, "version", return_value="0.0.0"):
            with self.assertRaisesRegex(audit.AuditError, "reader_version_mismatch"):
                audit.require_reader("pyarrow")
        with mock.patch.object(importlib.metadata, "version",
                               side_effect=importlib.metadata.PackageNotFoundError):
            with self.assertRaisesRegex(audit.AuditError, "reader_unavailable"):
                audit.require_reader("pyarrow")


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

    def test_hand_specified_geometry_anchors_and_all_marks(self):
        oracle = json.loads((ROOT / "verification/imaging/geometry-oracles.json").read_bytes())
        root = ET.fromstring((self.bundle / "chart.svg").read_bytes())
        ns = {"s": "http://www.w3.org/2000/svg"}
        groups = {node.attrib["data-row-key"]: node for node in root.findall("s:g", ns)}
        self.assertEqual(len(groups), oracle["expected_public_marks"])
        self.assertEqual(len(root.findall("s:g/s:rect", ns)), oracle["expected_numeric_bars"])
        for anchor in oracle["anchors"]:
            node = groups[anchor["row_key"]].find("s:rect", ns)
            if anchor["value"] is None:
                self.assertIsNone(node)
            else:
                self.assertEqual({key: int(node.attrib[key]) for key in ("x", "height", "y")},
                                 {key: anchor[key] for key in ("x", "height", "y")})

    def test_large_integer_imaging_cannot_succeed_by_rounding(self):
        authority = audit.load_authority(FIXTURES / "source-integers.json")
        for kind, name in [("svg", "chart.svg"), ("scene", "scene.json"),
                           ("vega_lite", "chart.vl.json")]:
            with self.subTest(kind=kind), self.assertRaisesRegex(audit.AuditError, "browser_precision"):
                audit.audit_artifact(authority, kind, (self.bundle / name).read_bytes())

    def test_scene_crop_duplicate_or_null_to_zero(self):
        original = json.loads((self.bundle / "scene.json").read_bytes())
        for change in (
            lambda v: v.update(marks=v["marks"][:16]),
            lambda v: v["marks"].append(v["marks"][0]),
            lambda v: v["marks"][5].update(value=0),
            lambda v: v["marks"][0].update(row_keys=["E09_WITHHELD_ROW_A"]),
        ):
            value = copy.deepcopy(original)
            change(value)
            with self.assertRaises(audit.AuditError):
                audit.audit_artifact(self.source, "scene", encoded(value))

    def test_svg_external_entity_and_geometry_hiding_fail(self):
        raw = (self.bundle / "chart.svg").read_bytes()
        for value in (
            b'<!DOCTYPE svg [<!ENTITY hidden SYSTEM "file:///missing">]>' + raw,
            raw.replace(b'height="280"', b'height="NaN"', 1),
            raw.replace(b'fill="#465f82"', b'fill="transparent"', 1),
            raw.replace(b'<g data-row-key="y2000"', b'<g transform="scale(0)" data-row-key="y2000"', 1),
            raw.replace(b'<metadata>', b'<metadata hidden="true">', 1),
        ):
            with self.assertRaises(audit.AuditError):
                audit.audit_artifact(self.source, "svg", value)

    def test_unknown_format_and_malformed_json_fail_without_payload(self):
        for kind, raw in (("pdf", b"E09_RESTRICTED_PAYLOAD_A"),
                          ("json", b'{"secret":"E09_RESTRICTED_PAYLOAD_A",}'),
                          ("json", b'{"rows":NaN}')):
            with self.assertRaises(audit.AuditError) as ctx:
                audit.audit_artifact(self.source, kind, raw)
            self.assertNotIn("E09_RESTRICTED", str(ctx.exception))


def rewrite_zip(raw, replacements=None, extra=None):
    """Mutate actual serialized parts without calling either writer or auditor."""
    result = io.BytesIO()
    replacements = replacements or {}
    with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(result, "w") as target:
        for item in source.infolist():
            data = source.read(item)
            if item.filename in replacements:
                changed = replacements[item.filename](data)
                if changed == data:
                    raise AssertionError("Mutation was not applied")
                data = changed
            target.writestr(item, data)
        for name, data in (extra or {}).items():
            target.writestr(name, data)
    return result.getvalue()


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

    def test_arrow_types_nullability_units_rows_and_rights_mutations(self):
        import pyarrow as pa
        import pyarrow.ipc as ipc
        import pyarrow.parquet as pq
        authority = audit.load_authority(FIXTURES / "source-mixed.json")
        original = ipc.open_file(FIXTURES / "mixed/table.arrow").read_all()
        cases = []
        for field in (
            pa.field("publications", pa.int64(), nullable=True, metadata={b"unit": b"works"}),
            pa.field("publications", pa.uint64(), nullable=True, metadata={b"unit": b"citations"}),
        ):
            schema = original.schema.set(2, field)
            cases.append(pa.Table.from_pylist(original.to_pylist(), schema=schema))
        rows = original.to_pylist()
        rows[5]["publications"] = 0
        cases.append(pa.Table.from_pylist(rows, schema=original.schema))
        cases.append(original.slice(0, original.num_rows - 1))
        cases.append(pa.concat_tables([original, original.slice(0, 1)]))
        cases.append(original.replace_schema_metadata({b"e09": b'{"rights":"allowed"}'}))
        cases.append(original.replace_schema_metadata({**original.schema.metadata,
                                                        b"hidden": b"unapproved payload"}))
        # A nullable year field cannot silently become non-nullable, even if all
        # selected records happen to be dated. Independently check its schema.
        rows = original.to_pylist()
        rows[20]["year"] = 2000
        schema = original.schema.set(1, pa.field("year", pa.int32(), nullable=False,
                                                  metadata={b"unit": b"calendar_year"}))
        cases.append(pa.Table.from_pylist(rows, schema=schema))
        for index, table in enumerate(cases):
            for kind in ("arrow_ipc", "parquet"):
                sink = pa.BufferOutputStream()
                if kind == "parquet":
                    pq.write_table(table, sink)
                else:
                    with ipc.new_file(sink, table.schema) as writer:
                        writer.write_table(table)
                with self.subTest(case=index, format=kind), self.assertRaises(audit.AuditError):
                    audit.audit_artifact(authority, kind, sink.getvalue().to_pybytes())

    def test_multiple_parquet_row_groups_are_fully_read(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        authority = audit.load_authority(FIXTURES / "source-mixed.json")
        table = pq.ParquetFile(FIXTURES / "mixed/table.parquet").read()
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink, row_group_size=3)
        raw = sink.getvalue().to_pybytes()
        self.assertGreater(pq.ParquetFile(pa.BufferReader(raw)).num_row_groups, 1)
        audit.audit_artifact(authority, "parquet", raw)

    def test_arrow_hidden_batch_metadata_is_rejected(self):
        import pyarrow as pa
        import pyarrow.ipc as ipc
        authority = audit.load_authority(FIXTURES / "source-mixed.json")
        table = ipc.open_file(FIXTURES / "mixed/table.arrow").read_all()
        sink = pa.BufferOutputStream()
        with ipc.new_file(sink, table.schema) as writer:
            writer.write_batch(table.to_batches()[0], custom_metadata={"hidden": "unapproved"})
        with self.assertRaisesRegex(audit.AuditError, "arrow_hidden_batch_metadata"):
            audit.audit_artifact(authority, "arrow_ipc", sink.getvalue().to_pybytes())

    def test_xlsx_formula_hidden_sheet_link_comment_and_extra_content(self):
        authority = audit.load_authority(FIXTURES / "source-mixed.json")
        raw = (FIXTURES / "mixed/table.xlsx").read_bytes()
        replacements = [
            {"xl/worksheets/sheet1.xml": lambda b: b.replace(b'<c r="C2"><v>0</v></c>',
                b'<c r="C2"><f>1-1</f><v>0</v></c>')},
            {"xl/workbook.xml": lambda b: b.replace(b'<sheet name="Data"',
                                                      b'<sheet state="hidden" name="Data"')},
            {"xl/_rels/workbook.xml.rels": lambda b: b.replace(b'<Relationship Id=',
                        b'<Relationship TargetMode="External" Id=', 1)},
            {"xl/worksheets/sheet1.xml": lambda b: b.replace(b'<row r="2"',
                                                              b'<row hidden="1" r="2"')},
            {"xl/sharedStrings.xml": lambda b: b.replace(b'</sst>',
                        b'<si><t>UNAPPROVED_ORPHAN_TEXT</t></si></sst>')},
            {"docProps/core.xml": lambda b: b.replace(b'</cp:coreProperties>',
                        b'<dc:description>UNAPPROVED_METADATA_TEXT</dc:description></cp:coreProperties>')},
            {"xl/worksheets/sheet1.xml": lambda b: b.replace(b'</sheetData>',
                        b'<unknown>UNAPPROVED_XML_TEXT</unknown></sheetData>')},
        ]
        for index, mutation in enumerate(replacements):
            with self.subTest(case=index), self.assertRaises(audit.AuditError):
                audit.audit_artifact(authority, "xlsx", rewrite_zip(raw, mutation))
        for name in ("xl/comments1.xml", "customXml/item1.xml", "xl/vbaProject.bin"):
            with self.subTest(part=name), self.assertRaises(audit.AuditError):
                audit.audit_artifact(authority, "xlsx", rewrite_zip(raw, extra={name: b"hidden"}))
        with self.assertRaisesRegex(audit.AuditError, "xlsx_prefix_or_trailing_payload"):
            audit.audit_artifact(authority, "xlsx", raw + b"UNAPPROVED_TRAILING_PAYLOAD")

    def test_xlsx_large_integer_must_not_be_binary64(self):
        authority = audit.load_authority(FIXTURES / "source-integers.json")
        raw = (FIXTURES / "integers/table.xlsx").read_bytes()
        changed = rewrite_zip(raw, {"xl/worksheets/sheet1.xml": lambda b:
            b.replace(b'<c r="C7" t="s"><v>22</v></c>',
                      b'<c r="C7"><v>9007199254740992</v></c>')})
        with self.assertRaises(audit.AuditError):
            audit.audit_artifact(authority, "xlsx", changed)

    def test_bundle_manifest_and_path_mutations(self):
        source = audit.load_authority(FIXTURES / "source-mixed.json")
        for case in ("unlisted", "missing", "duplicate", "traversal", "absolute", "symlink", "digest"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                dest = Path(tmp) / "bundle"
                shutil.copytree(FIXTURES / "mixed", dest)
                path = dest / "manifest.json"
                manifest = json.loads(path.read_bytes())
                if case == "unlisted":
                    (dest / "extra.txt").write_text("unapproved")
                elif case == "missing":
                    (dest / "table.html").unlink()
                elif case == "duplicate":
                    manifest["artifacts"][-1] = manifest["artifacts"][0]
                elif case in ("traversal", "absolute"):
                    manifest["artifacts"][0]["path"] = "../secret" if case == "traversal" else "/secret"
                elif case == "symlink":
                    asset = dest / "table.json"
                    outside = Path(tmp) / "target"
                    asset.rename(outside)
                    asset.symlink_to(outside)
                else:
                    manifest["artifacts"][0]["sha256"] = "0"*64
                path.write_bytes(encoded(manifest))
                with self.assertRaises(audit.AuditError):
                    audit.audit_bundle(source, dest)

    def test_cli_pass_and_failure_have_truthful_exit_status_and_no_payload(self):
        good = subprocess.run([sys.executable, "-m", "verification.outputs.audit",
                               str(FIXTURES / "source-mixed.json"), str(FIXTURES / "mixed")],
                              cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        self.assertFalse(json.loads(good.stdout)["release_qualified"])
        with tempfile.TemporaryDirectory() as tmp:
            bad_source = Path(tmp) / "E09_RESTRICTED_PAYLOAD_A"
            bad_source.write_text('E09_RESTRICTED_PAYLOAD_A')
            bad = subprocess.run([sys.executable, "-m", "verification.outputs.audit",
                                  str(bad_source), str(FIXTURES / "mixed")],
                                 cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(json.loads(bad.stdout)["status"], "failed")
        self.assertNotIn("E09_RESTRICTED", bad.stdout + bad.stderr)


if __name__ == "__main__":
    unittest.main()
