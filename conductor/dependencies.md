# Prefer dependencies over bespoke infrastructure

| Domain | Preferred candidate | Alternative/gate |
| --- | --- | --- |
| Columnar operations | Polars LazyFrames | DataFusion for Arrow streaming SQL when benchmarks justify |
| Tables/wire | Apache Arrow IPC, Parquet | Avoid incompatible versions and type loss |
| Graph | Petgraph, rustworkx-core | Raphtory for temporal storage only after correctness comparison |
| Community detection | Maintained Leiden implementation | Test against published fixtures, controlled seeds |
| Persistence | redb | Fjall benchmark and crash replay |
| Statistics/ML | statrs, linfa | Evidence-backed custom domain algorithms |
| Embedding | FastEmbed or Candle | Local-only model downloads opt-in, exact model hashes |
| Graphics | Plotters, Vega-Lite | resvg; optional wgpu based on measured benefit |
| Excel | rust_xlsxwriter / polars_excel_writer | Injected formula and truncated rows safety checks |
| PDF and reports | Typst, HTML | CiteLattice specifies content, renderer owns layout |
| Invalidation | Salsa-style dependency graph | Separate durable checkpoint/event state |

All external dependencies require licence and advisories check, isolated compile evidence, maintained API, and independently assessed numerical parity. The backend-probes manifest is intentionally **not verified** at this stage.
