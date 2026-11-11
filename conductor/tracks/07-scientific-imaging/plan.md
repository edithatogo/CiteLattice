# Track 07 scoped execution plan

1. [x] Establish baseline authoritative annual table and contract types.
2. [x] Add red-first Rust tests for mark-to-row conservation, 17+ years, precision overflow, duplicate years, denied export and mark budget.
3. [x] Implement pure scoped `build_annual_scene` using reusable Serde/JCS/sha2 and existing source counts; no new graphics runtime required.
4. [x] Add Vega-Lite v5 data specification, accessible exact-count rows, safe static SVG and distinct scene/render identities.
5. [ ] Observe rustfmt, Clippy, all Rust tests and Python JSON Schema tests at exact PR head.
6. [ ] Independently check generated SVG rect values and Vega-Lite rows against Arrow/Parquet and the signed source data; include large/corrupted inputs.
7. [ ] Add LOD and aggregate-membership conservation, temporal layout stability, uncertainty layers and independent cross-source identity resolution.
8. [ ] Evaluate perception and misleading-change detection with prespecified held-out scenarios; independent rerun for any beyond-frontier claim.

```sh
cargo fmt --all -- --check
cargo test -p citelattice-visualize
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

Output remains an in-memory scene. Rendering SVG or declaring Vega-Lite does not establish browser accessibility, publication-quality PDF or complete research-object provenance.
