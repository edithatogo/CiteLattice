# Standard formats and contract boundaries

See machine-readable [format registry](../contracts/formats.json).

**CSL-JSON** is the preserved bibliographic source-of-truth, not a substitute for a full bibliographic evidence graph or complete references. The Searchright proposed envelope in [contract](../contracts/interop/scholarly-stream.v1.schema.json) carries changes and rights. Do not conflate a CSL-JSON array with JSONL or a custom event envelope.

For high-volume execution prefer Arrow IPC streams and Parquet; keep null types, timezone, publication/event dates, decimal quantities, source vocabulary and logical type metadata. CSV must specify loss of nesting, zero-vs-null, escaped spreadsheet formulas and conversion receipt. Decode into owned buffers before async queues; do not claim all formats are zero-copy.

Use existing import/export and rendering libraries rather than writing new XML, RIS, BibTeX, workbook or SVG parsers. Searchright remains the owner of publication-source interchange; the CiteLattice leaf adapter should never duplicate provider retrieval/authentication.

GraphML/GEXF provide graph exchange, not stable dense in-memory IDs. Vega-Lite covers ordinary statistical graphics, while EvidenceScene carries scientific mark-to-row evidence, uncertainty, temporal alignment and privacy controls. RO-Crate 1.3/PROV cover provenance, not authorisation or scientific accuracy.

Every adapter declares exact source and target contract IDs, schema revisions, capability, loss report, input/output digests, rights and quarantine counts. Independently validate exported artifacts; test both source roundtrip and converted output semantic equivalence.
