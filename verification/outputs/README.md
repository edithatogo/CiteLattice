# E09 independent conservation fixture harness

This is an executable, read-only audit of a **synthetic fixture profile**. It
compares separately supplied source tables with decoded artifacts, checks every
declared asset, and rejects semantic changes even when a candidate's checksums
have been recomputed. Passing it qualifies the fixture auditor only. It does not
qualify CiteLattice production exports, an actual Searchright producer, durable
replay, or a release.

The scoped ownership claim is [issue #21](https://github.com/edithatogo/CiteLattice/issues/21).
The coordinating requirements remain in [E09](../../conductor/evaluation-programme.json)
and [Track 12](../../conductor/tracks/12-scientific-evaluation/plan.md).
No shared plan, registry, production crate, root manifest, lockfile or CI file is
changed here. See the [integrator handoff](HANDOFF.md) for the remaining work.

## Run the complete audit

Run from the repository root in an isolated environment. Installation is an
explicit setup step; neither the auditor nor the tests download tools or data.

```sh
python -m venv .venv-e09
.venv-e09/bin/python -m pip install -r requirements/citation-evaluation.txt \
  -r verification/outputs/requirements.txt
.venv-e09/bin/python -m unittest discover -s tests -v
.venv-e09/bin/python -m verification.outputs.audit \
  verification/outputs/fixtures/source-mixed.json \
  verification/outputs/fixtures/mixed
.venv-e09/bin/python -m verification.outputs.audit \
  verification/outputs/fixtures/source-integers.json \
  verification/outputs/fixtures/integers
```

The CLI exits `0` only after every required artifact passes. Missing, mismatched
or unpinned readers cause a failure; there is no partial-pass mode. It emits
fixed, redacted error codes on failure and never evaluates source expressions,
workbook formulas, Typst code or browser code. Successful receipts always say
`claim: synthetic-fixture-auditor-only` and `release_qualified: false`.

The existing lightweight Python CI environment does not install E09's optional
readers. In that environment the full-reader test class explicitly skips, while
the standard-library authority, text, imaging and pin tests execute. **A green
existing CI job is not full E09 execution.** The integrator must explicitly admit
the pinned full-reader commands before using them as an additional gate; this
lane does not change CI or weaken any existing gate.

## Independent authorities and expected results

`source-mixed.json` is a repository-authored table of 24 synthetic rows. Twenty-two
rows may be exported; two whole rows must be withheld. The public rows include a
real zero, one missing count, one withheld count, one undated row and a literal
`=1+1` label. Their independently specified known total is **180 works**. All 22
public rows have scene membership; the 20 observed counts have bars. A missing
or withheld count has a labelled state and no bar, rather than a fabricated
zero. The population is deliberately larger than the earlier 16-period crop.

`source-integers.json` contains `0`, `2^32−1`, `2^32`, `2^53−1`, `2^53`,
`2^53+1`, `u64::MAX`, and a null. Its exact known total is
**18,473,765,680,063,709,182**. All tabular formats retain these integers. The
imaging auditor refuses the unsafe browser values; it does not round them or
advertise a large-integer Vega/SVG result. Empty and all-null populations are
separately tested at the authority layer.

Whole-row rights (`public` / `withhold`) and count availability (`observed` /
`missing` / `withheld`) are separate. An excluded-row count is published only
when the synthetic policy permits it. Otherwise both `withheld_rows` and
`source_rows` remain null, because publishing the latter would disclose the
former by subtraction. Publicly visible withheld cells remain distinguishable
from missing cells. Unknown rights, inconsistent null states, duplicate row
identities, Boolean/floating/string count substitutes and unsigned overflow are
rejected. These synthetic policies do not establish real-world entitlements.

The source tables are not derived from a production writer, another candidate
format, or the auditor. Hand-specified counts and [geometry anchors](../imaging/geometry-oracles.json)
are checked independently. `build_fixtures.py` encodes those source tables using
separate fixture writers and never imports the auditor or production code.
PyArrow is used for both synthetic Arrow/Parquet encoding and independent
reading; that round trip tests the harness, **not independent Rust-writer parity**.
XLSX encoding uses XlsxWriter, while reading uses openpyxl and ZIP/XML inspection.

## What each reader checks

| Artifact | Independent reader and checks |
| --- | --- |
| JSON | Strict standard-library JSON, duplicate-key rejection, exact scalar types, rows, rights, null states, metadata and source/projection fingerprints |
| CSV | Standard-library CSV, all cells and row identities, explicit `NULL` representation, reversible formula-prefix convention; logical types/units are declared in the required disclosure sidecar |
| Arrow IPC | PyArrow 19.0.1, exact Int32/UInt64/UTF-8 fields, nullability, field units, schema metadata, all rows and absence of custom batch metadata |
| Parquet | PyArrow 19.0.1, physical/logical schema, all row groups, metadata, exact integers and nulls; no conversion through pandas or binary64 |
| XLSX | openpyxl 3.1.5, real cell types/values, explicit large-integer text, two visible sheets and disclosure metadata, plus complete supported package-part inspection |
| HTML | Standard-library HTMLParser, strict offline table grammar, accessible table values and metadata, rejected scripts, hidden containers, comments and unknown attributes |
| Typst source | Closed literal `#text` table grammar and metadata, exact values, rejected extra expressions; no Typst execution or PDF claim |
| Scene / Vega-Lite | Strict JSON, exact mark/value/membership/rights lineage, no extra hover/layer/transform/URL payload; no Vega rendering claim |
| SVG | XML parser, exact row membership and labels, rational geometry inequalities, bar/null distinction, complete viewBox, no script/event/hidden/foreign/unknown content |

The workbook profile intentionally fixes the static package parts and worksheet
shells of the pinned XlsxWriter fixture encoding. It also enumerates every cell
and shared string, so extra unreferenced strings, ignored XML and document
properties cannot pass simply because visible values match. It rejects unknown
parts, formulas even with correct cached values, hidden sheets/rows, comments,
external links, macros, ZIP comments/extra fields and appended data. General XLSX
compatibility, alternative encoders and arbitrary workbook styling require a
separately reviewed profile; a matching ZIP signature is never sufficient.

Every bundle must contain exactly the profile's required files. Unknown files,
duplicate/omitted manifest entries, symlinks, path traversal, absolute paths,
wrong types and wrong hashes fail. Independent semantic checks still run after
integrity checks. Serialized bytes, rows and expanded XLSX contents have small
fixture budgets; these limits are not a proof against every malicious native
decoder allocation or covert channel. Use only public/synthetic inputs here.

## Pins, regeneration and evidence

[roundtrip-manifest.json](roundtrip-manifest.json) pins source tables, fixture
assets, reader/test source, the workbook encoding profile and the observed
production/contract baseline. The latter is an inspection pin, **not integrator
admission of those contracts**. Tool versions and declared upstream licences
are recorded there; E04 supply-chain qualification remains outstanding.

To reproduce an encoding, install `requirements-fixtures.txt` and write to a
new destination (the generator refuses an existing directory):

```sh
.venv-e09/bin/python -m pip install -r verification/outputs/requirements-fixtures.txt
.venv-e09/bin/python -m verification.outputs.build_fixtures \
  verification/outputs/fixtures/source-mixed.json /tmp/e09-reencoded-mixed
```

The generator uses a fixed workbook creation timestamp for reproducibility, not
as an execution timestamp. Golden fixtures are never regenerated automatically
by tests. Changes to authorities, profiles or tools require an explicit review
and a new pin manifest. The local JSON digest convention is documented in
`audit.canonical`; it is not the production RFC 8785 identity algorithm.

All fixture data and geometry anchors are newly authored synthetic examples,
dedicated under [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/).
No provider dataset, restricted record, font, model or third-party source code
is redistributed. Harness source follows the workspace's `MIT OR Apache-2.0`
licence declaration. Execution results are in [results](results); their exact
implementation SHA and final PR head are distinguished in the handoff.
