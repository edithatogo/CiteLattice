# Optional backend evaluations

Versions are proposals, not confirmed compilable compatibility sets. This package
is deliberately outside the root workspace and has no Cargo.lock, so it does not
break the small portable contract core. Do **not** claim the feature flags
have built until one-feature-at-a-time tests pass on a pinned toolchain.

Qualify: [Polars], Arrow IPC/Parquet, Petgraph, DataFusion, workbook writer,
static plotting, local FastEmbed and SVG rasterisation.
Avoid simultaneous DataFusion/Polars dependencies in the core;
check the Arrow version matrix before compiling combined features.

Other evaluated alternatives: Raphtory for temporal graph modelling, rustworkx-core
for high-performance graph kernels, Leiden implementations, redb/Fjall for state,
Candle for local models, Plotters and Vega-Lite for figures, Typst for reports.
Select by observed capability, licence, maintenance and benchmark evidence, not hype.
