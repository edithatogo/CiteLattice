# Reconciled executable track registry

| Track | Status | Outcome | Proof |
| --- | --- | --- | --- |
| 00 — bibx design.2 migration | Incomplete | Import and reconcile useful previous source/contracts/history; use CiteLattice crate and repo names | Change manifest, complete compile/test and API parity |
| 01 — Searchright + formats | Native JSONL implemented; event consumer source pending CI | Canonical CSL, proposed stream, Arrow/Parquet, other reference formats | Producer/consumer golden fixtures, compiled replay tests and durable checkpoint |
| 02 — Methods registry | Planned | bibliometrix/PyBibX/DImensions/lower-friction outcome definition and oracles | Publication references, independent numerical outputs |
| 03 — Entity and graph analytics | Planned | Stable IDs, coauthors/coupling/co-citation/main paths | Source vs result comparison, incremental/full replay |
| 04 — Local inference and dynamics | Planned | Topic/novelty/semantic change optional embeddings | Model revisions, calibration and transparent baseline comparison |
| 05 — Dimensions research objects | Planned | Grants, patents, trials, policy, datasets, cross-domain links | Rights, typed relationships, coverage/uncertainty |
| 06 — Versioning and reproducible outputs | Scaffolded | Separate source/method/table/scene/render versions, complete data exports | Invalidation, schema and bundle round trips |
| 07 — Beyond-frontier imaging | Scaffolded | Mark-to-row lineage, multiverse comparisons, LOD, uncertainty and accessibility | Geometry, disclosure and conservation tests |
| 08 — Reporting and distribution | Planned | Reproducible XLSX/PDF/HTML/RO-Crate packages | Format validation and snapshot checks |
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

### Event consumer implementation increment (2026-11-11)

[Track 01](tracks/01-scholarly-events/spec.md) owns the bounded `org.scholarly.stream` consumer. Source-authored capabilities include canonical JCS payload hashing, strict decimal u64 counters, per-epoch sequence/lineage checks, idempotent duplicate events, correction pointers, source retraction/deletion, hashed privacy tombstones and no retained CSL title/abstract. The event snapshot contract is separately versioned.

This is a **single-epoch, in-memory, source-minimised consumer**, not durable replay, an authenticated producer, complete CSL parser or scientific graph update. Its native tests and CI are not yet observed. Subsequent tasks must add committed event spool/checkpoint atomicity, multi-epoch migration, genuine Searchright producer bytes and integration with scientific dirty-dependency tracking. Neither Searchright PR #812 nor these local results should be presented as admitted interoperability without exact producer+consumer tests.
