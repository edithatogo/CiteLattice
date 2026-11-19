"""Offline oracle/receipt-GATE tests only; Polars/native execution is NOT asserted."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory
import unittest

PROBE = Path(__file__).resolve().parents[1] / "verification/dependencies/track09-polars-annual"
sys.path.insert(0, str(PROBE))
import synthetic  # noqa: E402
import compare  # noqa: E402


class Track09ParityGateTests(unittest.TestCase):
    def test_fixture_bytes_are_deterministic_and_negative_cases_are_explicit(self) -> None:
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            first = synthetic.write_bundle(Path(a))
            second = synthetic.write_bundle(Path(b))
            self.assertEqual(first, second)
            for case in first["cases"]:
                self.assertEqual((Path(a) / case["filename"]).read_bytes(), (Path(b) / case["filename"]).read_bytes())
            self.assertEqual(synthetic.verify_bundle(Path(a)), first)
            cases = {item["case_id"]: item["expected"] for item in first["cases"]}
            self.assertEqual(cases["mixed"]["annual"], [
                {"year": -1, "count": 1}, {"year": 0, "count": 1},
                {"year": 1999, "count": 2}, {"year": 2024, "count": 2},
            ])
            self.assertEqual(cases["mixed"]["undated"], 2)
            self.assertEqual(cases["undated"]["annual"], [])
            self.assertEqual(cases["invalid-schema"], {"status": "rejected", "error_category": "InvalidContract"})
            self.assertEqual(cases["duplicate-id"], {"status": "rejected", "error_category": "Duplicate"})

    def test_permutation_preserves_record_year_associations(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            synthetic.write_bundle(root)
            mixed = [json.loads(x) for x in (root / "mixed.jsonl").read_text().splitlines()]
            permuted = [json.loads(x) for x in (root / "permuted.jsonl").read_text().splitlines()]
            self.assertNotEqual(mixed, permuted)
            self.assertEqual(
                {r["record_id"]: r["publication_year"] for r in mixed},
                {r["record_id"]: r["publication_year"] for r in permuted},
            )

    def _setup(self, folder: Path) -> tuple[dict, Path, Path]:
        manifest = synthetic.write_bundle(folder / "fixtures")
        # Self-test receipts only; never interpret these as runtime output.
        rows = [dict(case_id=c["case_id"], input_sha256=c["input_sha256"], **deepcopy(c["expected"])) for c in manifest["cases"]]
        baseline = folder / "baseline.jsonl"
        candidate = folder / "candidate.jsonl"
        baseline.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        candidate.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        return manifest, baseline, candidate

    def test_gate_accepts_oracle_shaped_self_test_receipts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._setup(root)
            self.assertEqual(compare.compare(root / "fixtures", root / "baseline.jsonl", root / "candidate.jsonl"), 8)

    def test_gate_fails_closed_on_missing_candidate_case(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._setup(root)
            lines = (root / "candidate.jsonl").read_text().splitlines()
            (root / "candidate.jsonl").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(compare.ParityError, "missing or extra"):
                compare.compare(root / "fixtures", root / "baseline.jsonl", root / "candidate.jsonl")

    def test_gate_rejects_floating_count_and_wrong_null_semantics(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._setup(root)
            rows = [json.loads(x) for x in (root / "candidate.jsonl").read_text().splitlines()]
            mixed = next(r for r in rows if r["case_id"] == "mixed")
            mixed["annual"][0]["count"] = 1.0
            (root / "candidate.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(compare.ParityError, "precision or type"):
                compare.compare(root / "fixtures", root / "baseline.jsonl", root / "candidate.jsonl")
            mixed["annual"][0]["count"] = 1
            mixed["undated"] = 0
            (root / "candidate.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(compare.ParityError, "conservation"):
                compare.compare(root / "fixtures", root / "baseline.jsonl", root / "candidate.jsonl")

    def test_gate_rejects_wrong_negative_admission(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._setup(root)
            rows = [json.loads(x) for x in (root / "candidate.jsonl").read_text().splitlines()]
            bad = next(r for r in rows if r["case_id"] == "invalid-schema")
            bad.update(status="ok")
            with self.assertRaisesRegex(compare.ParityError, "acceptance/rejection"):
                compare.assert_receipt(next(c for c in json.loads((root / "fixtures/manifest.json").read_text())["cases"] if c["case_id"] == "invalid-schema"), bad)

    def test_bundle_rejects_tampered_oracle_even_when_source_digest_is_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            synthetic.write_bundle(root)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            mixed = next(r for r in manifest["cases"] if r["case_id"] == "mixed")
            mixed["expected"]["annual"][0]["count"] = 2
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest oracle"):
                synthetic.verify_bundle(root)

    def test_bundle_rejects_unsafe_fixture_path_before_reading(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            synthetic.write_bundle(root)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["cases"][0]["case_id"] = "../not-a-fixture"
            manifest["cases"][0]["filename"] = "../not-a-fixture.jsonl"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid or repeated fixture path"):
                synthetic.verify_bundle(root)

    def test_bundle_integrity_rejects_tampering(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            synthetic.write_bundle(root)
            with (root / "mixed.jsonl").open("ab") as stream:
                stream.write(b"\n")
            with self.assertRaisesRegex(ValueError, "byte integrity"):
                synthetic.verify_bundle(root)


if __name__ == "__main__":
    unittest.main()
