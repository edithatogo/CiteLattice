# Reconciled executable track registry

| Track | Status | Outcome | Proof |
| --- | --- | --- | --- |
| 00 — bibx design.2 migration | Incomplete | Import and reconcile useful previous source/contracts/history; use CiteLattice crate and repo names | Change manifest, complete compile/test and API parity |
| 01 — Searchright + formats | Scaffolded | CSL-JSON, proposed stream, Arrow/Parquet, other reference formats | Producer/consumer golden fixtures, replay tests |
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
| 12 — Scientific evaluation | Planned | Broad validation and honest release claims | Independent oracles, differential comparator tests, versioned research reports |

Each planned track should have one small implementation PR at a time. Avoid automatic phase/subissue multiplication. Do not claim the previous scaffold has been migrated until it is actually present and compiling.
