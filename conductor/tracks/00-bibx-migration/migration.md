# Design.2 migration reconciliation — 2026-11-27

Receiving revision: `c1654c5c0453e03fde38aabdfbf8fedc2e4a5a84`. Historical baseline: bibx design.2
(2026-11-10), recovered companion artifacts bibx-design-expansion.md,
bibx-imaging-contracts.md, bibx-verification-design2.md and
bibx-capability-coverage.json. The latter is preserved here as a structurally
re-serialized JSON snapshot, not a claim of byte identity to an archive.
The complete bibx-contracts-design2.zip was not recovered from accessible
GitHub, file library or Drive searches. The prior verification report describes
source-only archive delivery and unusable historical Git metadata; do not
reconstruct or claim history from descriptions.

## Exact catalogue comparison

147 unique historical IDs and 147 unique receiving IDs; 147 matched, zero
missing and zero additional. 0 family labels and 73 priorities
differ (case-insensitive priority comparison). Historical titles, contract
families, dependency owners, source lists, definition status and acceptance
criteria are preserved in the snapshot, not substituted into the current
catalogue or used to promote any method. The historical exclusions and source
versions are preserved. The current inventory remains canonical for current
status; independent per-method verification remains Track 12.

## Receiving path reconciliation (design-level, not archive file-by-file)

| Historical design area | Receiving path | Disposition |
| --- | --- | --- |
| Canonical CSL and scholarly stream | contracts/interop; crates/citelattice-ingest | Scoped existing implementation; producer and durable replay held (01) |
| Outcome inventory | contracts/methods/catalog.json | All 147 IDs conserved; historical metadata retained separately |
| Method, source, result and version identities | crates/citelattice-core/src/contracts; contracts/json-schema | Existing typed contract families; complete old API parity held |
| Evidence scenes and rendering | crates/citelattice-visualize; docs/imaging.md | Annual scene slice; advanced layout, LOD and independent fidelity held (07) |
| Output and bundle contracts | crates/citelattice-export; docs/outputs.md | Scoped portable/transactional outputs; PDF and conservation held (08/12) |
| Research objects and linked ecosystem | docs/dimensions.md; docs/studies/innovation-voi.md | Planned/contract-only; no provider equivalence claimed |
| Optional backend probes | backend-probes | Existing isolated declarations; qualification held (09) |
| Citation/graph analytics | crates/citelattice-analysis; crates/citelattice-network | Newer receiving implementation; do not overwrite with scaffold |
| Conductor | vendor/gemini-conductor; conductor/ | Existing upstream gitlink retained; brownfield setup repair proposed |
| Original source files, lockfile and history | Not available for inspection | Held: recover archive and compare; do not restore stale dependencies blindly |

This manifest is an interim reconciliation, not closure. Existing exact CI
receipts, open independent comparator/conservation lanes and security work are
not superseded. A full source manifest and exact API/native qualification are
still necessary under Track 00's original acceptance contract.
