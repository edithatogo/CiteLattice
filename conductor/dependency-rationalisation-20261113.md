# Rust dependency rationalisation — CiteLattice (2026-11-13)

**Status:** scoped Conductor adoption contract; code substitutions not yet implemented or certified by this file.

## Repository-specific decisions

- Reconcile existing track 09 (dependency evaluation) and track 12 (scientific evaluation); do not create competing track numbers.
- **Verified:** analysis uses Proptest and Thiserror; network uses Petgraph; the `citation-summary` CLI manually parses a single command and JSONL stream.
- **Conditional:** Clap only if its CLI improvements outweigh added dependency cost, with golden JSONL/stdout/stderr and invalid-argument tests.
- **Evaluate:** Polars for tabular analytics while retaining Petgraph and Arrow/Parquet contracts; Rayon only for independently measured deterministic kernels; Itertools only when it removes substantial bespoke iterator logic.
- **Extend:** Proptest for graph/source-order properties, Criterion for validated scientific kernels and Insta only for compact redacted versioned output/schema snapshots.
- **Retain:** canonical JSON hashing and provenance; no Regex substitution for scholarly format parsers; reuse Searchright/Sourceright/Citeweft where boundaries match.

## Delivery and acceptance contract
- Reconcile existing Conductor tracks and ownership before editing code; do not duplicate completed tasks.
- Write a failing behavioural/regression test first for each runtime change; preserve APIs, schema versions, stdout/stderr, exit codes, error codes and MSRV or explicitly version breaking changes.
- Run the existing repo gates: targeted tests, full workspace tests, fmt, clippy and contract/interop checks. Record actual passing CI SHA; this document is planning, not validation.
- Inventory duplicate crate versions/features with `cargo tree -d` and `cargo tree -e features`; review unused dependencies, `cargo audit`, `cargo deny`, licence, MSRV, SBOM and release implications where applicable.
- Benchmark performance proposals with fixed fixtures and baseline/candidate receipts, including correctness, memory, CPU and determinism.
- Decision for each candidate must be recorded as adopt, retain, reject or defer with evidence, risks and rollback.
- Do not expose identifiable, secret, copyrighted or otherwise restricted raw data in tracing, snapshots, benchmarks or CI artifacts.
