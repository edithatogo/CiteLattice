# Citation-summary source increment

**State:** Rust source authored, native build/format/lint/test not executed in the
authoring runtime. Python independently validates the synthetic fixtures and JSON
schemas; that is not Rust runtime or external scientific validation.

## Scope

The new `citelattice-analysis` crate adds actual function bodies for h-index,
actual-N-capped g-index, i10, exact totals, missing-count ranges, content-addressed
identities and bounded independent-request NDJSON. It reuses the existing core
`Revision` rather than replacing canonical bibliographic contracts.

CSL-JSON remains canonical bibliographic interchange. This calculation accepts a
**citation-count sidecar** keyed to those publication identities. It does not
invent a CSL field, acquire citations, resolve authors, reconstruct a complete
citation universe, accept Searchright events or run an existing provider.

A complete population [10,8,5,4,3] has h=4, g=5, i10=1 and total=30 under this
profile. The independent fixture calculation supplies those expected values;
CLI output from the new Rust code has not yet been observed.

## Wire contract

`org.citelattice.citation_request` / `1.0.0` requires source ID/version/digest,
population and citation-universe IDs, RFC3339 cutoff, explicit missing-count and
export policies, and uniquely identified observations. Citation counts are
canonical decimal **strings** in [0, 18446744073709551615]; null is unknown and
must be explicit. Whole JSON objects or one compact object per line are shown
under `examples/citation-summary/`.

The library limits requests to 100,000 actual works. The CLI limits each physical
line to 1,048,576 bytes including newline and at most 10,000 requests. A direct
library request can be larger in bytes than the CLI limit, so these are distinct
limits. Numeric totals accumulate in checked u128 and are emitted as strings.
They never pass through IEEE754 JSON-number canonicalisation.

## Missing counts

`reject` refuses unknown counts. `bounds` retains all actual works and calculates
extremal h/g/i10 values, assuming observed counts are exact in the named universe.
A lower-bound computation uses zero for each unknown count; this is not reported
as observed data. An upper construction uses a value above all relevant index
thresholds. Results explicitly say complete, partial or unavailable.

For [100,null,null], h is [1,3], g is [3,3] and i10 is [1,3]. N remains 3; dropping
unknown works would change g's meaning. Empty populations have exact zero values;
nonempty populations with no known counts retain unavailable status and ranges.
Known total is a lower bound under missingness; upper total is null, not a made-up
estimate. These are **identification bounds, not confidence intervals**. They do
not cover missing works, imperfect attribution or underestimated observed counts.

## Versioning, hashes and rendering

The normalisation sorts unchanged IDs; no case folding or silent deduplication.
Domain-separated RFC8785/SHA256 keys distinguish scientific inputs, calculations,
whole requests, results and rendering. The calculation key includes method,
package/build identity and missingness policy. Caller export permission changes
the request/result but not the science; render style changes only the render key.

Trusted CI may set `CITELATTICE_BUILD_REVISION` when building. Without it, the
result explicitly has no build revision. Package version alone is not attestation
of exact executable bytes. Without an exact qualified build revision, a calculation
key is a logical development identity and must not be used as a trusted persistent
cross-build cache key. Result/render hashes still identify their supplied content.
The source digest is supplied by the caller; this
module validates its form but cannot verify external source bytes it does not
read. Unkeyed hashes detect accidental changes, not dishonest recomputation.
`render_key` implements dependency identity, **not a renderer or automatic cache**.

## Permission and data minimisation

Local `analyze` can calculate with export denied. The supplied JSONL and render-key
paths require `export: allowed`. This is a caller policy declaration, not an
independent licence check or an authentication system. A hostile caller can write
its own exporter; future deployment adapters must enforce real authority.

Results omit per-paper observation lists and abstracts; errors omit raw payloads.
IDs still require appropriate handling. No network, model, telemetry, subprocess
provider, workbook or filesystem exporter is enabled by the calculation code.

## Intended native usage (not run in this authoring environment)

```sh
cargo run -p citelattice-analysis --bin citelattice -- citation-summary \
  < examples/citation-summary/complete.request.jsonl > results.jsonl
```

A blank line, malformed request, unknown version, duplicate identity, overflow,
invalid cutoff or denied output is rejected. CRLF and no final newline are
accepted. Output is complete JSONL per accepted request. Failure on a later input
preserves earlier results; I/O failure can leave a partial final line. For atomic
files, use a temporary file and validate before rename. This is not durable
checkpointing or a transaction over the whole input stream.

## Dependency reuse

Serde handles wire parsing, `serde_json_canonicalizer` handles RFC8785, `sha2`
handles hashing, `semver` parses exact revisions, `time` parses RFC3339 and
`thiserror` provides typed safe errors. `proptest` supplies generated invariant
cases. Small domain-specific integer formulas remain in this crate. No Polars,
DataFusion, graph or model engine is pulled into this small first increment.
Versions must be resolved/locked and supply-chain checked in trusted native CI;
no lockfile is fabricated in an offline environment.
