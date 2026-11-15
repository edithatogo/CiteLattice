# E05 independent numerical comparator harness

## Outcome and evidence boundary

The bounded harness is implemented. **Production numerical qualification remains
blocked by E04 and the absence of an admitted upstream source/contract/toolchain
receipt.** No production evaluator, schema, Cargo file, CI workflow or common
Conductor plan is changed by this lane.

At baseline `966ff7d8650568804b90f3a8d3af2dd94516c3b0`, E04 is `planned` and
`verification/native-ci-receipt.json` / `verification/dependency-review.json`
are absent. Earlier successful scoped CI runs do not establish that prerequisite.
The contract hashes below identify an inspected snapshot; they are not an E04
admission or evidence that the Rust implementation produced these numbers.

The independently executed **PyBibX source-method probe** matches h and g on 271
complete synthetic cases: **542 exact comparisons, zero mismatches**. Nine
missing-count cases are retained as unsupported. This runs two unchanged method
ASTs from a pinned public source file. It does not import the installed PyBibX
package, execute its constructor/parser, resolve real authors, or establish
end-to-end package parity. R is unavailable in the authoring environment;
bibliometrix execution is explicitly blocked. Its adapter is authored and
statically reviewed, with no R-native execution claimed.

The 147 catalogue outcomes all retain an explicit state in
[outcome-status.json](../../verification/comparators/outcome-status.json):
146 deferred and one unsupported by the selected comparator surfaces. None is
qualified. This is conventional method verification, with no empirical or
scientific superiority claim.

## Immutable source and contract pins

The [manifest](../../verification/comparators/manifest.json) records original
upstream repositories, exact commits, declared package versions, licences,
source-file SHA-256 values, method names and runtime versions. It pins the
CiteLattice method/request/result contracts, catalogue and reusable oracle bytes.
Changed pinned bytes fail closed. A moving branch name or a matching package
version alone is insufficient.

| Comparator | Source revision | Declared version | Selected surface | Runtime |
| --- | --- | --- | --- | --- |
| [PyBibX](https://github.com/Valdecy/pybibx/tree/c8086085a70a80042822f8886e34e98036d4e206) | `c8086085a70a80042822f8886e34e98036d4e206` | `5.9.5` | `pbx_probe.h_index`, `pbx_probe.g_index` | CPython `3.12.14`; standard library only |
| [bibliometrix](https://github.com/massimoaria/bibliometrix/tree/ea89af04e8568146f1c6c53363d65a65a86d4213) | `ea89af04e8568146f1c6c53363d65a65a86d4213` | `5.5.0.9000` | `Hindex`, `field="source"`, `years=Inf` | Target R `4.5.2`, dplyr `1.1.4`, jsonlite `2.0.0`; unexecuted |

The bibliometrix target names exact direct tools. A full installed R dependency
lock and observed session still require qualification; this file does not claim
one exists. The worker refuses a different direct runtime. Optional Parquet
export uses `pyarrow==21.0.0` and records its format profile separately.

The selected upstream code is not vendored or relicensed. PyBibX's pinned
[LICENSE](https://github.com/Valdecy/pybibx/blob/c8086085a70a80042822f8886e34e98036d4e206/LICENSE)
states GPL version 3 or later. bibliometrix's pinned
[DESCRIPTION](https://github.com/massimoaria/bibliometrix/blob/ea89af04e8568146f1c6c53363d65a65a86d4213/DESCRIPTION)
declares GPL-3. Acquire sources separately from those originals and retain their
licences. The repository contributes only adapters, synthetic fixtures and
observed numerical evidence. The harness never downloads source, installs a
package, accesses a provider, or starts model inference.

## Matched conventions and explicit exclusions

Every case has unique synthetic work IDs, a named synthetic population and
citation universe, cutoff `2026-01-01T00:00:00Z`, whole-publication counting and
an explicit missingness policy. Citation counts already include whatever
self-citations the synthetic fixture declares. No citation graph or external
database completeness is inferred from a count sidecar.

All actual works belong exactly once to one synthetic author (PyBibX) or one
synthetic source (bibliometrix). This is a neutral grouping for the selected
corpus-level h/g/total definitions. It is not a comparison of author matching
against journal matching. The R adapter also checks the returned publication
count and exact work IDs, so filtering/deduplication cannot silently change N.
R's m-index is excluded because it uses the current year; no wall-clock-derived
metric enters the comparison.

| Convention | Harness behavior |
| --- | --- |
| h | Compare exact integers under the pinned definition: maximum k with at least k works having at least k citations. |
| g | Cap the expected result at the number of supplied actual works; never add fictitious zero-citation works or clip a comparator result. For `[100]`, g is 1; for `[100,0,0]`, g is 3. A differing comparator result remains a mismatch. |
| i10 | Independent known-answer coverage; neither selected upstream adapter supplies it. Rows are `unsupported_method`, not fabricated matches. |
| Total | Decimal-string known totals are independently checked. PyBibX's selected h/g surface does not supply total; bibliometrix's `TC` is eligible only inside the exact R domain. |
| Unknown count | Preserve JSON/Parquet null and every actual work. Both external adapters return `unsupported_missing_counts`; do not zero-fill, drop rows, or compare only observed publications. |
| Missingness bounds | Reuse the seven existing bounds fixtures. `[100,null,null]` retains N=3 and g bounds `[3,3]`. The known total is a lower bound; unidentified upper totals remain null. External point comparators are not evidence for those bounds. |
| Large integers | Inputs and outputs are canonical decimal strings. Python integers remain exact. bibliometrix is rejected before execution when any count or the total exceeds `2^53-1`; source values are never rounded to make a comparison pass. |
| Empty population | Exact zero known answers are retained. PyBibX's methods are invoked with an empty work list and one synthetic group. bibliometrix is marked `unsupported_empty_population`, with no invented upstream row. |
| Malformed evidence | Reject duplicate identities/JSON keys, numeric JSON counts, floating/non-finite outputs, unknown protocol versions, wrong source/runtime pins, omitted cases, duplicate results and changed scope/N. |

Expected answers do not enter worker requests. Each worker response binds its
values to the case identity, exact input digest and actual N. The input digest
uses a local sorted ASCII JSON profile containing no floating-point values; it
is explicitly separate from production RFC 8785 identities. External methods
are run in bounded subprocesses. Subprocess isolation is not a general security
sandbox; only reviewed, checksum-matched public source is admitted.

## Fixtures and observed rows

The harness reuses all 260 existing subset-enumeration fixtures and seven
missingness fixtures without editing them. It adds 13 explicitly stated known
answers for empty/zero corpora, ties, actual-N examples, i10 boundaries,
binary64 neighbours, unsafe totals, u64 totals and unknown counts. The tests
independently enumerate subsets, rather than copying the production sorted
prefix algorithm. Fixtures are development and correctness cases, not held-out
empirical data or a claim of independent human replication.

All 280 cases generate four rows per backend, including unsupported and blocked
rows. [results.parquet](../../verification/comparators/results.parquet) has
**2,240 rows**, with integer fields stored as decimal UTF-8 and genuine nulls.
It binds the manifest and fixture-set digests in file metadata and carries
`production_numerical_qualification=false`.

| Observed row status | PyBibX | bibliometrix | Interpretation |
| --- | ---: | ---: | --- |
| `matched` | 542 | 0 | Exact h/g source-method matches only |
| `blocked_runtime` | 0 | 795 | Eligible h/g/total comparisons not run because R is unavailable |
| `unsupported_missing_counts` | 18 | 27 | Nine partial/unavailable cases, retained with their actual N |
| `unsupported_integer_range` | 0 | 12 | Four cases exceed the admitted R integer domain |
| `unsupported_empty_population` | 0 | 6 | Two empty-case instances, no invented bibliometrix output |
| `unsupported_method` | 560 | 280 | Methods outside the chosen upstream surfaces |
| `mismatch` / `error` | 0 | 0 | No observed mismatches or execution errors in this run |

Blocked and unsupported comparisons are not successes. Totals, missingness
bounds, production Rust behavior and whole-package import pipelines remain
outside the executed external numerical evidence.

## Reproduce the bounded checks

From the repository root, the ordinary offline suite is:

```sh
python -B -m unittest discover -s tests -p 'test_method_comparators.py' -v
python -B -m unittest discover -s tests -v
```

The harness itself needs no third-party Python package. Existing repository
schema tests retain their own existing requirements. The Parquet round-trip test
is explicitly skipped when the optional pinned PyArrow runtime is unavailable;
that skip is not a completed round trip. The authoring run executed it using
PyArrow 21.0.0 and passed all 36 tests (21 new E05 tests plus 15 existing tests).
No shared CI installation step is added in this lane.

To run the exact PyBibX source-method probe, use CPython 3.12.14 and a local tree
containing the pinned `pybibx/base/pbx.py`, `setup.py` and `LICENSE` bytes:

```sh
python -B verification/comparators/harness.py \
  --pybibx-source /path/to/pinned/pybibx \
  --json /path/to/new/probe.json
```

Add `--bibliometrix-source /path/to/pinned/bibliometrix` with pinned `R/Hindex.R`
and `DESCRIPTION` bytes. If R is available, the worker checks its declared direct
runtime and invokes the unchanged source function. Use `--rscript` only to
select that local runtime. No R execution is inferred from authoring the script.

With the optional `pyarrow==21.0.0` environment, add
`--parquet /path/to/new/results.parquet`. Output paths must not exist. Counts are
stored as strings even when small, and unavailable values remain null. The
source trees are read-only inputs. No third-party source is copied into the
repository by these commands.

Exit 0 means an independent probe ran without observed mismatch/error. Exit 1
means a discrepancy or worker error. Exit 2 means invalid configuration, pins or
output. Exit 3 means no external execution or required qualification is blocked.
`--require-qualified` cannot succeed in this lane: an executed pilot never
supplies E04 admission or a production result.

## Review and coordinator handoff

[CLAIM.md](../../verification/comparators/CLAIM.md) records the inspected ownership
boundary. [PR #22](https://github.com/edithatogo/CiteLattice/pull/22) records the
exact published heads and the coordinator handoff. Execution evidence includes
the original expected RED import failure, the actual test log, source/runtime
pins, raw PyBibX method observations, file digests and retained blocked results.

Review fixed two concrete issues: the R adapter now uses `source()` for its
text connection, and the parent validates the worker's exact reported runtime
in addition to source, protocol, identities and counts. The runtime guard has
negative tests. No production numerical changes were made or requested to make
these fixtures pass.

The active coordinator must supply the accepted E04 source/contract/toolchain
receipt, own any shared manifest/CI/registry updates, and admit a separate pinned
production execution surface before numerical qualification. R-native execution
and its complete environment lock remain separate missing evidence. A later
full-package comparison must explicitly include acquisition/parsing, identities,
cutoffs and missingness; source-method probes cannot be relabelled as that work.
Refresh the relevant pins and rerun the affected comparisons when contracts,
upstream sources, fixtures or runtimes change. No merge is authorised here.
