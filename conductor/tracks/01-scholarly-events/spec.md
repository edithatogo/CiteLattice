# Track 01: proposed Searchright scholarly event consumer

**Primary owner:** ingestion and scientific source identity. **Status:** source implementation under CI; producer compatibility and durability pending.

## Intent and boundaries

Implement the actual `org.scholarly.stream` / `1.0.0-design.2` consumer, preserving separate canonical CSL records, typed research-object identifiers, content digest/rights, and exact source change lineage. A Searchright transport contract is not evidence that Searchright's CLI produces valid envelopes.

## MoSCoW

| ID | Priority | Acceptance |
| --- | --- | --- |
| CL-EV-01 | Must | Parse bounded JSONL, reject unknown fields, unsupported versions and oversized lines before unbounded memory use |
| CL-EV-02 | Must | RFC8785 digest exact match, decimal-u64 source counters, valid date, rights and artifact hashes |
| CL-EV-03 | Must | Per-stream epoch ordering, prior source revision and idempotent replay, fail closed on event ID collision |
| CL-EV-04 | Must | Typed publication / nonpublication objects; correction pointers, retractions and deletion tombstones |
| CL-EV-05 | Must | Privacy-minimised snapshot; do not retain raw CSL titles/abstracts or expose restricted keys |
| CL-EV-06 | Must | Real Searchright producer bytes tested at exact commits (not currently demonstrated) |
| CL-EV-07 | Must | Durable spool, restart and sink/checkpoint atomicity (not currently implemented) |
| CL-EV-08 | Should | Versioned multi-epoch migrations and Arrow IPC/Parquet adapter |
| CL-EV-09 | Won't | Duplicate upstream provider execution or claim globally complete citation coverage |

## Evidence ceiling

Code and source-fixture acceptance are distinct from compiler, hosted CI, live producer, crash durability, independent scientific validation and public release. Only promote actual observed results. Sample fixture fields are a transport minimum; full official CSL schema validation remains future work.
