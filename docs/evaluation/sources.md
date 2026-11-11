# Primary source and dataset register

Checked 10 November 2026. These are references and acquisition candidates, not
claims that external benchmarks or licensed datasets were downloaded/executed.

| ID | Source | Use and qualification |
| --- | --- | --- |
| S01 | Hirsch (2005), https://doi.org/10.1073/pnas.0507655102 | h-index definition; declared publication/citation universe still required |
| S02 | Egghe (2006), https://doi.org/10.1007/s11192-006-0144-7 | g-index definition; this profile explicitly caps at actual N |
| S03 | bibliometrix Hindex source, https://github.com/massimoaria/bibliometrix/blob/master/R/Hindex.R | Independent method comparator; pin exact source/version and conventions before running |
| S04 | bibliometrix official introduction, https://www.bibliometrix.org/vignettes/Introduction_to_bibliometrix.html | Coverage map and conventional analyses, not evidence of this library's parity |
| S05 | https://docs.rs/serde_json_canonicalizer/0.3.2/serde_json_canonicalizer/ | Canonical JSON dependency; compile/lock and run conformance vectors before admission |
| S06 | https://www.rfc-editor.org/rfc/rfc8785 | Canonical byte identity; large counts use strings, avoiding binary64 precision loss |
| S07 | https://help.openalex.org/access/snapshot/ and https://help.openalex.org/access/sync/ | Pin a specific public snapshot/manifest and its bytes; distinguish free snapshot access, paid sync and licensed full-text assets |
| S08 | https://github.com/allenai/S2AND and https://github.com/allenai/S2AND/blob/main/docs/data.md | Author-disambiguation benchmark; current Arrow and legacy formats differ; pin release and component rights before use |
| S09 | https://opencitations.net/download | Candidate independently sourced citation graph; select exact dump/terms/schema and inspect coverage before admission |
| S10 | https://www.researchobject.org/ro-crate/ | Provenance packaging; validate the selected exact profile with independent tooling |
| S11 | https://semver.org/ and https://www.rfc-editor.org/rfc/rfc3339 | Version syntax and observation-time representation; method semantics have separate versions |

OpenAlex is a source corpus, not authoritative ground truth on author identity or
complete citations. S2AND supplies labelled evaluation contexts, but reuse does
not prove correctness for other sources/fields. Compare tools on aligned inputs;
never call discrepant provider definitions a numerical bug without investigation.

No third-party source code, labels, private abstracts or proprietary provider
outputs are copied into this patch. Synthetic fixtures are repository-authored.
