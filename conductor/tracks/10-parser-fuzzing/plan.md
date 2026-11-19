# Track 10 parser fuzzing execution

- [x] Inspect current ingest boundaries, instructions and open PR ownership.
- [x] Add two executable native corpus/mutation tests using the real parser APIs.
  - `cargo +1.99.1 test -p citelattice-ingest --test fuzz_regressions`: 2 passed.
  - Root policy has no committed Cargo.lock; the isolated fuzzer commits its own lock.
- [x] Add the isolated coverage-guided target, synthetic seeds and bounded runner.
- [x] Add read-only PR/weekly workflow with exact tool pins and reproduction artifacts.
- [x] Execute a local ASan campaign; `../../../fuzz/validation.json` records counts and the local LeakSanitizer/ptrace limitation.
- [~] Inspect final-revision hosted CI with default sanitizers.
- [ ] Remaining Track 10 scanners/mutation/adaptive-CI work stays outside this increment.

See `../../../fuzz/README.md` for exact invariants and limits. No other track status
is promoted by this test infrastructure. Revert this focused PR to roll back.
