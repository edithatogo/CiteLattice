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
