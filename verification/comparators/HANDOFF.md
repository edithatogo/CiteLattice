# E05 exact-source handoff to the active coordinator

Recipient: **CiteLattice — Integration and event contracts**, chat
`6af2d103-38e4-8324-9afa-5ec1d36012f2`. Acknowledgement has not been received.

PR: <https://github.com/edithatogo/CiteLattice/pull/22> (draft; no merge authorised).
Branch: `verify/e05-method-comparators-20261115`.

## Immutable implementation and evidence

- Inspected main: `966ff7d8650568804b90f3a8d3af2dd94516c3b0`.
- Published scoped claim: `2c9bf895d80224e5b9b8c370e724cd91d145c54d`.
- Reviewed implementation/evidence commit:
  [`b06294fc6c891af7245976fbd0ab2c2fd137ec4e`](https://github.com/edithatogo/CiteLattice/commit/b06294fc6c891af7245976fbd0ab2c2fd137ec4e).
- Its complete Git tree: `4bb33304305f2c9924fca2b8a4bddc1fb660e2c5`.
  The remotely created tree exactly matched the locally staged, tested tree.
- This handoff is the only subsequent file addition. The PR description records
  the final head and its hosted CI separately, without claiming that local
  source-method results constitute hosted or production verification.
- [run.json](evidence/run.json) binds code, tests, contracts, fixtures, catalogue,
  raw observations and Parquet bytes with SHA-256. The results artifact SHA-256
  is `6908e22eba89de82ee774ac8c7404cdd56858e9260cc50a98cfd6059fccc6e76`.

Only `verification/comparators/**`, `docs/evaluation/method-parity.md` and
`tests/test_method_comparators.py` are changed. Live main and the open PR/branch
inventory were checked again before publication; no published overlapping claim
was found. No root manifest/lock/CI, schema, production crate, registry or common
plan was edited. No other worker/chat was started and no other work was removed.

## Executed proof

1. Expected RED: the newly authored test module failed to import the absent
   harness; the original test-file digest and actual output are retained.
2. GREEN: all 36 Python tests passed locally, including 21 new E05 tests and the
   optional PyArrow 21.0.0 round trip; zero local skips. Existing schema tests
   used jsonschema 4.26.0, rfc3339-validator 0.1.4 and six 1.17.0.
3. PyBibX 5.9.5 source commit `c8086085a70a80042822f8886e34e98036d4e206`:
   unchanged `pbx_probe.h_index` and `pbx_probe.g_index` AST nodes ran in a
   separate CPython 3.12.14 process on 271 complete cases. All 542 comparisons
   matched exact independent known answers. Expected answers were not passed to
   the worker. No installed-package/parser/author-resolution parity is claimed.
4. All 280 synthetic cases are retained, including nine missing-count cases;
   2,240 Parquet rows preserve exact decimal strings, genuine nulls and every
   unsupported/blocked result. The final rerun produced identical Parquet bytes.
5. Reviewed source, protocol, runtime, actual-N and input-digest checks;
   negative tests reject altered evidence, ambiguous numbers and omitted cases.
   Disagreements remain exact mismatches rather than clipped/averaged values.

## Blocks that remain

- E04 is `planned` at the inspected main. Both required native CI and dependency
  review receipts are absent. No accepted production source/contract/toolchain
  admission has been supplied. `--require-qualified` exits 3 and no outcome is
  promoted by a passing source-method pilot.
- bibliometrix source commit `ea89af04e8568146f1c6c53363d65a65a86d4213`
  (DESCRIPTION version 5.5.0.9000) and its full Hindex function are pinned.
  Rscript is unavailable: **zero bibliometrix numerical results were executed**.
  The R adapter is authored/static-reviewed only. Its direct target is R 4.5.2,
  dplyr 1.1.4 and jsonlite 2.0.0; a full installed R dependency/session lock is
  not admitted. Its 795 eligible metric rows are `blocked_runtime`.
- Missing counts are not supplied to either external surface. R empty inputs
  and counts/totals outside `2^53-1` remain unsupported. i10 is not supplied by
  either selected surface, and PyBibX total is not implemented by this adapter.
- All 147 inventory rows have explicit unqualified states: 146 deferred, one
  unsupported in these selected surfaces. Full-package parity, production Rust
  parity, empirical replication and scientific superiority are not established.

## Shared requests for the coordinator

1. Preserve this exclusive path ownership while reconciling the common plan.
   Record that the independent E05 harness and evidence are available, while
   dependent numerical qualification remains blocked. Link this PR and the
   method-parity document from common tracking only in the coordinator's lane.
2. Supply the exact accepted E04 source SHA, method/request/result contract hashes,
   feature/toolchain/platform/dependency receipts and an admitted production
   execution surface. The current contract snapshot is explicitly not admission.
3. Coordinate any future shared CI or environment changes. The existing schema
   job discovers the new offline tests; it does not install R/PyBibX/PyArrow.
   Without optional PyArrow, its round-trip test is visibly skipped. Do not
   reinterpret that skip as execution or weaken a gate to make it pass.
4. Qualify and execute the pinned R environment, then retain its full session,
   source provenance and raw results. A different upstream or runtime requires
   new pins and affected reruns, not a silent substitution.
5. Admit production comparison only after E04 and matched identity, corpus,
   citation-universe, cutoff, actual-N and missingness contracts are settled.
   Re-pin deliberately if shared contracts change. Any production numerical
   finding belongs to the coordinator; no numerical fix is included in this lane.

The source tree is reversible by reverting the scoped PR; there is no runtime
or infrastructure migration. Preserve the evidence and provenance when updating
pins. No merge or automatic merge setting is requested.
