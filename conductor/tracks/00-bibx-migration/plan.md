# Track 00 implementation plan

## Foundation and baseline
- [x] Verify existing pinned upstream submodule and initial CiteLattice main.
- [x] Compare all 147 design.2 outcome IDs to the current method inventory;
      preserve the exact historical catalogue separately.
- [x] Repair missing brownfield Conductor context and native track links; run
      the upstream resume script and verify all checklist members, plugin pin
      and style-guide identity on the exact hosted checkout.

## Source migration
- [x] Recover both original archives, check CRC, hash and enumerate all original
      paths; record that historical root Git commit history is unrecoverable.
- [x] Record a source-by-source reconciliation and retain all seven original
      schema/fixture pairs byte-exactly as non-production reference contracts.
- [~] Independently review the source/API crosswalk; resolve any useful missing
      APIs or document intentional differences without promoting scientific
      methods or overwriting current implementations.
- [ ] Observe updated-head native build, lint, schema and parity evidence;
      reconcile receiving-main CI after integration.
- [ ] Close Track 00 only when its original acceptance gates pass.

The source acquisition blocker is resolved. The old scaffold contains 66 loose
root Git blobs but no commit objects or recoverable branch tip; no synthetic
history is created. Original design.2 Python checks passed 22/22; this is not
evidence of Rust compilation or native API equivalence. Agent-host activation
and exact updated-head qualification remain separate.

## Observed setup receipt

At `35ef3876434adf9954e5b1f367d76ff227a29156`, hosted schema job
`140232230823` in run `45915076179` checked out the pinned upstream submodule
and passed all 22 Python tests, including the actual upstream resume checklist.
Rust job `140232230474` and FAIR/privacy runs `45915076189` / `45915076161`
also passed. New changes require a fresh receipt. The local setup instructions
now use the whole suite and the native registry labels the three partially
implemented tracks as in progress. The detailed archival API reconciliation
and full historical source are not part of this public change. Track 00 remains
open; do not infer archive-wide API parity or receiving-main integration.
