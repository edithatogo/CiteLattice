# Track 09: Polars annual aggregation receiving qualification

**Decision: DEFER (no backend admitted).** This is a reproducible, synthetic parity/benchmark **preparation**, not a claimed native Polars comparison. Work is limited to this directory and a new Python unit test. No dependency upgrades, shared interfaces, root lockfile, CI, Conductor registry, production code, live sources, rights-bearing data, branch pruning or merges.

## Source pin and ownership

- Inspected current main: cfd72e73872b33ceddfc923381c51278f94ae428 (2026-11-19).
- Registry: [Track 09](../../../conductor/tracks.md) is **scaffolded**, with isolated compile, security, benchmark and parity as acceptance gates. [Dependency decisions](../../../conductor/dependencies.md) prefer measuring Polars before adoption. [Dependency rationalisation](../../../conductor/dependency-rationalisation-20261113.md) calls Polars an evaluation candidate.
- Existing implementation: crates/citelattice-ingest/src/lib.rs, summarize_reader. It validates native Searchright bibliographic-record JSONL, deduplicates record identities, treats publication_year as Option<i32>, accumulates annual counts in a BTreeMap<i32,u64>, keeps undated counts separate and returns sorted year rows. Native-source, identity, graph, export and rights semantics must remain unchanged.
- Candidate: Polars 0.55.2, optional, default features disabled, with lazy and parquet features already declared in excluded backend-probes/Cargo.toml. Isolate one group-by of validated publication years only. No production crate imports or shared-source normalization changes.
- CI: the main commit's rust-core, schemas and privacy-and-secrets checks succeeded. Root Cargo.lock is absent in the inspected tree. The standard workflow does not compile the excluded backend-probes manifest. No candidate lock, isolated compilation or native parity result exists.
- No overlap with E05 draft PR #22 (bibliometric comparator tests), E09 draft PR #24 (cross-format conservation), or the existing shared-core integrator. Shared schema, CI, track registry and admission remain integrator-owned.

## One bounded candidate: static baseline-versus-Polars comparison

| Criterion | Existing BTreeMap path | Optional Polars path |
| --- | --- | --- |
| Scientific function | Annual frequency by source publication year | The same single group-by, not a new method |
| Missingness | None/null stays undated | Must explicitly exclude null from year groups and preserve undated |
| Precision | Exact integer year/count and sorted rows | Exact i32/u64, no float or silently zero-filled null |
| Package surface | Standard-library reducer (no added aggregation crate) | Polars 0.55.2 plus unresolved optional/transitive feature graph |
| Feature requirement | Existing ingest crate | Existing excluded polars feature (lazy + parquet) |
| Licence | Existing baseline | Polars 0.55.2 package advertises MIT; transitive licences NOT reviewed (https://docs.rs/crate/polars/0.55.2/source/Cargo.toml) |
| Build cost/performance | Existing main CI only; no matched benchmark | Unmeasured; no package delta, cold/warm build, RSS or latency receipts |
| Advisories | Track 09 not independently audited | Track 09 not independently audited |
| Result | Retain | Defer |

A published Polars package source size or docs.rs build time is **not** an apples-to-apples CiteLattice package/build cost. Neither static source inspection nor a successful empty-probe feature check demonstrates numerical parity.

## Reproducible synthetic fixture and gate

Run with Python 3.10+ (standard library only) in a full checkout:

    python verification/dependencies/track09-polars-annual/synthetic.py --out /tmp/citelattice-track09-annual
    python verification/dependencies/track09-polars-annual/synthetic.py --out /tmp/citelattice-track09-annual --verify
    python -m unittest discover -s tests -p 'test_track09_polars_annual.py' -v

Eight synthetic native JSONL cases: empty; mixed years including -1, 0, 1999, 2024 and None; exact record permutation; entirely undated; 8192 densely distributed records; 512 distinct years; duplicate record identity; invalid native schema. Exact bytes and SHA-256 are generated deterministically, with a separate Counter oracle and literal mixed-case known answers. Never use licensed, live or identifiable data.

For a future executed native baseline and candidate adapter, emit one JSON object per case and engine, containing only case_id, input_sha256, status and either exact record_count/undated/sorted annual [{year,count}] or a redacted Duplicate/InvalidContract error category. Never leak source record text, stack traces or hidden information. The gate verifies both engines **independently against the same oracle and against one another**.

    python verification/dependencies/track09-polars-annual/compare.py \
      --fixtures /tmp/citelattice-track09-annual \
      --baseline /tmp/track09-baseline-results.jsonl \
      --candidate /tmp/track09-polars-results.jsonl

The two result files must come from two separately executed native adapters at exact pinned revisions; **they do not exist yet**. The Python self-tests use explicitly invented receipts to test the gate itself. Nine locally executed tests passed, including initially red permutation/oracle/path-traversal regressions. This is not a claim of Rust, Polars, or end-to-end parity.

Current summarize_reader parses and validates native JSONL before the BTreeMap aggregation. To compare only the group-by fairly, both kernels must receive exactly the same prevalidated Option<i32> vector. Do not duplicate parsing and claim matched work. A new exposed validated-year production API would require the existing core owner's handoff; the permitted probe must not introduce it.

## Deferred native, package/build, safety and performance qualification

1. Pin an exact clean trusted checkout and one stable target/toolchain. Record git head, toolchain and cargo versions, target triple, CPU/RAM/OS, thread count, feature list, cache state and environment. Repeat the original baseline tests at the exact revision.
2. Resolve a lock **only in a temporary copy** of excluded backend-probes, retaining its SHA-256, the package checksums, advisory database versions and all command outputs. Do not change root Cargo.lock or upgrade requirements. Run isolated baseline and Polars dependency closures:

       cargo generate-lockfile --manifest-path backend-probes/Cargo.toml
       cargo tree --manifest-path backend-probes/Cargo.toml --locked --no-default-features -e normal,build
       cargo tree --manifest-path backend-probes/Cargo.toml --locked --no-default-features --features polars -e normal,build
       cargo tree --manifest-path backend-probes/Cargo.toml --locked --no-default-features --features polars -d
       cargo check --manifest-path backend-probes/Cargo.toml --locked --no-default-features --features polars

   The final check is **feature-closure compilation only**, since the current probe lib.rs has no Polars code. Report exact direct/transitive package deltas, duplicate versions, build errors and checksum/feature evidence.
3. Within this excluded probe only, implement an unowned baseline BTreeMap kernel and a Polars LazyFrame group-by with identical normalized inputs, output contract and checked conversions. Run the eight-case gate (including source-contract negative cases handled by an unchanged common preflight), compare exact integers and sorted rows. Do not attribute oracle equality to unexecuted production ingest parity.
4. In the **same controlled runner**, measure five independent cold clean release builds and ten warm builds for both feature profiles. Capture /usr/bin/time -v wall/CPU/peak RSS, CARGO_TARGET_DIR bytes and binary sizes. For each 8192-record and 512-year fixture, perform warm-ups and at least 30 separate timed runs. Preserve samples and median/p95, throughput, memory, failures and digest outputs; distinguish normalization, parsing, allocation and group-by costs. No cherry-picked speedups or cross-machine comparison.
5. Execute supply-chain review against the **resolved feature closure**: cargo-audit/cargo-deny/licences, MSRV, transitive checks, and SBOM if tooling is available. Record exact tools, advisory snapshots and exit codes. Missing tools/network mean **not checked**; no waivers or silent exclusions.
6. Decide ADOPT, RETAIN, REJECT or DEFER with parity, resource and build-package cost, complexity, threats and rollback. For now, **RETAIN the BTreeMap reducer; DEFER Polars promotion**. Integrator admits any future shared-interface work; no merge is requested from this lane.

## Actual local receipt (2026-11-19)

- Inspected main: cfd72e73872b33ceddfc923381c51278f94ae428.
- Python 3.13.5: 9 tests passed, 0 skipped, using synthetic fixtures/gate only.
- Rust/cargo: not installed in the local runtime. External package network unavailable. Native candidate executions: 0; isolated Cargo.lock: absent; package/build cost: **not measured**.
- Main hosted CI at inspected SHA: rust-core, schemas and privacy-and-secrets success; these do not test optional backends.
- Substitution admission, performance/scientific/security qualification: **false**.

This receiving evidence package deliberately avoids weakening an existing gate or claiming external provider, licensed dataset, production method, or native backend verification.
