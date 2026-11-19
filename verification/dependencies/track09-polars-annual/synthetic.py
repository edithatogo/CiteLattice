"""Offline synthetic Track 09 annual-aggregation cases; no real records or providers.

This generator specifies reference expectations. It does NOT execute CiteLattice or Polars.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

SOURCE_SCHEMA = "org.searchright.bibliographic-record.v1"
FIXTURE_VERSION = "citelattice-track09-polars-annual-fixtures-v1"


def cases() -> dict[str, tuple[list[int | None], str | None]]:
    mixed = [-1, 2024, None, 2024, 0, None, 1999, 1999]
    return {
        "empty": ([], None),
        "mixed": (mixed, None),
        "permuted": (mixed, None),
        "undated": ([None, None, None], None),
        "dense-8192": ([None if i % 13 == 0 else 1980 + (i % 41) for i in range(8192)], None),
        "wide-512": ([1900 + i for i in range(512)], None),
        "duplicate-id": ([2020, 2021], "Duplicate"),
        "invalid-schema": ([2020], "InvalidContract"),
    }


def generate_bytes(years: list[int | None], *, fault: str | None = None) -> bytes:
    chunks: list[bytes] = []
    for i, year in enumerate(years):
        record = {
            "schema_version": "invalid.synthetic.version" if fault == "InvalidContract" else SOURCE_SCHEMA,
            "record_id": "SYN-000000" if fault == "Duplicate" and i == 1 else f"SYN-{i:06d}",
            "source_receipt_id": f"synthetic-receipt-{i % 3}",
            "native_id": f"synthetic-native-{i:06d}",
            "title": f"Synthetic work {i}",
            "kind": "article" if i % 2 == 0 else {"other": "synthetic-kind"},
            "publication_year": year,
            "authors": [],
        }
        chunks.append((json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
    return b"".join(chunks)


def expected_for(years: list[int | None], fault: str | None) -> dict:
    if fault is not None:
        return {"status": "rejected", "error_category": fault}
    # Independent Counter oracle: not generated from production BTreeMap outputs.
    grouped = Counter(year for year in years if year is not None)
    return {
        "status": "ok",
        "record_count": len(years),
        "undated": sum(year is None for year in years),
        "annual": [{"year": year, "count": grouped[year]} for year in sorted(grouped)],
    }


def _case_bytes(name: str, years: list[int | None], fault: str | None) -> bytes:
    data = generate_bytes(years, fault=fault)
    if name == "permuted":
        data = b"".join(reversed(data.splitlines(keepends=True)))
    return data


def _canonical_manifest() -> dict:
    entries = []
    for name, (years, fault) in cases().items():
        data = _case_bytes(name, years, fault)
        entries.append({
            "case_id": name,
            "filename": name + ".jsonl",
            "input_sha256": hashlib.sha256(data).hexdigest(),
            "input_bytes": len(data),
            "expected": expected_for(years, fault),
        })
    return {"fixture_version": FIXTURE_VERSION, "source": "synthetic-only", "cases": entries}


def write_bundle(out: Path) -> dict:
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a non-empty output directory")
    out.mkdir(parents=True, exist_ok=True)
    manifest = _canonical_manifest()
    for entry in manifest["cases"]:
        years, fault = cases()[entry["case_id"]]
        (out / entry["filename"]).write_bytes(_case_bytes(entry["case_id"], years, fault))
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_bundle(out: Path) -> dict:
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("cases"), list):
        raise ValueError("invalid fixture manifest")
    seen: set[str] = set()
    for entry in manifest["cases"]:
        if not isinstance(entry, dict):
            raise ValueError("invalid fixture entry")
        case_id, name = entry.get("case_id"), entry.get("filename")
        if case_id not in cases() or name != case_id + ".jsonl" or name in seen:
            raise ValueError("invalid or repeated fixture path")
        seen.add(name)
    if manifest != _canonical_manifest():
        raise ValueError("manifest oracle/provenance differs from deterministic recipe")
    for entry in manifest["cases"]:
        data = (out / entry["filename"]).read_bytes()
        if len(data) != entry["input_bytes"] or hashlib.sha256(data).hexdigest() != entry["input_sha256"]:
            raise ValueError("fixture byte integrity failed")
    return manifest

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--verify", action="store_true", help="verify an existing bundle without modifying files")
    args = parser.parse_args()
    if args.verify:
        manifest = verify_bundle(args.out)
    else:
        manifest = write_bundle(args.out)
        verify_bundle(args.out)
    print(f"synthetic Track09 bundle verified: {len(manifest['cases'])} cases")


if __name__ == "__main__":
    main()
