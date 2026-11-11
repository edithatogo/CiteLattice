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
replay, corrections, gaps and spooled restart. The current bounded JSONL runner
has no event cursor or persistent state and must not be marketed as that adapter.

The current source hash and schema-version syntax checks are not provider
verification. Sourceright retains reference integrity; CiteWeft retains extraction;
Searchright retains acquisition/review decisions; CiteLattice owns this scientific
analysis. Optional Arrow/Parquet output follows the same scientific values and
requires separate transport/round-trip evidence before being advertised.
