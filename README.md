# CiteLattice

**Contract-first, Rust-native bibliometrics, scientometrics and research-system mapping.**

CiteLattice is the canonical successor to the `bibx` architectural prototype.
**Status: contract foundation with an initial citation-analysis source increment. Native acceptance of that increment is pending; this is not a validated full scientometrics engine.**
Do not infer method coverage, zero-copy behaviour, Searchright runtime compatibility, or beyond-frontier scientific performance from schemas alone.

## Boundaries

- Searchright owns acquisition, review lifecycle, deduplication and source receipts.
- Sourceright owns reference integrity; CiteWeft owns document extraction.
- CiteLattice owns scientific methods, entity/graph analytics, table/scene/report contracts, and independent comparisons.
- Innovate owns innovation diffusion, competition and substitution models; Voiage owns decision uncertainty and value-of-information models. Interoperate via versioned Arrow/Parquet and explicit scientific metadata; no mandatory or circular source dependencies.

## Standards, inputs and outputs

- Scholarly input: **CSL-JSON** (canonical bibliographic record), versioned `org.scholarly.stream` JSONL envelope for changes, RIS/BibTeX/NBIB/PubMed XML via optional adapters (prefer Searchright interchange).
- Analytical tabular: Apache Arrow IPC / Parquet with explicit schemas, null semantics, units, currencies, DOI/ORCID/ROR identifiers, provenance and content digests. CSV is a labelled lossy/flattened export.
- Graph exchange: GraphML, GEXF and JSON graph snapshots via optional adapters; stable IDs must be mapped to dense graph indexes with epoch-specific dictionary.
- Semantic: JSON-LD, W3C PROV and RO-Crate; Frictionless Data Package/Croissant metadata as optional descriptions, not an alternative to typed Arrow.
- Figures: Vega-Lite JSON for ordinary plots; evidence-linked scientific scenes with deterministic SVG/PNG, optional HTML/WebGPU; image/tile provenance and accessible data tables.
- Publications: Excel via rust_xlsxwriter, HTML, PDF via Typst, and complete RO-Crate results package. Workbook is **not** the canonical large-dataset store.

## Key documents

- [Conductor entry](conductor/index.md) with traceable requirements, workstreams and dependencies.
- [Scientific capability matrix](docs/capabilities.md), [dependency plan](conductor/dependencies.md) and [versioning](docs/versioning.md).
- [Scientific imaging and accessibility](docs/imaging.md).
- [Searchright producer/consumer integration](docs/searchright.md).
- [Innovate/Voiage research protocol](docs/studies/innovation-voi.md).

## Developer status

Core Rust contracts live in `crates/citelattice-core`. Heavy backend dependency probes live in an **excluded** optional workspace `backend-probes`; no untested dependency is forced into the default build. Contract schemas/fixtures are exercised in CI. The `citelattice-analysis` source increment adds h/g/i10/totals, missing-count ranges, reproducible identity keys and bounded independent-request JSONL. See [scope and usage](docs/citation-summary.md). Its Rust build and tests remain unverified in the authoring environment. Searchright event replay, graph analytics, actual figures, workbook/report writers and full feature parity remain pending.

The earlier `bibx` design.2 archive contains a more extensive initial API sketch and coverage inventory. Migration is tracked in Conductor: do not discard useful definitions or claim all files have been imported.

## Verification and research programme

[Track 12](conductor/tracks/12-scientific-evaluation/spec.md) sets out independent
method comparisons, missingness/identity stress tests, incremental/full replay,
evidence-linked imaging and the Innovate/Voiage study. It has an executable plan
and machine-readable task dependencies, without a second issue hierarchy.
The current source is not described as beyond-frontier; each such claim requires
a prespecified, held-out comparative result and scoped independent reproduction.


## Experimental evidence-linked imaging

`citelattice-visualize` (PR pending) builds scoped annual mark-to-source scenes, declarative Vega-Lite, offline SVG, accessible exact integer rows and self-check render receipts. No global citation coverage, independent scientific visualisation validation, or GPU capability is claimed. See `conductor/tracks/07-scientific-imaging/`.
