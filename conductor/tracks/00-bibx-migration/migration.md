# Design.2 migration reconciliation — 2026-11-27

The original design.2 ZIP and preceding scaffold ZIP were recovered from the
owner's Library; both passed ZIP integrity/CRC checks. Their exact archive
identities, all 147 project paths and 28 vendored paths are recorded in
[source-manifest.json](source-manifest.json). The initial scaffold's root Git
directory contains 66 loose blobs but no commit objects, pack or recoverable
branch tip. No original commit sequence is reconstructed.

The historical catalogue is byte-exact (Git blob 70630c859c39137a3eff5ff7c93a13712a3b04b1).
All 147 IDs and family labels match the current catalogue; 73 priority
assignments differ (case-insensitive comparison). Original priorities: 89 MUST,
58 SHOULD; current: 132 must, 15 should. The historical values, titles,
definitions, sources and acceptance criteria remain distinct from current
priorities and qualification.

All seven original schema/fixture pairs are retained in
`baseline-contracts.json.gz`, a UTF-8 JSON map from original project-relative
path to original file contents. Git blob hashes for all 14 files are recorded
in the manifest; current shared-stream schema and fixture have the same Git
blob identities as the original. Other contracts are historical reference
material, not replacements for current wire contracts. Run
`python -m unittest discover -s tests -p test_track00_migration.py -v` for
hash, inventory, schema and native setup-resume checks.

The recovered original design.2 source passed 16 original design contract tests
and 6 original shared-stream tests in Python (22/22). No original Rust compiler
or native equivalence result is claimed.

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
| Original source files, lockfile and history | source-manifest.json; original archive | source inventory retained; exact commit history unavailable; stale dependencies not restored |

The source manifest records all original project paths and the relevant current
successor or owning track, including original track mappings. A successor is
not an API equivalence assertion. Historical runtime sketches, optional
backend dependencies, source-provider credentials and broad proposed APIs are
not silently introduced into the receiving production workspace. Remaining
native API discrepancies require intentional-difference review or tested
implementation. Existing parallel PRs and scientific acceptance gates remain
unchanged.
