# Track 01 executable plan

1. [x] Inspect Searchright proposal and existing native JSONL reader.
2. [x] Write Rust consumer tests covering the shared fixture, exact duplicate and conflicting event ID, stream gap, invalid date, overflow, correction, deletion, source lineage, privacy and bounds.
3. [x] Author standalone `events.rs` with Serde, JCS canonicalization, SHA-256, RFC3339, bounded memory and explicit redacted errors.
4. [x] Add machine-readable result snapshot contract and Python negative schema tests.
5. [ ] Observe CI at the exact branch SHA; fix formatting, Clippy, cargo and failing native tests before merge.
6. [ ] Obtain actual Searchright-generated event bytes (Searchright #812 currently proposal) and implement producer+consumer compatibility suite.
7. [ ] Durable spool with write-ahead record + checkpoint and crash injection; compare full replay, ensure rights-deletion outcomes and no stale output caches.
8. [ ] Add epoch rollover/migration, historical revision queries and dependency invalidation to scientific outputs.
9. [ ] Build a real CSL/Arrow/Parquet adapter with loss and rights receipts.
10. [ ] Run independent methods and drift/format verification and update capability evidence.

## Verification commands

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test -p citelattice-ingest --test events
cargo test --workspace
python -m unittest discover -s tests -v
```

The current consumer is in-memory with no crash guarantee. A valid synthetic event and a schema match do not demonstrate a producer actually emitting that event. Results preserve hashed source identifiers but cannot reconstruct full CSL records; the source owner retains them.

## Serde suitability and maximal justified reuse — 18 November 2026 (planning)

The workspace already declares `serde` derive and `serde_json` with `raw_value`; `citelattice-ingest` uses `serde_json_canonicalizer` and SHA-256 for reproducible event records. `citelattice-export` separately uses Arrow/Parquet and XLSX. This separation is **appropriate**: Serde does not replace JCS canonicalization, numerical semantics or columnar storage; neither should interchangeable JSON/CSL DTOs erase upstream rights, source identifiers, corrections or deletions.

- [ ] Inventory each stable event, CSL and result-snapshot DTO for explicit schema/format versions, integer/float loss, unknown-field policy, duplicate-key rejection and error context; keep extension/unknown provider payloads lossless where the contract demands.
- [ ] Compare source-event JSONL ingest and output records against **real Searchright producer bytes**, not just self-produced Serde round trips. Retain independent canonical-byte/hash tests, schema fuzzing, malformed/oversize input and Arrow/Parquet conservation.
- [ ] Evaluate any repeated manual JSON formatting *only where present*, with benchmarks and deleted-code/contract parity; no blanket dependency replacement or false claim of optimisation.
- [ ] Keep Track 01 unfinished producer-consumer, spool/checkpoint, and CI gates open. Record exact source/consumer pins and original rights/deletion evidence; no new track or runtime claim from this plan note.
