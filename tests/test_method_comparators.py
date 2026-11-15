"""Offline E05 contract/oracle tests; these do not qualify production methods."""

import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from verification.comparators import harness
from verification.comparators.pybibx_worker import extract_methods


ROOT = Path(__file__).resolve().parents[1]
AREA = ROOT / "verification/comparators"


def independent_indices(counts):
    """Enumerate subsets, independently of sorted-prefix production kernels."""
    n = len(counts)
    return {
        "h": str(max(k for k in range(n + 1) if sum(c >= k for c in counts) >= k)),
        "g": str(max(k for k in range(n + 1)
                     if any(sum(s) >= k * k for s in itertools.combinations(counts, k)))),
        "i10": str(sum(c >= 10 for c in counts)),
        "total": str(sum(counts)),
    }


class ComparatorContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = harness.load_manifest(ROOT)
        cls.cases = harness.load_cases(ROOT, cls.manifest)

    def test_every_known_answer_has_an_independent_subset_oracle(self):
        self.assertGreaterEqual(len(self.cases), 280)
        for case in self.cases:
            with self.subTest(case=case["id"]):
                counts = [None if row["citations"] is None else int(row["citations"])
                          for row in case["observations"]]
                lower = independent_indices([0 if c is None else c for c in counts])
                upper = independent_indices([harness.U64_MAX if c is None else c for c in counts])
                for metric in ("h", "g", "i10"):
                    self.assertEqual(case["expected"][metric], [lower[metric], upper[metric]])
                self.assertEqual(case["expected"]["total"],
                                 [lower["total"], None if None in counts else lower["total"]])

    def test_existing_oracles_are_reused_without_replacing_them(self):
        ids = {c["id"] for c in self.cases}
        originals = json.loads((ROOT / "verification/citation-oracles.json").read_text())
        self.assertTrue({"existing/" + c["id"] for c in originals["cases"]} <= ids)
        self.assertEqual(len(ids), len(self.cases))

    def test_unknown_counts_retain_actual_n_and_null(self):
        case = next(c for c in self.cases if c["id"] == "known/partial-high")
        self.assertEqual(len(case["observations"]), 3)
        self.assertEqual(case["expected"]["g"], ["3", "3"])
        before = copy.deepcopy(case)
        for backend in self.manifest["comparators"]:
            self.assertEqual(harness.preflight(backend, case, "g"), "unsupported_missing_counts")
        self.assertEqual(case, before)
        self.assertIsNone(case["observations"][1]["citations"])

    def test_actual_n_cap_is_never_applied_to_comparator_output(self):
        case = next(c for c in self.cases if c["id"] == "known/single-high")
        self.assertEqual(case["expected"]["g"], ["1", "1"])
        row = harness.compare_value(case, "pybibx", "g", "10")
        self.assertEqual(row["status"], "mismatch")
        self.assertEqual(row["actual"], "10")

    def test_exact_integer_equality_has_no_float_tolerance(self):
        case = copy.deepcopy(self.cases[0])
        case["expected"]["total"] = ["9007199254740993", "9007199254740993"]
        self.assertEqual(harness.compare_value(case, "pybibx", "total", "9007199254740992")["status"], "mismatch")
        self.assertEqual(harness.compare_value(case, "pybibx", "total", "9007199254740993")["status"], "matched")
        for value in (9007199254740993, 1.0, True, "01", "1e3", "-1", None):
            with self.subTest(value=value), self.assertRaises(harness.ContractError):
                harness.compare_value(case, "pybibx", "total", value)

    def test_large_counts_and_sums_are_explicitly_unsupported_in_r(self):
        for name in ("binary64-neighbours", "binary64-sum", "u64-total"):
            case = next(c for c in self.cases if c["id"] == "known/" + name)
            self.assertEqual(harness.preflight("bibliometrix", case, "h"), "unsupported_integer_range")
            self.assertIsNone(harness.preflight("pybibx", case, "h"))

    def test_unsupported_methods_do_not_receive_adapter_reimplementations(self):
        case = next(c for c in self.cases if c["id"] == "known/textbook")
        self.assertEqual(harness.preflight("pybibx", case, "total"), "unsupported_method")
        for backend in self.manifest["comparators"]:
            self.assertEqual(harness.preflight(backend, case, "i10"), "unsupported_method")

    def test_empty_population_is_not_invented_as_a_bibliometrix_result(self):
        empty = next(c for c in self.cases if c["id"] == "known/empty")
        self.assertEqual(harness.preflight("bibliometrix", empty, "g"), "unsupported_empty_population")
        self.assertIsNone(harness.preflight("pybibx", empty, "g"))

    def test_case_validation_rejects_ambiguous_counts_and_duplicate_identity(self):
        template = next(c for c in self.cases if c["id"] == "known/textbook")
        for bad_value in (1, 1.0, True, "00", "+1", "-1", "1.0", str(2 ** 64)):
            bad = copy.deepcopy(template)
            bad["observations"][0]["citations"] = bad_value
            with self.subTest(value=bad_value), self.assertRaises(harness.ContractError):
                harness.validate_case(bad)
        bad = copy.deepcopy(template)
        bad["observations"][1]["id"] = bad["observations"][0]["id"]
        with self.assertRaises(harness.ContractError):
            harness.validate_case(bad)

    def test_scope_and_unknowns_are_bound_to_input_digest(self):
        original = next(c for c in self.cases if c["id"] == "known/partial-high")
        for field in ("citation_universe", "as_of", "population_id", "g_convention"):
            changed = copy.deepcopy(original)
            changed["context"][field] += "-changed"
            self.assertNotEqual(harness.input_digest(original), harness.input_digest(changed))
        changed = copy.deepcopy(original)
        changed["observations"][1]["citations"] = "0"
        self.assertNotEqual(harness.input_digest(original), harness.input_digest(changed))

    def test_response_must_retain_every_identity_and_exact_input_digest(self):
        case = next(c for c in self.cases if c["id"] == "known/textbook")
        result = {"case_id": case["id"], "input_sha256": harness.input_digest(case),
                  "actual_n": "5", "metrics": {"h": "4", "g": "5"}}
        self.assertEqual(harness.validate_results("pybibx", [case], [result])[case["id"]], result)
        for changed in ([], [result, result], [dict(result, actual_n="4")],
                        [dict(result, input_sha256="0" * 64)],
                        [dict(result, metrics={"h": 4, "g": "5"})],
                        [dict(result, metrics={"h": "4"})]):
            with self.subTest(changed=changed), self.assertRaises(harness.ContractError):
                harness.validate_results("pybibx", [case], changed)

    def test_pins_are_exact_and_changed_shared_contracts_fail_closed(self):
        for item in self.manifest["comparators"].values():
            self.assertRegex(item["commit"], r"^[a-f0-9]{40}$")
            self.assertTrue(item["license"])
            for file_pin in item["files"].values():
                self.assertRegex(file_pin, r"^[a-f0-9]{64}$")
        path = ROOT / self.manifest["inputs"]["method"]["path"]
        with self.assertRaises(harness.ContractError):
            harness.read_pinned(path, "0" * 64)

    def test_worker_runtime_protocol_and_source_are_checked_independently(self):
        case = next(c for c in self.cases if c["id"] == "known/textbook")
        pin = self.manifest["comparators"]["pybibx"]
        response = {
            "status": "executed", "protocol": harness.PROTOCOL, "backend": "pybibx",
            "source_sha256": pin["files"][pin["entrypoint"]],
            "runtime": {"implementation": "CPython", "python": "3.12.14"},
            "results": [{"case_id": case["id"], "input_sha256": harness.input_digest(case),
                         "actual_n": "5", "metrics": {"h": "4", "g": "5"}}],
        }
        self.assertEqual(harness.validate_response("pybibx", [case], response, pin, 0), response)
        for key, value in (("runtime", {"python": "3.12.14"}), ("source_sha256", "0" * 64),
                           ("protocol", "org.citelattice.e05-worker/2.0.0"), ("backend", "bibliometrix")):
            with self.subTest(key=key), self.assertRaises(harness.ContractError):
                harness.validate_response("pybibx", [case], dict(response, **{key: value}), pin, 0)
        for malformed in ([], None, {"status": "blocked_environment"}):
            with self.subTest(malformed=malformed), self.assertRaises(harness.ContractError):
                harness.validate_response("pybibx", [case], malformed, pin, 0)

    def test_duplicate_json_keys_floats_and_nonfinite_values_are_rejected(self):
        for text in ('{"h":"1","h":"2"}', '{"h":1.0}', '{"h":NaN}', '{"h":Infinity}'):
            with self.subTest(text=text), self.assertRaises(harness.ContractError):
                harness.strict_json(text)

    def test_bad_source_never_yields_a_match_or_hidden_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = harness.run_probe(ROOT, self.manifest, self.cases, {"pybibx": Path(tmp)})
            self.assertEqual(report["executions"]["pybibx"]["status"], "error")
            self.assertGreater(report["summary"]["error"], 0)
            self.assertNotIn("matched", report["summary"])

    @unittest.skipUnless(importlib.util.find_spec("pyarrow"), "optional pinned pyarrow runtime is absent")
    def test_parquet_round_trip_preserves_exact_strings_nulls_and_no_overwrite(self):
        import pyarrow as pa
        import pyarrow.parquet as pq

        report = harness.run_probe(ROOT, self.manifest, self.cases, {})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.parquet"
            harness.write_parquet(report, path, self.manifest)
            table = pq.read_table(path)
            self.assertEqual(table.to_pylist(), report["rows"])
            self.assertTrue(all(field.type == pa.string() for field in table.schema))
            self.assertEqual(table.schema.metadata[b"production_numerical_qualification"], b"false")
            big = next(row for row in table.to_pylist()
                       if row["case_id"] == "known/u64-total" and row["metric"] == "total")
            self.assertEqual(big["expected_lower"], "36893488147419103230")
            partial = next(row for row in table.to_pylist()
                           if row["case_id"] == "known/partial-high" and row["metric"] == "total")
            self.assertIsNone(partial["expected_upper"])
            self.assertIsNone(partial["actual"])
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                harness.write_parquet(report, path, self.manifest)
            self.assertEqual(path.read_bytes(), before)

    def test_e04_never_becomes_qualified_from_a_passing_pilot(self):
        gate = harness.qualification_status(ROOT, self.manifest)
        self.assertEqual(gate["state"], "blocked_e04")
        self.assertFalse(gate["production_numerical_qualification"])
        self.assertIsNone(gate["accepted_upstream_commit"])

    def test_all_147_outcomes_remain_explicitly_unqualified(self):
        catalogue = json.loads((ROOT / "contracts/methods/catalog.json").read_text())
        coverage = json.loads((AREA / "outcome-status.json").read_text())
        actual = {x["id"]: x for x in coverage["outcomes"]}
        self.assertEqual(set(actual), {x["id"] for x in catalogue["outcomes"]})
        self.assertEqual(len(actual), 147)
        self.assertEqual(len(coverage["outcomes"]), 147)
        self.assertTrue(all(x["status"] in {"deferred", "unsupported"} for x in actual.values()))
        self.assertFalse(coverage["production_numerical_qualification"])

    def test_offline_probe_retains_blocked_and_unsupported_rows(self):
        report = harness.run_probe(ROOT, self.manifest, self.cases, {})
        self.assertEqual(len(report["rows"]), len(self.cases) * 2 * 4)
        self.assertFalse(any(row["status"] == "matched" for row in report["rows"]))
        self.assertTrue(any(row["status"] == "blocked_source" for row in report["rows"]))
        self.assertTrue(all(row["actual"] is None for row in report["rows"]))
        self.assertFalse(report["qualification"]["production_numerical_qualification"])

    def test_cli_does_not_succeed_as_a_qualification_without_sources(self):
        proc = subprocess.run([sys.executable, "-B", str(AREA / "harness.py"), "--require-qualified"],
                              cwd=ROOT, text=True, capture_output=True, timeout=20)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["qualification"]["state"], "blocked_e04")


class SourceExecutionBoundary(unittest.TestCase):
    def test_only_unchanged_selected_methods_execute_after_hash_check(self):
        # Deliberately synthetic sentinel code tests extraction, not numerical parity.
        source = ("raise RuntimeError('module import must not execute')\n"
                  "class pbx_probe:\n"
                  "    def h_index(self):\n        return [self.marker]\n"
                  "    def g_index(self):\n        return [self.marker + 1]\n"
                  "    def unrelated(self):\n        raise RuntimeError('not selected')\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.py"
            path.write_text(source)
            methods = extract_methods(path, hashlib.sha256(source.encode()).hexdigest())
            marker = type("Marker", (), {"marker": 41})()
            self.assertEqual(methods["h_index"](marker), [41])
            self.assertEqual(methods["g_index"](marker), [42])
            self.assertEqual(set(methods), {"h_index", "g_index"})
            with self.assertRaises(harness.ContractError):
                extract_methods(path, "0" * 64)


if __name__ == "__main__":
    unittest.main()
