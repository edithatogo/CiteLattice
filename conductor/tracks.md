# Reconciled executable track registry

| Track | Status | Outcome | Proof |
| --- | --- | --- | --- |
| 00 — bibx design.2 migration | Incomplete | Import and reconcile useful previous source/contracts/history; use CiteLattice crate and repo names | Change manifest, complete compile/test and API parity |
| 01 — Searchright + formats | Scaffolded | CSL-JSON, proposed stream, Arrow/Parquet, other reference formats | Producer/consumer golden fixtures, replay tests |
| 02 — Methods registry | Planned | bibliometrix/PyBibX/DImensions/lower-friction outcome definition and oracles | Publication references, independent numerical outputs |
| 03 — Entity and graph analytics | Initial Petgraph baseline on main; broader scope pending | Stable IDs, coauthors/coupling/co-citation/main paths | Source vs result comparison, incremental/full replay |
| 04 — Local inference and dynamics | Planned | Topic/novelty/semantic change optional embeddings | Model revisions, calibration and transparent baseline comparison |
| 05 — Dimensions research objects | Planned | Grants, patents, trials, policy, datasets, cross-domain links | Rights, typed relationships, coverage/uncertainty |
| 06 — Versioning and reproducible outputs | Scaffolded | Separate source/method/table/scene/render versions, complete data exports | Invalidation, schema and bundle round trips |
| 07 — Beyond-frontier imaging | Evidence-linked annual scene source; CI pending | Mark-to-row lineage, multiverse comparisons, LOD, uncertainty and accessibility | Geometry, disclosure and conservation tests |
| 08 — Reporting and distribution | Partial output adapters; transactional API under review | Reproducible XLSX/PDF/HTML/RO-Crate packages | Format validation and snapshot checks |
| 09 — Dependency evaluation | Scaffolded | Polars/graph/datafusion/render/backend substitutions only on evidence | Isolated compile, security, benchmark and parity |
| 10 — Lean agent harness/security | Planned | CodeQL, Gitleaks, deny/audit/vet, fuzz/property/mutation with adaptive CI | Exact revision observed hosted CI |
| 11 — Innovate/Voiage research | Specified | Hold-out prediction, decision-value estimation | Registered/frozen protocol and independent analysis |
| 12 — [Scientific evaluation](tracks/12-scientific-evaluation/spec.md) | Specified; initial source increment | Citation kernels plus E01–E12/R01–R04 verification/research programme | Python reference/schema checks; native and external evidence pending |

Each planned track should have one small implementation PR at a time. Avoid automatic phase/subissue multiplication. Do not claim the previous scaffold has been migrated until it is actually present and compiling.

### Current source increment (not a remote or native completion claim)

Track 12 coordinates the [citation analysis plan](tracks/12-scientific-evaluation/plan.md),
with responsibilities in 01/02/06/07/09/10/11. `citelattice-analysis` contains
source-authored h/g/i10/totals, missing-count bounds, versioned fingerprints and
bounded request JSONL. The 147-item catalogue remains an inventory; this narrow
method profile and its evidence are in `contracts/methods/citation-summary.v1.json`.
No other track's historical status is promoted by these files.

### Current integration queue (2026-11-11)

- PR #8 (Petgraph network baseline) was merged after its exact-head core CI passed.
- PR #10 (SVG completeness/overflow and bounded coauthor expansion) is open; its hosted CI was queued at last observation. Do not mark this work merged or verified.
- PR #9 (offline four-layer security) is open and **must not merge** until qualified self-hosted runners, local model weights and real offline scans are demonstrated; mock tests are insufficient.
- Transactional output publication is a separate scoped change, with staging, digest checks and non-overwriting rename. This is a same-filesystem visibility guarantee, not durable fsync or multi-directory transaction.
- Searchright #812 remains proposed; actual producer/consumer streaming is not yet demonstrated.

Prioritise exact-head CI for these PRs, then cross-format output integrity, versioned Searchright events, independent bibliometrix/PyBibX parity and held-out research studies. Keep evidence states independent of code presence.

### Track 07 implementation slice (2026-11-11)

`citelattice-visualize` constructs one deterministic annual evidence scene with exactly one mark and source-year row identity per source table row. It enforces source count conservation, unique sorted years, explicit annual bar budgets, safe JSON integer precision, an accessible exact-count table, Vega-Lite v5 data specification, and static SVG with row annotations and artifact/scene digests. A change of source input digest invalidates the scientific scene while a purely source-layout-neutral table revision can preserve the SVG bytes. **No external scientific map, GPU renderer, PDF, cross-source temporal alignment or human interpretation advantage is claimed.** The code requires native CI and independent geometry/rights audits.
