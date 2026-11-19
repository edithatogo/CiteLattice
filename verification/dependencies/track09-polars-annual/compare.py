"""Fail-closed gate for future two-run Track09 backend parity receipts.

Passing this gate with invented test receipts is a gate self-test, NOT backend qualification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from synthetic import verify_bundle


class ParityError(ValueError):
    """Receipt or cross-backend mismatch."""


def load_receipts(path: Path) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        case_id = entry.get("case_id")
        if not isinstance(case_id, str) or case_id in entries:
            raise ParityError("invalid or duplicate case_id in receipts")
        entries[case_id] = entry
    return entries


def _integer(value: object) -> bool:
    return type(value) is int and 0 <= value <= 18446744073709551615


def assert_receipt(expected_case: dict, found: dict) -> None:
    expected = expected_case["expected"]
    common = {"case_id", "input_sha256", "status"}
    fields = common | ({"record_count", "undated", "annual"} if expected["status"] == "ok" else {"error_category"})
    if set(found) != fields:
        raise ParityError("unknown, missing or potentially disclosing receipt fields")
    if found["case_id"] != expected_case["case_id"] or found["input_sha256"] != expected_case["input_sha256"]:
        raise ParityError("case/digest mismatch")
    if found["status"] != expected["status"]:
        raise ParityError("acceptance/rejection mismatch")
    if expected["status"] == "rejected":
        if found["error_category"] != expected["error_category"]:
            raise ParityError("error classification mismatch")
        return
    count, missing = found["record_count"], found["undated"]
    if not _integer(count) or not _integer(missing) or missing > count:
        raise ParityError("invalid record/undated counts")
    rows = found["annual"]
    if not isinstance(rows, list):
        raise ParityError("annual rows must be an array")
    previous_year = None
    aggregate = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"year", "count"}:
            raise ParityError("invalid annual row shape")
        year, amount = row["year"], row["count"]
        if type(year) is not int or not -(2**31) <= year < 2**31 or not _integer(amount) or amount == 0:
            raise ParityError("annual year/count precision or type mismatch")
        if previous_year is not None and year <= previous_year:
            raise ParityError("annual years not unique and sorted")
        aggregate += amount
        previous_year = year
    if aggregate != count - missing:
        raise ParityError("annual count conservation failed")
    if {key: found[key] for key in ("record_count", "undated", "annual")} != {
        key: expected[key] for key in ("record_count", "undated", "annual")
    }:
        raise ParityError("independent annual-count oracle mismatch")


def compare(bundle: Path, baseline_receipts: Path, candidate_receipts: Path) -> int:
    manifest = verify_bundle(bundle)
    expected_ids = {entry["case_id"] for entry in manifest["cases"]}
    baseline = load_receipts(baseline_receipts)
    candidate = load_receipts(candidate_receipts)
    if set(baseline) != expected_ids or set(candidate) != expected_ids:
        raise ParityError("missing or extra baseline/candidate cases")
    for entry in manifest["cases"]:
        case_id = entry["case_id"]
        assert_receipt(entry, baseline[case_id])
        assert_receipt(entry, candidate[case_id])
        if baseline[case_id] != candidate[case_id]:
            raise ParityError("baseline/candidate result differs")
    return len(expected_ids)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = compare(args.fixtures, args.baseline, args.candidate)
    except (ParityError, ValueError, KeyError, TypeError, OSError) as exc:
        print(f"FAIL Track09 parity gate: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"PASS Track09 parity gate: {count} receipt pairs match the synthetic oracle; execution provenance must be verified separately")


if __name__ == "__main__":
    main()
