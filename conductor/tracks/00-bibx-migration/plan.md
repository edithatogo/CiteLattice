# Track 00 implementation plan

## Foundation and baseline
- [x] Verify existing pinned upstream submodule and initial CiteLattice main.
- [x] Compare all 147 design.2 outcome IDs to the current method inventory;
      preserve the recovered historical catalogue as a separate evidence snapshot.
- [x] Record observed contract/implementation lineage and missing archive.
- [~] Repair missing brownfield Conductor context and native track links; verify
      repository-local plugin and complete checklist on exact committed checkout.

## Source migration
- [ ] Recover the full bibx-contracts-design2.zip, record SHA-256 and inventory
      all original files and available history. Never invent missing Git objects.
- [ ] Reconcile every original source/contract/API to the receiving revision;
      retain or migrate useful missing pieces with regression tests and preserve
      current behavior. Explicitly justify obsolete/delegated files.
- [ ] Execute complete native build, lint, schema and API parity checks at exact
      PR head and receiving main, independently review the manifest.
- [ ] Close Track 00 only after the source and native acceptance gates pass.

Blocker: recovered companion design documents and catalogue are not the original
source ZIP. The legacy archive's historical Git metadata was not a usable
checkout according to its verification report. Full original API parity is
unverified. Hosted setup/contract checks and agent-host activation remain to be
observed.
