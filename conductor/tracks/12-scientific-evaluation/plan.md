# Track 12 implementation and evaluation plan

The user authorised continuation. No new approval loops are needed for ordinary
implementation. Tasks are sequenced by scientific and interface dependencies,
not estimates of calendar duration. Source baseline: `5ec968d181b89237d3e7b1f477671627d3248986`.

## Current scoped change: E01–E03

Consumes: explicit `CitationRequest`, canonical CSL-linked publication IDs and
caller-declared source/scope/rights. Produces: `AnalysisResult`, independent
calculation/result/render fingerprints, and a bounded NDJSON CLI.

- [x] Inspect current main, open work and the earlier design.
- [x] Write independent subset-enumeration and schema tests before fixtures.
- [x] Observe Python RED (missing fixtures/schema/programme).
- [x] Author actual Rust contracts, validation, h/g/i10/total kernels, identities,
      bounded I/O and CLI, with tests for edge cases and failures.
- [x] Specify request/result schemas, precise method conventions and examples.
- [ ] Observe Rust RED/GREEN, rustfmt, Clippy, tests and doctests.
- [ ] Resolve and commit a trusted Cargo.lock and qualify dependencies.
- [x] Prior citation analysis/ingest/export source is now present on main.
- [ ] Verify the complete current native CI and match any compiler/test evidence
      to the exact main commit. A committed source path alone is not qualification.

## Execution commands

Run after applying to a complete CiteLattice checkout:

```sh
python -m pip install -r requirements/citation-evaluation.txt
python -m unittest discover -s tests -v
cargo fmt --all
cargo check --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo run -p citelattice-analysis --bin citelattice -- citation-summary \
  < examples/citation-summary/complete.request.jsonl > /tmp/citelattice-results.jsonl
```

Native tests in `crates/citelattice-analysis/tests/` cover 260 independent exact
fixtures, missing-count ranges, maximum integer totals, duplicate IDs, dates,
permutation/monotonicity properties, tamper detection, render identity, framing,
CRLF, denied output, partial-prefix errors and a real binary smoke test. Claims
remain pending until these commands actually run on the source revision.

## Remaining executable units

1. **E04:** run native and supply-chain admission. Pin accepted versions, preserve
   platform logs and dependency features; fix rather than exempt failing gates.
2. **E05:** create pinned R/Python comparator workers in isolated environments;
   emit the same comparison schema and document convention differences.
3. **E06:** implement actual Searchright producer-to-consumer counts sidecar;
   do not label this independent-request JSONL runner an event replay engine.
4. **E07/E08:** add independent identity/graph oracles and source coverage tests.
5. **E09:** one Arrow/Parquet table → evidence scene → SVG/workbook/report slice.
   Use existing parsers/renderers and verify numerical/rights conservation.
6. **R01–R04:** pilot, fix the candidate, freeze protocol/splits/thresholds, run
   confirmation, ablate components, record failures and independently rerun.
7. **E10–E12:** matched resource benchmarks, reproducible bundles and per-capability
   release claims. Do not block a useful local release on every research track.

Detailed artifacts, task dependencies and observable acceptance criteria are in
`conductor/evaluation-programme.json`; that registry, not a second issue tree,
controls continuation. Planned filenames are future deliverables, not claimed
present implementations.

## Review focus

Large integers must never pass through binary64 canonicalisation as numbers.
Missing citations must not erase unknown works from N. Source fingerprints are
caller declarations, not remotely verified bytes. Public unkeyed hashes are not
signatures. Permission flags are not independent entitlement verification.
I/O failure can leave an incomplete last output line; callers requiring atomic
files must use a temporary file plus verified rename. No full-stream transaction
or durable checkpoint is claimed.

## Current E09 risk remediation (PR #10, provisional pending CI)

A scoped output correctness and computational safety fix adds red-first Rust
regression cases: annual SVG must not silently truncate after 16 periods;
u64::MAX publication counts must not overflow chart arithmetic; >256 author
strings in a bibliographic record must be rejected before pair expansion.
The fix renders all bars through a declared 512-bin display budget,
uses u128 intermediate scaling, guards a million distinct coauthor edges
and rejects excessive author counts. A very large temporal plot must use a
tabular/summary view until an LOD chart adapter exists.

Acceptance: exact-head `cargo fmt --check`, Clippy -D warnings, all native
workspace tests, and output checks. Do not promote beyond-frontier evidence from
these regressions; they prevent misleading graphics and input exhaustion.
Validate publication-year and count agreement across CSV, SVG, HTML, Parquet
and workbook as part of later E09/E10. Use independent known-answer tables.

Next E09 tasks: transactional staging/commit of all output assets, integrity
verification before publication, explicit missing/withheld mark provenance,
reproducible geometry fixtures and accessibility review. Prior Conductor states
are historical snapshots rather than new automatic completion claims.

## Reconciled current status (2026-11-12)

Scoped native compilation, formatting, Clippy and workspace tests passed in PRs #10–#13; these facts are recorded with exact heads and merged commits. Original RED/GREEN per-method observations and full independent scientific validation are **not** inferred from a passing workspace suite. E06's in-memory event consumer is merged but not a durable producer/consumer transport; E09's transactional and imaging slices are merged but do not establish PDF output, semantic cross-renderer equivalence or frontier superiority.
