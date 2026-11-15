# E09 scoped integrator handoff

## Ownership and source boundary

Authorised lane: **E09 — independent cross-format conservation**. Durable claim:
[issue #21](https://github.com/edithatogo/CiteLattice/issues/21).

Only `verification/outputs/**`, `verification/imaging/**` and the new
`tests/test_output_conservation.py` are changed. The **Integration and event
contracts** coordinator remains the owner of all production crates, producer
protocol/schema, durable spool/recovery, root Cargo/lock/CI, evaluation registry
and common plans. No new handoff acknowledgement is assumed.

The branch starts from main `966ff7d8650568804b90f3a8d3af2dd94516c3b0`.
Pre-edit inspection covered all 24 advertised remote refs (including HEAD),
open PR #9 (`84227bcc0137b6c05fc1ad4f35f65f1135bf4e6f`), open PR #19
(`73bb6950e1cce3becc8a03709e9674590307ea5f`), their changed paths and comments,
issues, relevant merged output/imaging discussions and Conductor. No target
paths or published overlapping claim were found. A subsequent check found E05
draft PR #22 confined to its separate comparator namespace. No coordinator
acknowledgement was present in the E09 claim discussion at that check.

## Delivered scope

The bounded fixture harness is implemented: separate known-answer authorities,
exact source/contract/tool/asset pins, independent format readers, a fail-closed
CLI, count/type/null/rights/withheld-count checks, source-to-mark geometry checks,
and tamper/disclosure tests. Every passing result explicitly remains
`synthetic-fixture-auditor-only` with `release_qualified: false`.

The published red-first source/test commit is
`2c1e616e6b85b4f7e20c6c72fffbbeda2f731a4b` (local original:
`7302e2d3ec1342415dbf1b2dfb7b46c2173f60cf`). The first
observed run failed because the auditor module did not yet exist. Review then
found and repaired three ignored-workbook-content cases: unused shared strings,
document properties, and ignored worksheet XML. Additional coverage rejects
Arrow batch metadata and appended workbook data. No production defect was
inferred or repaired from these harness findings.

`results/execution.json` binds commands, outcomes, tools and code/fixture hashes
to published implementation commit `7f1869681d944a15c8fcfc759fa203e9a4b127ed`.
The shell had no Git push credentials, so the authenticated GitHub connector
published the commits with new commit metadata. Every blob and the complete
implementation tree (`c68e65209a1f097bb58ebfbf161c3613f3cce51f`) were verified
identical to locally tested implementation `070e94459b217a1f051b354e91abb44a635b43e5`.
The published source was then fetched into a clean checkout and the commands
rerun there. A later evidence-only commit can add these
receipts without changing the tested implementation. The PR body and issue
handoff provide the final exact head and its rerun results; do not substitute a
green result from a different head.

## Still blocked; requested coordinator actions

| Dependency | Observed boundary and requested action |
| --- | --- |
| E04 | The inspected registry still says planned; `Cargo.lock`, `verification/native-ci-receipt.json` and `verification/dependency-review.json` are absent at the baseline. Pin admitted native/toolchain/dependency evidence before dependent release qualification. |
| Producer conformance | Pin the actual producer and consumer heads, schema and shared executed fixtures. The observed `org.scholarly.stream/1.0.0-design.2` baseline is not an admitted live producer relationship. |
| Durable spool/recovery | Retain ownership of checkpoint, deletion, duplicate, restart and crash evidence. A synthetic output round trip provides no durable replay proof. |
| Production output contract | Agree the mapping for per-row rights, missing versus withheld counts, excluded-row disclosure, exact units/types, source/table revisions and canonical ordering. Current annual production outputs have a narrower non-nullable annual-count shape. This PR's six-column fixture profile does not redefine or claim compatibility with it. |
| Actual native artifacts | After the preceding pins, capture artifacts from native production at exact heads into an isolated test location and add an explicit reader/profile adapter. Do not relabel these Python-written fixtures as Rust output or use a lossy conversion to conceal unsupported rights/null semantics. |
| Additional CI gate | Review the optional pinned reader environment and run both complete CLI audits plus the full tests with zero reader skips. The current shared CI installs only its existing lightweight requirements. No CI change is made in this lane. |
| External rendering / accessibility | Separately qualify a pinned Vega/browser/Typst renderer, raster/PDF outputs, and accessibility. These tests verify source semantics and one SVG geometry profile only. |

These are handoff requests, not changes to shared files. No merge, release,
gate relaxation, infrastructure change, new worker, or new Work/Codex chat was
performed. The PR should remain draft pending integrator review; completion of
the fixture lane does not mark the broader E09 task complete.

## Resource and reproduction notes

Before implementation the shared workspace volume had approximately 7 MB free.
Work therefore used a separate isolated checkout and virtual environment on the
temporary filesystem, which initially had 4.9 GB free. No other checkout,
target directory, package cache or uncommitted work was removed or modified.
No Rust build was attempted: `rustc` and `cargo` were unavailable on PATH, and
native/release qualification is outside this lane's current evidence.

An initial broad Python run in the base environment exposed two existing
strict-date tests failing because the declared `rfc3339-validator` dependency
was absent. Installing the repository's unchanged declared requirements in the
isolated environment resolved both; no test or date contract was weakened.
The complete commands and limitations are in the [README](README.md).
