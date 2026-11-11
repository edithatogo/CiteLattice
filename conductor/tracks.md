# Reconciled executable track registry

| Track | Status | Outcome | Proof |
| --- | --- | --- | --- |
| 00 — bibx design.2 migration | Incomplete | Import and reconcile useful previous source/contracts/history; use CiteLattice crate and repo names | Change manifest, complete compile/test and API parity |
| 01 — Searchright + formats | Bounded event consumer CI passed; producer and durable replay pending | Canonical CSL, proposed stream, Arrow/Parquet, other reference formats | Producer/consumer golden fixtures, compiled replay tests and durable checkpoint |
| 02 — Methods registry | Planned | bibliometrix/PyBibX/DImensions/lower-friction outcome definition and oracles | Publication references, independent numerical outputs |
| 03 — Entity and graph analytics | Initial Petgraph baseline on main; broader scope pending | Stable IDs, coauthors/coupling/co-citation/main paths | Source vs result comparison, incremental/full replay |
| 04 — Local inference and dynamics | Planned | Topic/novelty/semantic change optional embeddings | Model revisions, calibration and transparent baseline comparison |
| 05 — Dimensions research objects | Planned | Grants, patents, trials, policy, datasets, cross-domain links | Rights, typed relationships, coverage/uncertainty |
| 06 — Versioning and reproducible outputs | Versioned identities and typed outputs implemented; full invalidation pending | Separate source/method/table/scene/render versions, complete data exports | Invalidation, schema and bundle round trips |
| 07 — Beyond-frontier imaging | Evidence-linked annual scenes passed CI; independent evaluation pending | Mark-to-row lineage, multiverse comparisons, LOD, uncertainty and accessibility | Geometry, disclosure and conservation tests |
| 08 — Reporting and distribution | Transactional writer passed CI; durable publication and external PDF pending | Reproducible XLSX/PDF/HTML/RO-Crate packages | Format validation and snapshot checks |
| 09 — Dependency evaluation | Scaffolded | Polars/graph/datafusion/render/backend substitutions only on evidence | Isolated compile, security, benchmark and parity |
| 10 — Lean agent harness/security | Planned | CodeQL, Gitleaks, deny/audit/vet, fuzz/property/mutation with adaptive CI | Exact revision observed hosted CI |
| 11 — Innovate/Voiage research | Specified | Hold-out prediction, decision-value estimation | Registered/frozen protocol and independent analysis |
| 12 — [Scientific evaluation](tracks/12-scientific-evaluation/spec.md) | Core method slices passed native CI; independent scientific evaluation pending | Citation kernels plus E01–E12/R01–R04 verification/research programme | Python reference/schema checks; native and external evidence pending |

Each planned track should have one small implementation PR at a time. Avoid automatic phase/subissue multiplication. Do not claim the previous scaffold has been migrated until it is actually present and compiling.

### Verified source increments (not scientific-method certification)

Track 12 coordinates the [citation analysis plan](tracks/12-scientific-evaluation/plan.md),
with responsibilities in 01/02/06/07/09/10/11. `citelattice-analysis` contains
source-authored h/g/i10/totals, missing-count bounds, versioned fingerprints and
bounded request JSONL. The 147-item catalogue remains an inventory; this narrow
method profile and its evidence are in `contracts/methods/citation-summary.v1.json`.
No other track's historical status is promoted by these files.

### Verified integration decisions (2026-11-12)

- [PR #10](https://github.com/edithatogo/CiteLattice/pull/10): bounded coauthors and safe complete SVG — merged; `rust-core` and `schemas` passed.
- [PR #11](https://github.com/edithatogo/CiteLattice/pull/11): staged/verified transactional scientific package — merged; both required jobs passed.
- [PR #13](https://github.com/edithatogo/CiteLattice/pull/13): annual evidence-linked scene/Vega-Lite/SVG — merged; both required jobs passed.
- [PR #12](https://github.com/edithatogo/CiteLattice/pull/12): bounded single-epoch scholarly event consumer — merged; both required jobs passed.
- [PR #9](https://github.com/edithatogo/CiteLattice/pull/9) remains **draft** until offline runners, tools, model assets and real scans are independently qualified; no mock-only promotion.
- [Searchright #812](https://github.com/edithatogo/searchright/pull/812) remains **unmerged**: `rustix` advisory fixed, but 259 cargo-vet exemptions expired. No automatic extension or source-audit claim.

These are scoped compiler/tests/schema outcomes. They do **not** establish live Searchright producer compatibility, portable crash recovery, complete independent bibliometrix/PyBibX validation, safety certification or beyond-frontier research performance. [Exact CI evidence](../verification/ci-acceptance-2026-11-12.json) is separate from Conductor planning.


### Next executable dependency order

1. Searchright actual event producer and CiteLattice consumer-driven conformance at pinned source revisions; embargo rights and lost-reference coverage are explicit.
2. Durable source-event spool and checkpoint/recovery with power-loss, duplicate and deletion tests; match full replay.
3. Independent table-to-Parquet/XLSX/Vega-Lite/SVG/Typst semantic and disclosure audits; source-to-mark conservation.
4. Pinned bibliometrix/PyBibX method oracles and source-coverage/author-resolution validation before new algorithm families.
5. Execute E01–E12 and R01–R04 with held-out comparative protocols. Never promote beyond-frontier from code presence or a visually attractive chart.
