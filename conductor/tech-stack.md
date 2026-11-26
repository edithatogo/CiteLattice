# Technology stack

Observed baseline: c1654c5c0453e03fde38aabdfbf8fedc2e4a5a84.

- Rust edition 2024, Cargo resolver 3. Six production crates:
  citelattice-core, citelattice-analysis, citelattice-ingest, citelattice-export,
  citelattice-network and citelattice-visualize.
- Serde/serde_json, canonical JSON and content digests; typed Arrow/Parquet,
  Petgraph, rust_xlsxwriter, Vega-Lite and SVG in scoped existing implementations.
  Typst source is not a qualified PDF renderer.
- Python 3.13 structural/reference tests with pinned jsonschema and RFC3339
  validation; native cargo fmt, check, Clippy and workspace tests in GitHub Actions.
- Optional excluded backend-probes workspace; no mandatory provider, GPU, LLM,
  database or remote inference. Evaluate changes in [dependencies](dependencies.md).
- Git and pinned Conductor plugin 0.3.0; repository-local source pin, not a
  global installation. See [setup](setup.md).

Cargo.lock is absent at the observed baseline; reproducible dependency admission
and security qualification remain separate gates. See [versioning](../docs/versioning.md).
