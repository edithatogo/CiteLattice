# Searchright / CiteLattice integration: current boundary

The mirrored producer proposal is `org.scholarly.stream` / `1.0.0-design.2`.
Searchright PR #812 remains a proposal until admitted and observed at exact
producer/consumer revisions. This continuation does not mutate Searchright or
claim that its CLI produces the new citation analysis requests.

The new analysis crate accepts an independent `org.citelattice.citation_request`
sidecar. A future leaf adapter must select a publication population from preserved
CSL, bind its source receipts and identity decisions, and provide explicit
citation observations from a declared universe/cutoff. Missing references or
counts stay unavailable. A search-result set is not automatically a citation
universe. The adapter must not replace canonical CSL or Searchright review state.

Track 12 task E06 owns the consumer test: actual producer bytes, exact source and
schema identities, permission propagation, no lost fields, duplicate/conflicting
replay, corrections, gaps and spooled restart. The independent-request JSONL runner has no event cursor or persistent state.
The new `citelattice_ingest::events` module **does** implement a bounded, single-epoch semantic consumer of the mirrored proposed Searchright stream. It retains only source/key digests, statuses, rights classifications and event fingerprints; it is not a durable checkpoint or connected real producer. Both boundaries must stay distinct.

The current source hash and schema-version syntax checks are not provider
verification. Sourceright retains reference integrity; CiteWeft retains extraction;
Searchright retains acquisition/review decisions; CiteLattice owns this scientific
analysis. Optional Arrow/Parquet output follows the same scientific values and
requires separate transport/round-trip evidence before being advertised.

## Proposed event-stream consumer — implementation slice

The consumer tests use the exact mirrored Searchright proposal fixture at `contracts/interop/examples/scholarly-stream-upsert.json`. Runtime validation covers RFC8785 canonical SHA-256 payload digest, schema identity, source-rights and prior-revision integrity, exact per-stream epoch sequence, duplicate/conflicting replay and correction/retraction/deletion semantics. Unknown/partial CSL coverage and source-authority rights are not inferred. The snapshot carries `org.citelattice.scholarly-event-snapshot` / `0.1.0` and is deliberately not a source-text archive.

**Next required producer work:** Searchright must actually emit bounded event envelopes; independently invoke the producer against a rights-clear source corpus, capture exact bytes, verify both consumers' schemas and semantic behaviour at pinned commits, exercise crash/spool/restart and rights revocations, then promote the prepared passport. Until that point the connection is a proposal with executable consumer code, not end-to-end interoperability.
