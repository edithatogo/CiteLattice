# CiteLattice Conductor

**Canonical design and planning state; runtime implementation is separate.**

Read [requirements](requirements.md), [design](design.md), [tracks](tracks.md), then the active track, method registry, source contract and affected Rust modules. Do not infer runtime or scientific validation from a schema.

CiteLattice supersedes the working bibx name. Earlier bibx design.2 is the migration baseline, not proof that every file has been imported. Searchright proposed stream is org.scholarly.stream 1.0.0-design.2; neither side's runtime interoperability is yet admitted.

Lean solo workflow: scoped plan + contract + failing test + implementation + recorded CI result + merge. No duplicated governance, mandatory multi-agent approval boards or hundreds of generated tracking issues.

## Active implementation and evaluation

- [Track 12 verification and frontier specification](tracks/12-scientific-evaluation/spec.md)
- [Executable plan and native acceptance commands](tracks/12-scientific-evaluation/plan.md)
- [Machine-readable task/dependency registry](evaluation-programme.json)
- [Current citation-summary API](../docs/citation-summary.md)

The current merged source has passed the scoped Rust core and schema workflows. See [exact CI acceptance](../verification/ci-acceptance-2026-11-12.json). Scientific fidelity, full producer/consumer interoperability, security qualification and beyond-frontier hypotheses require separate evidence.

- [Track 07 evidence-linked annual scenes](tracks/07-scientific-imaging/spec.md) — Vega-Lite, SVG and mark-to-row contracts; hosted core CI passed; independent imaging evaluation pending.
- [Track 01 versioned scholarly stream consumer](tracks/01-scholarly-events/spec.md) — producer and durable replay verification pending.
