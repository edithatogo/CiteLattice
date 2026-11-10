# CiteLattice

**Contract-first, Rust-native bibliometrics, scientometrics and research-system mapping.**

CiteLattice is the canonical successor to the `bibx` architectural prototype.
**Status: design and API scaffold; not a working or validated bibliometric engine.**
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
- [Scientific capability matrix](docs/capabilities.md), [dependency plan](docs/dependencies.md) and [versioning](docs/versioning.md).
- [Scientific imaging and accessibility](docs/imaging.md).
- [Searchright producer/consumer integration](docs/searchright.md).
- [Innovate/Voiage research protocol](docs/studies/innovation-voi.md).

## Developer status

Core Rust contracts live in `crates/citelattice-core`. Heavy backend dependency probes live in an **excluded** optional workspace `backend-probes`; no untested dependency is forced into the default build. Contract schemas/fixtures are exercised in CI. Runtime streaming, mathematical algorithms, actual figures, notebook/workbook/report writers and complete feature parity are **not yet implemented**.

The earlier `bibx` design.2 archive contains a more extensive initial API sketch and coverage inventory. Migration is tracked in Conductor: do not discard useful definitions or claim all files have been imported.
