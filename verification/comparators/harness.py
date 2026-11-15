"""Offline, exact-integer E05 probes. No production numerical admission is made.

External source is supplied explicitly and checked before execution. Expected
answers never enter a worker. The harness has only standard-library dependencies;
Parquet export is optional and separately version-pinned.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
AREA = Path("verification/comparators")
U64_MAX = 2 ** 64 - 1
SAFE_R_INTEGER = 2 ** 53 - 1
METRICS = ("h", "g", "i10", "total")
SUPPORT = {"pybibx": ("h", "g"), "bibliometrix": ("h", "g", "total")}
PROTOCOL = "org.citelattice.e05-worker/1.0.0"
MAX_CASES = 1000
MAX_WORKS = 8  # This small independent subset-oracle suite is deliberately bounded.


class ContractError(ValueError):
    """Invalid evidence, input or worker output; no numerical match is admitted."""


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError("duplicate JSON key")
            result[key] = value
        return result

    def bad_number(_):
        raise ContractError("floating point/non-finite JSON is not allowed")

    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_float=bad_number, parse_constant=bad_number)
    except (ValueError, TypeError) as error:
        raise ContractError("invalid exact JSON") from error


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value):
    """Local ASCII JSON digest profile; not a replacement for production JCS."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def read_pinned(path, expected):
    data = Path(path).read_bytes()
    if digest(data) != expected:
        raise ContractError("pinned bytes changed: " + Path(path).name)
    return data


def decimal(value):
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]{0,38}", value):
        raise ContractError("expected canonical nonnegative decimal text")
    return int(value)


def load_manifest(root=ROOT):
    manifest = strict_json((root / AREA / "manifest.json").read_text())
    if manifest.get("schema_version") != "org.citelattice.e05-comparators/1.0.0":
        raise ContractError("unsupported comparator manifest")
    if set(manifest["comparators"]) != set(SUPPORT):
        raise ContractError("unexpected comparator set")
    for pin in manifest["inputs"].values():
        read_pinned(root / pin["path"], pin["sha256"])
    return manifest


def context(case_id, missing):
    return {
        "population_id": "synthetic:e05:" + case_id,
        "citation_universe": "synthetic:e05-closed-counts-v1",
        "as_of": "2026-01-01T00:00:00Z",
        "identity_policy": "exact-unique-synthetic-work-ids",
        "counting": "whole-publications-single-synthetic-group",
        "self_citations": "included-in-supplied-counts",
        "g_convention": "capped-at-actual-n-no-fictitious-works",
        "missing": "bounds" if missing else "reject",
    }


def make_case(case_id, counts, expected):
    case = {
        "id": case_id,
        "context": context(case_id, None in counts),
        "observations": [{"id": case_id + "/work-" + str(i),
                          "citations": None if c is None else str(c)}
                         for i, c in enumerate(counts)],
        "expected": expected,
    }
    validate_case(case)
    return case


def validate_case(case):
    if not isinstance(case, dict) or set(case) != {"id", "context", "observations", "expected"}:
        raise ContractError("invalid case fields")
    if not isinstance(case["id"], str) or not case["id"] or len(case["id"]) > 128:
        raise ContractError("invalid case identity")
    rows = case["observations"]
    if not isinstance(rows, list) or len(rows) > MAX_WORKS:
        raise ContractError("case exceeds independent oracle budget")
    ids = set()
    unknown = False
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "citations"}:
            raise ContractError("invalid observation")
        if not isinstance(row["id"], str) or not row["id"] or row["id"] in ids:
            raise ContractError("empty or duplicate work identity")
        ids.add(row["id"])
        if row["citations"] is None:
            unknown = True
        elif decimal(row["citations"]) > U64_MAX:
            raise ContractError("count exceeds u64")
    if case["context"] != context(case["id"], unknown):
        raise ContractError("unmatched corpus/cutoff/missingness convention")
    if not isinstance(case["expected"], dict) or set(case["expected"]) != set(METRICS):
        raise ContractError("missing expected metrics")
    for metric, bounds in case["expected"].items():
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise ContractError("invalid expected interval")
        low = decimal(bounds[0])
        if bounds[1] is None:
            if metric != "total" or not unknown:
                raise ContractError("unidentified upper total only for missing counts")
        else:
            high = decimal(bounds[1])
            if low > high or (metric != "total" and high > len(rows)):
                raise ContractError("invalid actual-N bounds")
            if unknown and metric == "total":
                raise ContractError("missing counts have no identified upper total")


def load_cases(root, manifest):
    def data(key):
        pin = manifest["inputs"][key]
        return strict_json(read_pinned(root / pin["path"], pin["sha256"]))

    cases = []
    for item in data("oracles")["cases"]:
        counts = item["counts"]
        if any(type(c) is not int or not 0 <= c <= U64_MAX for c in counts):
            raise ContractError("legacy oracle count is not an exact integer")
        expected = {m: [str(item["expected"][m])] * 2 for m in METRICS}
        cases.append(make_case("existing/" + item["id"], counts, expected))
    for index, item in enumerate(data("bounds")["cases"]):
        counts = item["counts"]
        if any(c is not None and (type(c) is not int or not 0 <= c <= U64_MAX) for c in counts):
            raise ContractError("invalid bounds oracle count")
        expected = {m: [str(item["lower"][m]), str(item["upper"][m])]
                    for m in ("h", "g", "i10")}
        # This is fixture metadata only, never a value attributed to a comparator.
        known = str(sum(c for c in counts if c is not None))
        expected["total"] = [known, None if None in counts else known]
        cases.append(make_case("existing/bounds-" + str(index), counts, expected))
    for item in data("known_answers")["cases"]:
        counts = [None if c is None else decimal(c) for c in item["counts"]]
        cases.append(make_case("known/" + item["id"], counts, item["expected"]))
    if not cases or len(cases) > MAX_CASES or len({c["id"] for c in cases}) != len(cases):
        raise ContractError("invalid case population")
    return cases


def wire_case(case):
    # In particular, do not send expected answers to an external worker.
    return {key: case[key] for key in ("id", "context", "observations")}


def input_digest(case):
    return digest(canonical_bytes(wire_case(case)))


def preflight(backend, case, metric):
    if backend not in SUPPORT or metric not in SUPPORT[backend]:
        return "unsupported_method"
    counts = [row["citations"] for row in case["observations"]]
    if None in counts:
        return "unsupported_missing_counts"
    if backend == "bibliometrix":
        if not counts:
            return "unsupported_empty_population"
        if sum(decimal(c) for c in counts) > SAFE_R_INTEGER:
            return "unsupported_integer_range"
    return None


def result_row(case, backend, metric, status, actual=None):
    return {
        "backend": backend, "case_id": case["id"], "metric": metric,
        "input_sha256": input_digest(case), "actual_n": str(len(case["observations"])),
        "observed_n": str(sum(r["citations"] is not None for r in case["observations"])),
        "expected_lower": case["expected"][metric][0],
        "expected_upper": case["expected"][metric][1],
        "actual": actual, "status": status,
        "qualification": "unqualified_independent_probe",
    }


def compare_value(case, backend, metric, actual):
    decimal(actual)  # No numerical coercion, tolerance, clipping or averaging.
    lower, upper = case["expected"][metric]
    if lower != upper:
        raise ContractError("point comparator cannot qualify an interval")
    return result_row(case, backend, metric,
                      "matched" if actual == lower else "mismatch", actual)


def validate_results(backend, cases, results):
    if not isinstance(results, list):
        raise ContractError("worker results are not a list")
    expected = {c["id"]: c for c in cases}
    found = {}
    for result in results:
        if not isinstance(result, dict) or set(result) != {"case_id", "input_sha256", "actual_n", "metrics"}:
            raise ContractError("invalid worker result fields")
        key = result["case_id"]
        if not isinstance(key, str) or key not in expected or key in found:
            raise ContractError("unknown or duplicate worker case")
        case = expected[key]
        if result["input_sha256"] != input_digest(case) or result["actual_n"] != str(len(case["observations"])):
            raise ContractError("worker changed scope, identities, counts or actual N")
        if not isinstance(result["metrics"], dict) or set(result["metrics"]) != set(SUPPORT[backend]):
            raise ContractError("missing or extra worker metric")
        for value in result["metrics"].values():
            decimal(value)
        found[key] = result
    if set(found) != set(expected):
        raise ContractError("worker omitted cases")
    return found


def qualification_status(root, manifest):
    # E04 admission remains the coordinator's responsibility. Merely adding a
    # similarly named receipt or setting a status cannot admit a candidate here.
    registry = strict_json((root / "conductor/evaluation-programme.json").read_text())
    tasks = [t for t in registry["tasks"] if t["id"] == "E04"]
    if len(tasks) != 1:
        raise ContractError("ambiguous E04 prerequisite")
    return {
        "state": "blocked_e04", "observed_e04_state": tasks[0]["state"],
        "production_numerical_qualification": False,
        "accepted_upstream_commit": None, "accepted_e04_receipt_sha256": None,
        "contract_snapshot_sha256": manifest["inputs"]["method"]["sha256"],
        "reason": "Exact E04 source/contract/toolchain admission is not supplied by this lane.",
    }


def verify_source(source, pin):
    for path, sha in pin["files"].items():
        read_pinned(Path(source) / path, sha)


def validate_response(backend, cases, response, pin, returncode):
    if not isinstance(response, dict):
        raise ContractError("worker response is not an object")
    if response.get("status") == "blocked_environment" and returncode == 3:
        return response
    if returncode != 0 or response.get("status") != "executed":
        raise ContractError("worker did not report execution")
    if response.get("protocol") != PROTOCOL or response.get("backend") != backend:
        raise ContractError("worker protocol/backend mismatch")
    if response.get("source_sha256") != pin["files"][pin["entrypoint"]]:
        raise ContractError("worker source mismatch")
    runtime = response.get("runtime")
    required = ({k: pin["runtime"][k] for k in ("implementation", "python")}
                if backend == "pybibx" else pin["runtime"])
    if runtime != required:
        raise ContractError("worker runtime differs from pinned environment")
    validate_results(backend, cases, response.get("results"))
    return response


def execute_worker(root, backend, cases, source, manifest, rscript=None):
    pin = manifest["comparators"][backend]
    verify_source(source, pin)
    if backend == "pybibx":
        if (platform.python_version() != pin["runtime"]["python"] or
                platform.python_implementation() != pin["runtime"]["implementation"]):
            return {"status": "blocked_environment", "runtime": {
                "python": platform.python_version(), "implementation": platform.python_implementation()}}
        command = [sys.executable, "-I", "-B", str(root / AREA / "pybibx_worker.py"),
                   "--source", str(Path(source).resolve()), "--manifest", str(root / AREA / "manifest.json")]
    else:
        executable = rscript or shutil.which("Rscript")
        if executable is None:
            return {"status": "blocked_runtime", "reason": "Rscript is unavailable"}
        command = [str(executable), "--vanilla", str(root / AREA / "bibliometrix_worker.R")]
    payload = {
        "protocol": PROTOCOL,
        "cases": [dict(wire_case(c), input_sha256=input_digest(c)) for c in cases],
        "pin": pin,
    }
    if backend == "bibliometrix":
        # Pass the exact already-hashed bytes, avoiding a second unverified read.
        payload["source_text"] = read_pinned(Path(source) / "R/Hindex.R", pin["files"]["R/Hindex.R"]).decode("utf-8")
    encoded = canonical_bytes(payload)
    if len(encoded) > 2_000_000:
        raise ContractError("worker input budget exceeded")
    proc = subprocess.run(command, input=encoded, capture_output=True, timeout=30)
    if len(proc.stdout) > 2_000_000 or len(proc.stderr) > 64_000:
        raise ContractError("worker output budget exceeded")
    if proc.returncode not in (0, 3):
        raise ContractError("worker failed with exit " + str(proc.returncode))
    response = strict_json(proc.stdout)
    return validate_response(backend, cases, response, pin, proc.returncode)


def run_probe(root, manifest, cases, sources, rscript=None):
    if len(cases) > MAX_CASES or len({c["id"] for c in cases}) != len(cases):
        raise ContractError("invalid probe case count")
    for case in cases:
        validate_case(case)
    rows, executions = [], {}
    for backend in SUPPORT:
        eligible = [c for c in cases if preflight(backend, c, "h") is None]
        if backend not in sources:
            execution = {"status": "blocked_source", "reason": "No explicit pinned local source supplied"}
        elif not eligible:
            execution = {"status": "unsupported_cases"}
        else:
            try:
                execution = execute_worker(root, backend, eligible, sources[backend], manifest, rscript)
            except (ContractError, OSError, subprocess.TimeoutExpired) as error:
                execution = {"status": "error", "reason": type(error).__name__ + ": " + str(error)}
        executions[backend] = execution
        results = ({r["case_id"]: r for r in execution["results"]}
                   if execution["status"] == "executed" else {})
        for case in cases:
            for metric in METRICS:
                status = preflight(backend, case, metric)
                if status:
                    rows.append(result_row(case, backend, metric, status))
                elif execution["status"] == "executed":
                    rows.append(compare_value(case, backend, metric, results[case["id"]]["metrics"][metric]))
                else:
                    rows.append(result_row(case, backend, metric, execution["status"]))
    return {
        "schema_version": "org.citelattice.e05-probe/1.0.0",
        "manifest_sha256": digest((root / AREA / "manifest.json").read_bytes()),
        "fixture_set_sha256": digest(canonical_bytes(cases)),
        "case_count": len(cases), "qualification": qualification_status(root, manifest),
        "harness_runtime": {"implementation": platform.python_implementation(),
                            "python": platform.python_version(), "platform": platform.platform()},
        "executions": executions, "rows": rows,
        "summary": dict(sorted(Counter(r["status"] for r in rows).items())),
    }


def write_parquet(report, path, manifest):
    import pyarrow as pa
    import pyarrow.parquet as pq

    if pa.__version__ != manifest["parquet_runtime"]["pyarrow"]:
        raise ContractError("un-pinned Parquet runtime")
    fields = ("backend", "case_id", "metric", "input_sha256", "actual_n", "observed_n",
              "expected_lower", "expected_upper", "actual", "status", "qualification")
    metadata = {key: str(report[key]).encode("ascii")
                for key in ("schema_version", "manifest_sha256", "fixture_set_sha256")}
    metadata[b"production_numerical_qualification"] = b"false"
    schema = pa.schema([pa.field(f, pa.string(), nullable=f in {"actual", "expected_upper"})
                        for f in fields], metadata=metadata)
    table = pa.Table.from_pylist(report["rows"], schema=schema)
    # Exclusive creation: an existing evidence artifact is never overwritten.
    with Path(path).open("xb") as stream:
        pq.write_table(table, stream, compression="NONE", version="2.6")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pybibx-source", type=Path)
    parser.add_argument("--bibliometrix-source", type=Path)
    parser.add_argument("--rscript", type=Path)
    parser.add_argument("--json", type=Path, help="Create a full evidence report (refuses overwrite)")
    parser.add_argument("--parquet", type=Path, help="Create exact-string comparison rows")
    parser.add_argument("--require-qualified", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(ROOT)
        cases = load_cases(ROOT, manifest)
        sources = {b: p for b, p in (("pybibx", args.pybibx_source),
                                     ("bibliometrix", args.bibliometrix_source)) if p is not None}
        report = run_probe(ROOT, manifest, cases, sources, args.rscript)
        if args.json:
            with args.json.open("x", encoding="utf-8") as stream:
                json.dump(report, stream, sort_keys=True, separators=(",", ":"))
                stream.write("\n")
        if args.parquet:
            write_parquet(report, args.parquet, manifest)
        brief = {k: v for k, v in report.items() if k not in {"rows", "executions"}}
        brief["executions"] = {b: {k: v for k, v in e.items() if k != "results"}
                               for b, e in report["executions"].items()}
        print(json.dumps(brief, sort_keys=True, indent=2))
        if report["summary"].get("mismatch", 0) or report["summary"].get("error", 0):
            return 1
        if args.require_qualified or not any(e["status"] == "executed" for e in report["executions"].values()):
            return 3
        return 0
    except (ContractError, OSError, ImportError) as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
